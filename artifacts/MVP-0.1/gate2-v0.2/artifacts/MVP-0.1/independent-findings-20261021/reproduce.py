from pathlib import Path
from copy import deepcopy
import sys
sys.path.insert(0,str(Path.cwd()))
from tests.support import baseline,obj,patch_context
from define_auto.common import ContractError,canonical,sha,write
from define_auto.model import validate_model
from define_auto.decisions import apply_decision
root=Path.cwd(); results={}; hashes={str(p):sha(p.read_bytes()) for p in sorted(root.glob('define_auto/*.py'))}
m=baseline()
def check(name,mutation):
 x=deepcopy(m); mutation(x)
 try:
  validate_model(x); results[name]={'accepted':True}
 except Exception as e: results[name]={'accepted':False,'error':getattr(e,'code',type(e).__name__)}
check('resolved_missing_decision',lambda x:x['issues'][0].update(status='resolved',decision_id='NONEXISTENT'))
check('forged_evidence_id',lambda x:x['evidence'][0].update(evidence_id='forged'))
check('wrong_snapshot_hash',lambda x:x.update(model_snapshot_id='model-'+'0'*64))
check('wrong_dependency_hash',lambda x:x['dependency_snapshot'].update(dependency_snapshot_id='dep-'+'0'*64))
check('observed_type_wrong',lambda x:obj(x,'DM','SEX')['observed'].update(type=['arbitrary']))
check('view_assertion_divergence',lambda x:obj(x,'DM','SEX')['expected'].update(label='arbitrary different candidate'))
check('downstream_invalid',lambda x:x.update(downstream_records=[{'record_id':None,'status':'APPROVED'}]))
# Exercise real mode with explicit synthetic review-only declaration; no true business approval.
a,p,auth=patch_context(m); a['test_only']=False; auth['test_only']=False; p['authorization_status']='authorized'
dep=deepcopy(a['dependency_snapshot'])
try:
 first,r=apply_decision(a,p,dep,auth)
 q=deepcopy(p);q.update(decision_id='REVIEW-SECOND',supersedes=p['decision_id'],selected_value='Sex'); au=deepcopy(auth); au['authorization_id']='REVIEW-AUTH-SECOND';au['scope']['selected_value']='Sex'
 try:
  second,r=apply_decision(first,q,dep,au);results['real_supersedes']={'success':True,'approved':obj(second,'DM','SEX')['approved']}
 except Exception as e: results['real_supersedes']={'success':False,'error':getattr(e,'code',type(e).__name__)}
except Exception as e: results['first_authorized']={'success':False,'error':getattr(e,'code',type(e).__name__)}
write(root/'work/mvp01-final-review/initial-results.json',{'source_hashes':hashes,'results':results})
print(results)
