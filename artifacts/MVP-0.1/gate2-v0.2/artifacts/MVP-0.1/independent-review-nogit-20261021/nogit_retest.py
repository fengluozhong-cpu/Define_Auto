from pathlib import Path
import sys,importlib.util
sys.path.insert(0,str(Path.cwd()))
p=Path('tools/mvp01/run_checks.py');spec=importlib.util.spec_from_file_location('review_nogit_runner',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
mod.shutil.which=lambda command:None
sys.argv=[str(p),'--run-id','independent-review-nogit-20261021']
raise SystemExit(mod.main())
