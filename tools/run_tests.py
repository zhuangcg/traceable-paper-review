"""Run all self-contained checks, stopping on the first failed test."""
import subprocess
import sys
import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for path in sorted((root/'tests').glob('test_*.py')):
    print(path.name,flush=True)
    subprocess.run([sys.executable,str(path)],cwd=root,check=True,env={**os.environ,'PYTHONUTF8':'1'})
print('ALL TESTS PASSED')
