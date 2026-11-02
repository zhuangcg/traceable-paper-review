#!/usr/bin/env python3
"""Run deterministic stages; reading and evidence creation remain agent work."""
import argparse
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def run(*args):
    subprocess.run([sys.executable, str(HERE / args[0]), *map(str, args[1:])], check=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=('prepare', 'verify', 'annotate', 'finish'))
    p.add_argument('workdir', type=Path)
    p.add_argument('--markdown', type=Path)
    p.add_argument('--pdf', type=Path)
    p.add_argument('--paper-id')
    p.add_argument('--keep-csv', action='store_true')
    args = p.parse_args()
    if args.stage == 'prepare':
        if not args.markdown:
            p.error('prepare requires --markdown')
        run('prepare_source.py', args.markdown, '--out', args.workdir)
        run('read_sections.py', args.workdir, '--list')
    elif args.stage == 'verify':
        run('verify_evidence.py', args.workdir)
    elif args.stage == 'annotate':
        run('annotate_markdown.py', args.workdir)
        if args.pdf:
            run('annotate_pdf.py', args.workdir, args.pdf)
        run('finalize_notes.py', args.workdir)
    else:
        run('audit_note.py', args.workdir)
        command = ['finish_review.py', args.workdir, '--clean']
        if args.paper_id:
            command += ['--paper-id', args.paper_id]
        if args.keep_csv:
            command.append('--keep-csv')
        run(*command)

if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
