"""Read-only approval/dependency audit; never run the reconciliation engine."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'artifacts/TASK-001/gate1-v0.1'
APPROVED_HASH = 'b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', args.run_id):
        parser.error('run-id must be one simple directory name')
    out = ROOT / 'artifacts/MVP-0.1' / args.run_id
    out.mkdir(parents=True, exist_ok=False)
    started = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
    checks = []

    def check(cid, actual, expected):
        checks.append({'check_id': cid, 'actual': actual, 'expected': expected,
                       'result': 'passed' if actual == expected else 'failed'})

    try:
        manifest = PACKAGE / 'manifest.json'
        check('M01-Q01.manifest', digest(manifest), APPROVED_HASH)
        # Never trust or follow manifest paths until its approved bytes match.
        if digest(manifest) != APPROVED_HASH:
            raise ValueError('Approved manifest mismatch; dependent resolution blocked')
        items = json.loads(manifest.read_text('utf-8-sig'))['files']
        check('M01-Q01.file_count', len(items), 82)
        resolved = []
        for item in items:
            path = (PACKAGE / item['path']).resolve()
            if not path.is_relative_to(PACKAGE.resolve()):
                raise ValueError('Frozen reference leaves package root')
            check('M01-Q01.file.' + item['path'],
                  [path.stat().st_size, digest(path)], [item['bytes'], item['sha256']])
            resolved.append({'reference': item['path'], 'resolved_copy': path.relative_to(ROOT).as_posix(),
                             'sha256': digest(path), 'bytes': path.stat().st_size, 'role': item['role']})
        save(out / 'frozen-reference-map.json', {'root': PACKAGE.relative_to(ROOT).as_posix(), 'files': resolved})
        reads = {
            'AGENTS.md': 'complete', 'GOALS.md': 'complete',
            'PLANS.md': '1/2/3/CTRL-01/02/03/8', 'REQUIREMENTS.md': 'complete including CTRL-05/06',
            'ARCHITECTURE.md': 'complete including 1-4.1/5/10',
            'docs/tasks/TASK-001.md': 'complete latest handoff and approval',
            'docs/tasks/MVP-0.1-kickoff-prompt.md': 'complete v0.2',
            'docs/tasks/MVP-0.1.md': 'complete initial task/checklist draft',
            'docs/approvals/APR-20261020-01.md': 'baseline approval',
            'docs/approvals/APR-20261020-02.md': 'complete',
            'artifacts/TASK-001/gate1-v0.1/docs/contracts/TASK-001-contract-v0.1.md': 'complete',
            'artifacts/TASK-001/gate1-v0.1/docs/contracts/TASK-001-technical-basis-v0.1.md': 'complete',
            'artifacts/TASK-001/gate1-v0.1/expectations/task001/v0.1/expected.json': 'complete 24 cases/facts',
            'artifacts/TASK-001/gate1-v0.1/expectations/task001/v0.1/coverage.json': 'complete 36 rows',
            'artifacts/TASK-001/gate1-v0.1/expectations/task001/v0.1/gate1-checklist.json': 'complete Q01-Q07',
            'tools/task001/check_materials.py': 'complete applicability/environment audit',
            'tools/task001/check_git_preservation.py': 'complete read-only Git recovery audit',
        }
        additional_reads = {
            'docs/contracts/MVP-0.1-read-context-v0.1.md': 'complete accepted M01-D01 implementation contract',
            'expectations/mvp01/v0.1/additional-cases.json': 'independent 23 case expectations and byte recipes; materialization verified',
            'docs/tasks/mvp01-review/startup-review.md': 'complete independent preparation review',
            'docs/tasks/mvp01-review/read-context-review.md': 'complete independent material/context review',
            'docs/tasks/MVP-0.1-skill-setup-draft.md': 'complete pending configuration draft',
            'fixtures/mvp01/v0.1/manifest.json': 'materialized independent byte fixtures',
            'fixtures/mvp01/baseline-context-v0.1/manifest.json': 'synthetic baseline declarations',
        }
        reads.update({p: s for p, s in additional_reads.items() if (ROOT / p).is_file()})
        save(out / 'reading-record.json', {'files': [dict(path=p, sections=s, sha256=digest(ROOT / p)) for p, s in reads.items()]})
        coverage_path = PACKAGE / 'expectations/task001/v0.1/coverage.json'
        coverage = json.loads(coverage_path.read_text('utf-8-sig'))['rows']
        save(out / 'carryover.json', {'source': coverage_path.relative_to(ROOT).as_posix(), 'source_sha256': digest(coverage_path),
             'approval': 'APR-20261020-02', 'current_task': 'MVP-0.1',
             'rows': [dict(r, receiving_task='MVP-0.1' if 'MVP 0.1' in r['deferred_to'] or
                            r['requirement'] in ['NFR-003', 'NFR-007'] else r['deferred_to'],
                            original_record_is_historical=True, current_execution_result='not_run') for r in coverage]})
        baseline_cases = json.loads((PACKAGE / 'expectations/task001/v0.1/expected.json').read_text('utf-8-sig'))['cases']
        check('M01-Q03.registered_baseline', [c['id'] for c in baseline_cases], [f'T001-C{i:02}' for i in range(1, 25)])
        check('M01-Q04.coverage_rows', len(coverage), 36)
    except Exception as exc:
        checks.append({'check_id': 'STARTUP_EXECUTION', 'result': 'failed', 'exception_type': type(exc).__name__, 'message': str(exc)})
    failed = [c for c in checks if c['result'] != 'passed']
    save(out / 'checks.json', {'scope': 'startup material integrity only', 'checks': checks, 'collected': len(checks),
         'executed': len(checks), 'failed': len(failed), 'skipped': 0, 'result': 'failed' if failed else 'passed',
         'engine_cases_executed': 0, 'gate2': 'not_assessed'})
    save(out / 'run.json', {'task_id': 'MVP-0.1', 'run_id': args.run_id, 'command': sys.argv,
         'started_at': started, 'finished_at': dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
         'python': sys.version, 'platform': platform.platform(), 'script_sha256': digest(Path(__file__)),
         'head': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
         'result': 'failed' if failed else 'passed', 'exit_code': 1 if failed else 0})
    inputs = [PACKAGE / 'manifest.json', Path(__file__), ROOT / 'docs/tasks/MVP-0.1.md']
    save(out / 'inputs-manifest.json', {'files': [dict(path=p.relative_to(ROOT).as_posix(), sha256=digest(p), bytes=p.stat().st_size) for p in inputs],
         'frozen_files': 'frozen-reference-map.json', 'other_read_dependencies': 'reading-record.json'})
    save(out / 'outputs-manifest.json', {'files': [dict(path=p.name, sha256=digest(p), bytes=p.stat().st_size) for p in sorted(out.glob('*.json'))], 'excludes_self': True})
    print(json.dumps({'run': out.relative_to(ROOT).as_posix(), 'checks': len(checks), 'failed': len(failed), 'engine_cases_executed': 0}))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
