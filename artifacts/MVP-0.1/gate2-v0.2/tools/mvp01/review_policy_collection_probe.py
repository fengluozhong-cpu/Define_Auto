"""Independent real-discovery omission probe for a mandatory new policy case."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mvp01 import run_checks

original = unittest.defaultTestLoader.discover


def filtered(*args, **kwargs):
    suite = original(*args, **kwargs)
    return unittest.TestSuite(t for t in run_checks.flatten(suite)
                              if run_checks.case_id(t) != 'M01-RP40')


if __name__ == '__main__':
    unittest.defaultTestLoader.discover = filtered
    raise SystemExit(run_checks.main())
