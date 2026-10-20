"""Verify approved snapshots in a Git tree and an independent extracted archive."""
import argparse
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    import re
    if not re.fullmatch(r'[A-Za-z0-9._-]+', args.run_id):
        parser.error('simple run-id required')
    root = Path(__file__).resolve().parents[2]
    git = lambda *a: subprocess.check_output(['git', '-C', str(root), *a])
    tree = git('rev-parse', args.ref + '^{tree}').decode().strip()
    out = root / 'artifacts/TASK-001' / args.run_id
    restored = root / 'work' / args.run_id
    out.mkdir(exist_ok=False)
    restored.mkdir(parents=True, exist_ok=False)
    archive = git('archive', '--format=tar', tree)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
        tf.extractall(restored, filter='data')
    sha = lambda b: hashlib.sha256(b).hexdigest()
    manifests = [
        ('baselines/BL-20261020-01', '55b68829f17a489060281174c901a9de6fd2f5902831ed3b7aa717696e5e802c'),
        ('artifacts/TASK-001/gate1-v0.1', 'b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3'),
    ]
    checks = []
    for prefix, manifest_hash in manifests:
        manifest_path = prefix + '/manifest.json'
        manifest_bytes = (root / manifest_path).read_bytes()
        items = json.loads(manifest_bytes)['files']
        targets = [(manifest_path, manifest_hash, len(manifest_bytes))]
        targets += [(prefix + '/' + f['path'], f['sha256'], f['bytes']) for f in items]
        for path, expected_hash, expected_size in targets:
            local = (root / path).read_bytes()
            blob = git('show', tree + ':' + path)
            recovered = (restored / path).read_bytes()
            checks.append({'path': path, 'expected_sha256': expected_hash,
                           'worktree_match': sha(local) == expected_hash and len(local) == expected_size,
                           'git_blob_match': sha(blob) == expected_hash and len(blob) == expected_size,
                           'archive_restore_match': sha(recovered) == expected_hash and len(recovered) == expected_size})
    failed = [c for c in checks if not all(c[k] for k in ('worktree_match', 'git_blob_match', 'archive_restore_match'))]
    result = {'performed_at': dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
              'requested_ref': args.ref, 'tree': tree,
              'scope': 'Approved Task 000 and Task 001 exact bytes in worktree, Git blobs and independent git archive extraction; no engine execution',
              'result': 'failed' if failed else 'passed', 'check_count': len(checks), 'failed_count': len(failed),
              'restore_directory': str(restored.relative_to(root)),
              'archive_sha256': sha(archive), 'checks': checks}
    (out / 'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
