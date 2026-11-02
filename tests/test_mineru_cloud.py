import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import mineru_cloud as mineru

def archive(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, value in entries.items():
            z.writestr(name, value)
    return buf.getvalue()

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    pdf = root / 'paper.pdf'
    pdf.write_bytes(b'%PDF-1.4 example')
    zipped = archive({'full.md': 'Example ![](images/a.png)', 'images/a.png': b'image'})
    calls = []
    def fake(url, method='GET', body=None, headers=None):
        calls.append((url, method, headers or {}))
        if url.endswith('file-urls/batch'):
            assert headers['Authorization'] == 'Bearer secret'
            return json.dumps({'code': 0, 'data': {'batch_id': 'batch-1', 'file_urls': ['https://upload.example/file']}}).encode()
        if url == 'https://upload.example/file':
            assert method == 'PUT' and body == pdf.read_bytes() and not headers
            return b''
        if 'extract-results/batch/' in url:
            return json.dumps({'code': 0, 'data': {'extract_result': [{'state': 'done', 'full_zip_url': 'https://cdn.example/result'}]}}).encode()
        assert url == 'https://cdn.example/result' and not headers
        return zipped
    with patch.object(mineru, 'request', fake):
        result = mineru.convert(pdf, root / 'result', 'secret')
        assert Path(result['markdown']).read_text() == 'Example ![](images/a.png)'
        assert (root / 'result/images/a.png').read_bytes() == b'image'
        try:
            mineru.convert(pdf, root / 'result', 'secret')
            raise AssertionError('existing output must be preserved')
        except ValueError:
            pass
    assert len(calls) == 4
    for bad in ('../escape', '/absolute', 'C:/escape', 'images/../../escape'):
        try:
            mineru.extract_zip(archive({'full.md': 'text', bad: 'bad'}), root)
            raise AssertionError('unsafe archive accepted')
        except ValueError:
            pass
    with patch.object(mineru, 'api', return_value={'batch_id':'batch-1', 'file_urls':['https://upload.example/file']}), patch.object(mineru, 'request', return_value=b''):
        try:
            mineru.convert(pdf, root / 'timeout', 'secret', timeout=0)
            raise AssertionError('timeout accepted')
        except ValueError as exc:
            assert 'timed out' in str(exc) and not (root / 'timeout').exists()
print('PASS: mocked cloud upload, download, output safety and timeout')
