#!/usr/bin/env python3
"""Convert one local PDF with the opt-in MinerU cloud API."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

API = 'https://mineru.net/api/v4/'
MAX_BYTES = 200 * 1024 * 1024
MAX_RESULT = 512 * 1024 * 1024


def request(url, method='GET', body=None, headers=None):
    if not url.startswith('https://'):
        raise ValueError('MinerU returned a non-HTTPS URL')
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    class SafeRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, response_headers, newurl):
            if req.has_header('Authorization') or urllib.parse.urlsplit(newurl).scheme != 'https':
                raise ValueError('Unsafe redirect')
            return super().redirect_request(req, fp, code, msg, response_headers, newurl)
    try:
        with urllib.request.build_opener(SafeRedirect()).open(req, timeout=120) as response:
            data = response.read(MAX_RESULT + 1)
            if len(data) > MAX_RESULT:
                raise ValueError('Response exceeds size limit')
            return data
    except (urllib.error.URLError, OSError) as exc:
        # Signed URLs and request headers can contain secrets; never echo them.
        raise ValueError('Network request failed; check connection and credentials') from None


def api(path, token, payload=None):
    headers = {'Authorization': 'Bearer ' + token}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    raw = request(API + path, 'POST' if payload is not None else 'GET',
                  json.dumps(payload).encode('utf-8') if payload is not None else None, headers)
    result = json.loads(raw)
    if result.get('code') != 0:
        raise ValueError('MinerU API failed; check token, quota and file limits (code: %s)' % result.get('code'))
    return result['data']


def extract_zip(raw, destination):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if sum(item.file_size for item in members) > MAX_RESULT:
            raise ValueError('Expanded result exceeds size limit')
        for item in members:
            path = PurePosixPath(item.filename)
            if (path.is_absolute() or '..' in path.parts or '\\' in item.filename
                    or ':' in item.filename or (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('Unsafe path in result archive')
        md = [i for i in members if PurePosixPath(i.filename).name == 'full.md' and not i.is_dir()]
        if len(md) != 1:
            raise ValueError('Result must contain exactly one full.md')
        archive.extractall(destination)
        return Path(destination).joinpath(*PurePosixPath(md[0].filename).parts)


def convert(pdf, output, token, timeout=1800, interval=5):
    pdf, output = Path(pdf).resolve(), Path(output).resolve()
    if not pdf.is_file() or pdf.suffix.lower() != '.pdf' or not 0 < pdf.stat().st_size <= MAX_BYTES:
        raise ValueError('Select an existing non-empty PDF of at most 200 MB')
    if output.exists():
        raise ValueError('Output already exists; choose a new output directory')
    if not token:
        raise ValueError('Set the MINERU_TOKEN environment variable')
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    data = api('file-urls/batch', token, {'files': [{'name': pdf.name, 'data_id': digest}], 'model_version': 'vlm'})
    batch = data['batch_id']
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', batch):
        raise ValueError('Invalid batch identifier')
    urls = data['file_urls']
    if len(urls) != 1:
        raise ValueError('Unexpected number of upload URLs')
    request(urls[0], 'PUT', pdf.read_bytes())
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rows = api('extract-results/batch/' + batch, token).get('extract_result', [])
        if rows:
            row = rows[0]
            if row.get('data_id') not in (None, '', digest):
                raise ValueError('Result does not match the submitted PDF')
            if row.get('state') == 'failed':
                raise ValueError('MinerU parsing failed; inspect the task in MinerU')
            if row.get('state') == 'done':
                raw = request(row['full_zip_url'])
                output.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix='mineru-', dir=output.parent) as tmp:
                    md = extract_zip(raw, tmp)
                    relative = md.relative_to(tmp)
                    # Move into a new directory only after the archive is checked.
                    os.rename(tmp, output)
                return {'markdown': str(output / relative), 'source_pdf_sha256': digest, 'batch_id': batch}
        time.sleep(interval)
    raise ValueError('MinerU task timed out; check the task on MinerU before retrying')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf', type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--confirm-upload', action='store_true', help='Confirm this PDF may be uploaded to MinerU')
    args = p.parse_args()
    if not args.confirm_upload:
        p.error('Cloud upload requires explicit consent: pass --confirm-upload')
    try:
        print(json.dumps(convert(args.pdf, args.out, os.environ.get('MINERU_TOKEN')), ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        p.exit(1, 'MinerU conversion failed: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
