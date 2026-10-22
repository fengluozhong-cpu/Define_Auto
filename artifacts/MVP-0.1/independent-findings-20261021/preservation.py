from pathlib import Path
import hashlib,json
root=Path.cwd();package=root/'artifacts/TASK-001/gate1-v0.1'; manifest=package/'manifest.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=[{'id':'approved_manifest','passed':sha(manifest.read_bytes())=='b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3'}]
for f in json.loads(manifest.read_text())['files']:
 b=(package/f['path']).read_bytes();checks.append({'id':f['path'],'passed':len(b)==f['bytes'] and sha(b)==f['sha256']})
draft=(root/'docs/tasks/MVP-0.1-skill-setup-draft.md').read_text(encoding='utf-8')
checks.append({'id':'confirmed_skill_draft','passed':sha((root/'docs/tasks/MVP-0.1-skill-setup-draft.md').read_bytes())=='8cbb9657b18e4a7bd16430bf0556b3cda3bbdc0255576cd3ce7d7dc96ecd875b'})
blocks=draft.split('```markdown\n')[1:]
targets=['AGENTS.md','docs/agents/issue-tracker.md','docs/agents/triage-labels.md','docs/agents/domain.md']
for target,block in zip(targets,blocks):
 expected=block.split('```')[0].strip(); actual=(root/target).read_text(encoding='utf-8').strip()
 checks.append({'id':'skill_'+target,'passed':actual.endswith(expected) if target=='AGENTS.md' else actual==expected})
out=root/'artifacts/MVP-0.1/independent-preservation-20261021';out.mkdir(exist_ok=False)
(out/'checks.json').write_text(json.dumps({'checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks)},indent=2),encoding='utf-8')
print(len(checks),sum(c['passed'] for c in checks),[c['id'] for c in checks if not c['passed']])
