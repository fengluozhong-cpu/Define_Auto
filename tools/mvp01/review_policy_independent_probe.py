"""Independent reviewer probes; preserves before/after evidence per unique run."""
import argparse
from copy import deepcopy
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from define_auto.common import ContractError, canonical, sha, write, load
from define_auto.review import apply_review_action
from define_auto.reporting import markdown
from tests.support import baseline, issue, obj, workspace
from tests.test_review_policy import action_for, authorize, delivery, rulebook, ReviewPolicyCases


def main():
    p = argparse.ArgumentParser(); p.add_argument('--run-id', required=True)
    out = ROOT / 'artifacts/MVP-0.1' / p.parse_args().run_id
    out.mkdir(parents=True, exist_ok=False)
    evidence = {'reviewer': '/root/review_policy_independent', 'checks': [],
                'source_hashes': {str(x.relative_to(ROOT)): sha(x.read_bytes()) for x in sorted((ROOT / 'define_auto').glob('*.py'))}}
    with workspace() as tmp:
        base = baseline(); book = rulebook(base, target='DM.ARM')
        m, _ = delivery(Path(tmp) / 'absent-rule', rules=book)
        f = m['review_policy']['rule_findings'][0]
        evidence['checks'].append({'id': 'IP01', 'scenario': 'Type rule on physically absent DM.ARM',
            'actual': f, 'passed': f['result'] != 'passed_local_rule'})
        m = baseline(); i = issue(m, 'DM', 'SEX', 'label')
        a = action_for(m, kind='return_upstream', target='DM.SEX', value=[i['issue_id']])
        m, auth = authorize(m, a); m, result = apply_review_action(m, a, auth, test_mode=True)
        entry = [x for x in m['review_policy']['upstream_rework'] if x['object_id'] == a['object_id']]
        evidence['checks'].append({'id': 'IP02', 'scenario': 'Human returns ordinary label conflict upstream',
            'actual': {'action_result': result, 'upstream_projection': entry,
                       'report_has_upstream_instruction': any(r[0] == a['object_id'] and r[1] == 'label' and '返回上游返工' in r[-1]
                          for r in __import__('define_auto.reporting', fromlist=['review_rows']).review_rows(m))},
            'passed': bool(entry) and any(r[0] == a['object_id'] and r[1] == 'label' and '返回上游返工' in r[-1]
                          for r in __import__('define_auto.reporting', fromlist=['review_rows']).review_rows(m))})
        m = baseline(); a = action_for(m, kind='return_upstream', target='DM.SEX', value=[[]]); m, auth = authorize(m, a)
        try:
            apply_review_action(m, a, auth, test_mode=True)
            state = 'accepted'
        except ContractError as exc:
            state = 'ContractError:' + exc.code
        except Exception as exc:
            state = type(exc).__name__
        evidence['checks'].append({'id': 'IP03', 'scenario': 'Malformed return scope nested list', 'actual': state,
                                   'passed': state.startswith('ContractError:')})
        m, flags = delivery(Path(tmp) / 'malformed-cli')
        book = rulebook(m); book['rules'][0]['value'] = []
        write(Path(tmp) / 'book.json', book)
        result = subprocess.run([sys.executable, '-m', 'define_auto', *flags,
            '--review-rules', str(Path(tmp) / 'book.json'), '--out', str(Path(tmp) / 'cli-output')],
            cwd=ROOT, capture_output=True, text=True)
        evidence['checks'].append({'id': 'IP06', 'scenario': 'Malformed rule value through real CLI',
            'actual': {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr},
            'passed': result.returncode == 1 and not result.stderr and 'invalid_rule_value' in result.stdout
                       and not (Path(tmp) / 'cli-output').exists()})
        from define_auto.review import reuse_offer
        fixture = ReviewPolicyCases(); fixture.setUp()
        try:
            old, current, _ = fixture.prior_current()
            offer = reuse_offer(current, old['decisions'][0])
            evidence['checks'].append({'id': 'IP05', 'scenario': 'Human reuse shows immutable previous and current observations',
                'actual': offer, 'passed': bool(offer.get('previous_observation') and offer.get('current_observation')
                    and offer.get('previous_candidates') and offer.get('input_changes'))})
        finally:
            fixture.doCleanups()
        m, flags = delivery(Path(tmp) / 'stable-cli')
        def cli(label, extra):
            folder = Path(tmp) / label
            result = subprocess.run([sys.executable, '-m', 'define_auto', *flags, *extra, '--out', str(folder)],
                                    cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError('Independent stability CLI failed: ' + result.stdout)
            return folder, load(folder / 'model.json')
        base_path, base_model = cli('stable-base', [])
        action = action_for(base_model); _, auth = authorize(base_model, action)
        write(Path(tmp) / 'stable-action.json', action)
        write(Path(tmp) / 'stable-auth.json', {k: v for k, v in auth.items() if k not in {'source_id', 'source_sha256'}})
        extra = ['--review-action', str(Path(tmp) / 'stable-action.json'), '--authorization', str(Path(tmp) / 'stable-auth.json')]
        confirmed_path, confirmed = cli('stable-confirm', extra)
        _, repeated = cli('stable-repeat', extra + ['--prior-model', str(confirmed_path / 'model.json')])
        evidence['checks'].append({'id': 'IP07', 'scenario': 'Repeated exact No Data action through real CLI with restored history',
            'actual': {'canonical_model_equal': canonical(confirmed) == canonical(repeated),
                      'first_model_id': confirmed['model_snapshot_id'], 'repeated_model_id': repeated['model_snapshot_id'],
                      'history_count': len(repeated['review_actions'])},
            'passed': canonical(confirmed) == canonical(repeated) and len(repeated['review_actions']) == 1})
    write(out / 'checks.json', evidence)
    print(canonical({'out': str(out), 'checks': evidence['checks']}).decode('utf-8'))
    return 0 if all(x['passed'] for x in evidence['checks']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
