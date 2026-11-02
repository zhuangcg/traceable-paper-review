#!/usr/bin/env python3
"""Report local prerequisites without installing or uploading anything."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.request

def inspect(workdir, network=False):
    path = Path(workdir).expanduser().resolve()
    parent = path
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    writable = False
    try:
        with tempfile.TemporaryFile(dir=parent):
            writable = True
    except OSError:
        pass
    try:
        import pymupdf
        pdf = hasattr(pymupdf, 'open')
    except (ImportError, OSError):
        pdf = False
    net = 'not_checked'
    if network:
        try:
            with urllib.request.urlopen('https://mineru.net/', timeout=5) as response:
                net = 'reachable' if response.status == 200 else 'unavailable'
        except (OSError, ValueError):
            net = 'unavailable'
    return {'python': sys.version.split()[0], 'python_supported': sys.version_info >= (3, 9),
            'interpreter': sys.executable, 'pymupdf_available': pdf,
            'workdir': str(path), 'writable_parent': str(parent), 'writable': writable,
            'mineru_token_set': bool(os.environ.get('MINERU_TOKEN')), 'network': net}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workdir', type=Path)
    p.add_argument('--check-network', action='store_true', help='Opt in to a MinerU connectivity probe')
    args = p.parse_args()
    print(json.dumps(inspect(args.workdir, args.check_network), ensure_ascii=False, indent=2))
