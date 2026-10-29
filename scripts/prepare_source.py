#!/usr/bin/env python3
"""Deterministic, dependency-free index for original MinerU Markdown.
Never edits the source or infers a PDF page from a Markdown line number.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone

PAGE_PATTERNS = [
    re.compile(r'^\s*<!--\s*(?:page|page_number|page-num|pdf_page|pagebreak|page_break)\s*[:= ]\s*(\d+)\s*-->\s*$', re.I),
    re.compile(r'^\s*#{1,6}\s+(?:Page|第)\s*(\d+)\s*(?:页)?\s*$', re.I),
]
HEADING = re.compile(r'^(#{1,6})\s+(.+?)\s*#*\s*$')
IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)|<img\b[^>]*src=["\']([^"\']+)["\'][^>]*>', re.I)
FENCE = re.compile(r'^\s*(`{3,}|~{3,})')
LIST_ITEM = re.compile(r'^\s*(?:[-*+]\s|\d+[.)]\s)')


def dump(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def classify(line):
    if not line.strip():
        return 'blank'
    if line.lstrip().startswith('|'):
        return 'table'
    if LIST_ITEM.match(line):
        return 'list_item'
    if IMAGE.search(line):
        return 'image'
    return 'paragraph'


def parse(source_path):
    raw = source_path.read_bytes()
    content = raw.decode('utf-8-sig')
    lines = content.splitlines()
    sections = []
    blocks = []
    visuals = []
    stack = []
    page = None
    current_sec = 'SEC000'
    section = {'id': current_sec, 'title': '前言或无章节正文', 'heading_line': None,
               'block_ids': [], 'status': 'pending', 'summary': '', 'review_notes': '', 'reason': ''}
    sections.append(section)
    buf, start, kind = [], None, None
    fence = None

    def flush():
        nonlocal buf, start, kind
        if not buf:
            return
        n = len(blocks) + 1
        bid = 'B%05d' % n
        item = {'id': bid, 'start_line': start, 'end_line': start + len(buf) - 1,
                'section_id': current_sec, 'section': ' > '.join(x[1] for x in stack) or '前言或无章节正文',
                'page': page, 'kind': kind, 'text': '\n'.join(buf)}
        blocks.append(item)
        sections[-1]['block_ids'].append(bid)
        buf, start, kind = [], None, None

    def push(line, number, typ):
        nonlocal buf, start, kind
        # Keep each table row/list item separately for precise evidence localization.
        if typ in ('table', 'list_item', 'image'):
            flush()
            buf, start, kind = [line], number, typ
            flush()
        else:
            if buf and kind != typ:
                flush()
            if not buf:
                start, kind = number, typ
            buf.append(line)

    for idx, line in enumerate(lines, 1):
        if fence:
            push(line, idx, 'code')
            if line.strip().startswith(fence):
                fence = None
                flush()
            continue
        matched = next((p.match(line) for p in PAGE_PATTERNS if p.match(line)), None)
        if matched:
            flush()
            page = int(matched.group(1))
            continue
        f = FENCE.match(line)
        if f:
            flush()
            fence = f.group(1)[:3]
            push(line, idx, 'code')
            continue
        h = HEADING.match(line)
        if h:
            flush()
            depth, title = len(h.group(1)), h.group(2).strip()
            stack = [s for s in stack if s[0] < depth] + [(depth, title)]
            current_sec = 'SEC%03d' % len(sections)
            sections.append({'id': current_sec, 'title': title, 'heading_line': idx,
                             'block_ids': [], 'status': 'pending', 'summary': '', 'review_notes': '', 'reason': ''})
            push(line, idx, 'heading')
            flush()
            continue
        for m in IMAGE.finditer(line):
            target = (m.group(2) or m.group(3) or '').strip().strip('<>')
            target = re.sub(r'\s+["\'].*$', '', target)
            local = not re.match(r'^(?:https?:|data:)', target, re.I)
            resolved = (source_path.parent / target).resolve() if local else None
            visuals.append({'id': 'V%04d' % (len(visuals)+1), 'line': idx, 'source_ref': target,
                            'local_exists': resolved.is_file() if resolved else None,
                            'local_path': str(resolved) if resolved else None,
                            'status': 'pending', 'reason': '', 'evidence_ids': []})
        typ = classify(line)
        if typ == 'blank':
            flush()
        else:
            push(line, idx, typ)
    flush()
    sections = [s for s in sections if s['block_ids']]
    header = {'format_version': 1, 'source_md': str(source_path),
              'sha256': hashlib.sha256(raw).hexdigest(), 'line_count': len(lines),
              'block_count': len(blocks), 'explicit_page_markers': sum(bool(any(p.match(x) for p in PAGE_PATTERNS)) for x in lines),
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'source_policy': 'markdown_authoritative_no_pdf_inference'}
    return header, {'format_version': 1, 'blocks': blocks}, sections, visuals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('markdown', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--reset', action='store_true', help='Explicitly reset all existing indexes and review work')
    args = parser.parse_args()
    src = args.markdown.expanduser().resolve()
    if not src.is_file() or src.suffix.lower() not in ('.md', '.markdown'):
        parser.error('Expected an existing Markdown (.md/.markdown), not PDF. Never install a converter automatically.')
    out = args.out.expanduser().resolve()
    if src.parent == out and src.name == 'notes.md':
        parser.error('Input is notes.md; select the original MinerU paper Markdown.')
    header, index, sections, visuals = parse(src)
    existing = out / 'source_manifest.json'
    if existing.exists() and not args.reset:
        old = json.loads(existing.read_text(encoding='utf-8'))
        if old.get('sha256') != header['sha256'] or old.get('source_md') != header['source_md']:
            parser.error('A different/modified source is already indexed here. Use a new --out or explicitly --reset after archiving.')
        print('Already prepared; preserving existing evidence and reading progress:', out)
        return
    if not args.reset and any((out / n).exists() for n in ('notes.md', 'evidence.json', 'coverage.json')):
        parser.error('Existing work found; refusing to overwrite. Use a fresh --out or --reset after archiving.')
    out.mkdir(parents=True, exist_ok=True)
    dump(out / 'source_manifest.json', header)
    dump(out / 'source_index.json', index)
    dump(out / 'coverage.json', sections)
    dump(out / 'visuals.json', visuals)
    print('Prepared:', str(out))
    print('Lines:', header['line_count'], '| blocks:', len(index['blocks']), '| sections:', len(sections), '| visuals:', len(visuals))
    if not header['explicit_page_markers']:
        print('No explicit PDF page markers in Markdown. Citations will use source line numbers only.')


if __name__ == '__main__':
    main()
