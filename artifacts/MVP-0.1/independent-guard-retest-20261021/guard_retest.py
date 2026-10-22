from pathlib import Path
import sys,importlib.util,unittest
sys.path.insert(0,str(Path.cwd()))
mode=sys.argv[1];run_id=sys.argv[2]
p=Path('tools/mvp01/run_checks.py');spec=importlib.util.spec_from_file_location('review_fault_runner',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
old=mod.unittest.defaultTestLoader.discover
if mode in {'skip','error'}:
 from tests.test_boundaries import RuntimeBoundaryTests
 if mode=='skip':RuntimeBoundaryTests.test_raw_label_and_privacy=unittest.skip('INDEPENDENT GUARD PROBE ONLY')(RuntimeBoundaryTests.test_raw_label_and_privacy)
 else:
  def fail(self):raise RuntimeError('INDEPENDENT GUARD PROBE ONLY')
  RuntimeBoundaryTests.test_raw_label_and_privacy=fail
else:
 def filtered(*a,**k):
  items=mod.flatten(old(*a,**k))
  return unittest.TestSuite([] if mode=='zero' else [t for t in items if not t.id().endswith('.test_raw_label_and_privacy')])
 mod.unittest.defaultTestLoader.discover=filtered
sys.argv=[str(p),'--run-id',run_id]
raise SystemExit(mod.main())
