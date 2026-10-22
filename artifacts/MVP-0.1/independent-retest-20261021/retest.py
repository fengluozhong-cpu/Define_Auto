from pathlib import Path
from copy import deepcopy
import sys,subprocess,json
sys.path.insert(0,str(Path.cwd()))
from tests.support import baseline,obj,patch_context,BASE,CONTEXT,PROVENANCE
from define_auto.common import canonical,sha,write,load,ContractError
from define_auto.model import validate_model,business_digest
from define_auto.decisions import apply_decision
from define_auto.reporting import review_rows,html_report,markdown
root=Path.cwd();out=root/'artifacts/MVP-0.1/independent-retest-20261021';out.mkdir(exist_ok=False)
files=sorted([*root.glob('define_auto/*.py'),*root.glob('tests/*.py'),root/'tools/mvp01/run_checks.py',root/'README.md'])
before={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in files};results=[]
def reject(cid,fn,codes):
 try: fn()
 except ContractError as e:
  assert e.code in codes,(cid,e.code,codes);results.append({'check_id':cid,'result':'passed','actual_error':e.code});return
 raise AssertionError(cid+' unexpectedly accepted')
m=baseline();validate_model(m,sealed=True)
for case in ['snapshot','dependency','type','expected','downstream','resolved']:
 x=deepcopy(m)
 if case=='snapshot':x['model_snapshot_id']='model-'+'0'*64
 if case=='dependency':
  x['dependency_snapshot']['dependency_snapshot_id']='dep-'+'0'*64;x['model_snapshot_id']=business_digest(x)
 if case=='type':obj(x,'DM','SEX')['observed']['type']=['arbitrary']
 if case=='expected':obj(x,'DM','SEX')['expected']['label']='Different candidate'
 if case=='downstream':x['downstream_records']=[{'record_id':None,'status':'APPROVED'}]
 if case=='resolved':x['issues'][0].update(status='resolved',decision_id='NO-SUCH-DECISION')
 reject('F01-'+case,lambda x=x:validate_model(x,sealed=True),{'model_snapshot_hash_mismatch','dependency_snapshot_hash_mismatch','invalid_model_shape','view_assertion_mismatch','invalid_required_text','missing_resolution_decision','invalid_observed_type'})
common=[sys.executable,'-m','define_auto','--manifest',str(BASE/'input-manifest.json'),'--read-context',str(CONTEXT),'--provenance','TEST-BASELINE-MANUFACTURE-001='+str(next(iter(PROVENANCE.values()))),'--isolated-test']
def run(name,flags,expect=0,error=None):
 cp=subprocess.run(common+flags+['--out',str(out/name)],cwd=root,capture_output=True,text=True)
 assert cp.returncode==expect,(name,cp.stdout,cp.stderr)
 if error:assert json.loads(cp.stdout)['error']==error,(name,cp.stdout)
 assert 'Traceback' not in cp.stderr
 results.append({'check_id':'CLI-'+name,'result':'passed','exit_code':cp.returncode,'stdout':json.loads(cp.stdout)})
 return load(out/name/'model.json') if expect==0 else None
initial=run('base',[])
p=load(BASE/'patch.json');p['dependency_snapshot_id']=initial['dependency_snapshot']['dependency_snapshot_id']
auth={'authorization_id':'TEST-INDEPENDENT-AUTH-1','reviewer':p['reviewer'],'test_only':True,'scope':{k:p[k] for k in ['object_id','field_path','selected_value','dependency_snapshot_id']}}
pp,ap=out/'patch.json',out/'authorization.json';write(pp,p);write(ap,auth)
flags=['--patch',str(pp),'--authorization',str(ap),'--previous-dependency',str(out/'base/dependencies.json')]
first=run('first',flags)
repeat=run('repeat',flags+['--prior-model',str(out/'first/model.json')]);assert canonical(first)==canonical(repeat)
q={**p,'decision_id':'TEST-INDEPENDENT-REVISION','supersedes':p['decision_id'],'selected_value':'Sex'}
auth['authorization_id']='TEST-INDEPENDENT-AUTH-2';auth['scope']['selected_value']='Sex';write(pp,q);write(ap,auth)
revision=run('revision',flags+['--prior-model',str(out/'repeat/model.json')]);assert len(revision['decisions'])==2;assert revision['decisions'][0]==first['decisions'][0]
assert obj(revision,'DM','SEX')['simulated_selection']['label']=='Sex';assert not any(o['approved'] for o in revision['objects'])
write(pp,{**q,'rationale':'changed same ID'})
run('same-id-different',flags+['--prior-model',str(out/'revision/model.json')],1,'reject_same_id_different_content');write(pp,q)
stale=run('dependency-change',flags+['--prior-model',str(out/'revision/model.json'),'--encoding','ascii'])
assert load(out/'dependency-change/patch-applicability.json')['status']=='needs_review';assert stale['decisions']==revision['decisions'];assert not obj(stale,'DM','SEX')['approved']
for kind in ['bad-snapshot','bad-dependency']:
 x=deepcopy(revision)
 if kind=='bad-snapshot':x['model_snapshot_id']='model-'+'0'*64
 else:x['dependency_snapshot']['dependency_snapshot_id']='dep-'+'0'*64;x['model_snapshot_id']=business_digest(x)
 path=out/(kind+'.json');write(path,x)
 run(kind,['--prior-model',str(path)],1,'model_snapshot_hash_mismatch' if kind=='bad-snapshot' else 'dependency_snapshot_hash_mismatch')
# Exercise ordinary approval branch on explicit synthetic-only review model, never project approval.
r,p,a=patch_context(m);r['test_only']=False;p['authorization_status']='authorized';a['test_only']=False
p['decision_id']='REVIEW-ONLY-NOT-PROJECT-APPROVAL-1';a['authorization_id']='REVIEW-ONLY-AUTH-1';dep=deepcopy(r['dependency_snapshot'])
firstreal,_=apply_decision(r,p,dep,a)
q={**p,'decision_id':'REVIEW-ONLY-NOT-PROJECT-APPROVAL-2','supersedes':p['decision_id'],'selected_value':'Sex'}
a2=deepcopy(a);a2['authorization_id']='REVIEW-ONLY-AUTH-2';a2['scope']['selected_value']='Sex'
secondreal,_=apply_decision(firstreal,q,dep,a2);assert secondreal['decisions'][0]==firstreal['decisions'][0]
assert obj(secondreal,'DM','SEX')['approved']['label']=='Sex';assert sum(x['assertion_kind']=='approved' for x in secondreal['assertions'])==1
results.append({'check_id':'F02-ordinary-branch-supersedes','result':'passed','scope':'Synthetic branch test only; no project approval saved'})
lengthissue=next(i for i in m['issues'] if i['field_path']=='storage_vs_declared_length')
p={**p,'decision_id':'REVIEW-ONLY-LENGTH','object_id':lengthissue['object_id'],'field_path':lengthissue['field_path'],'issue_ids':[lengthissue['issue_id']],'selected_value':lengthissue['candidates'][0]['value'],'supersedes':None}
a=deepcopy(a);a['authorization_id']='REVIEW-ONLY-LENGTH-AUTH';a['scope']={k:p[k] for k in ['object_id','field_path','selected_value','dependency_snapshot_id']}
lengthmodel,_=apply_decision(r,p,dep,a)
row=next(row for row in review_rows(lengthmodel) if row[0]==p['object_id'] and row[1]=='declared_length');assert row[5]==p['selected_value'];assert row[8]
assert all(row[8] for row in review_rows(m))
assert '&lt;script&gt;' in html_report({**m,'model_snapshot_id':'<script>'})
results.append({'check_id':'F03-length-approved-and-normal-provenance','result':'passed','length_value':row[5]})
after={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in files}
write(out/'results.json',{'checks':results,'source_hashes_before':before,'source_hashes_after':after,'source_changed':before!=after,'passed':len(results)})
(out/'retest.py').write_bytes(Path(__file__).read_bytes())
write(out/'outputs-manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'sha256':sha(p.read_bytes())} for p in sorted(out.rglob('*')) if p.is_file()]})
print(json.dumps({'passed':len(results),'source_changed':before!=after,'out':str(out)}))
