import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
scripts = root / 'scripts'
with tempfile.TemporaryDirectory() as tmp:
    work = Path(tmp) / 'review'
    preflight = subprocess.run([sys.executable, str(scripts / 'check_env.py'), str(work)], check=True, capture_output=True, text=True, encoding='utf8')
    data = json.loads(preflight.stdout)
    assert data['python_supported'] and data['writable'] and data['network'] == 'not_checked'
    assert 'mineru_token_set' in data
    subprocess.run([sys.executable, str(scripts / 'run_pipeline.py'), 'prepare', str(work), '--markdown', str(root / 'examples/input/paper.md')], check=True, capture_output=True)
    assert (work / 'source_manifest.json').is_file() and (work / 'source_index.json').is_file()
    failed = subprocess.run([sys.executable, str(scripts / 'run_pipeline.py'), 'finish', str(work)], capture_output=True)
    assert failed.returncode != 0 and not (work / 'review.json').exists()
    assert (work / 'source_manifest.json').exists()
print('PASS: preflight, pipeline preparation and failed-audit preservation')
