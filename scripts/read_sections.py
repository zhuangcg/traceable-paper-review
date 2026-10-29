#!/usr/bin/env python3
"""Read all Markdown sections in bounded pages and log which chunks were displayed.
Does not infer that the model cognitively understood the displayed text.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

MAX_CHARS = 10000  # stable pagination across calls / audit


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def pages_for_section(section, blocks):
    pieces = []
    for bid in section['block_ids']:
        block = blocks[bid]
        text = block['text']
        # Split a giant block, preserving source block ID and fragment offsets.
        for offset in range(0, max(1, len(text)), MAX_CHARS - 800):
            part = text[offset: offset + MAX_CHARS - 800]
            pieces.append({'block_id': bid, 'kind': block['kind'], 'start_line': block['start_line'],
                           'end_line': block['end_line'], 'page_marker': block.get('page'),
                           'fragment_start_char': offset, 'fragment_end_char': offset + len(part), 'text': part})
    result, active, length = [], [], 0
    for part in pieces:
        cost = len(part['text']) + 140
        if active and length + cost > MAX_CHARS:
            result.append(active)
            active, length = [], 0
        active.append(part)
        length += cost
    if active:
        result.append(active)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workdir', type=Path)
    p.add_argument('--list', action='store_true', help='List sections and exact page totals (no content displayed)')
    p.add_argument('--section', help='Section ID, e.g. SEC005')
    p.add_argument('--page', type=int, default=0, help='Zero-based page index')
    args = p.parse_args()
    root = args.workdir.expanduser().resolve()
    manifest, source, sections = (read_json(root / n) for n in ('source_manifest.json', 'source_index.json', 'coverage.json'))
    orig = Path(manifest['source_md'])
    if not orig.is_file() or hashlib.sha256(orig.read_bytes()).hexdigest() != manifest['sha256']:
        p.error('Original Markdown missing/modified. Re-index before reading.')
    blocks = {b['id']:b for b in source['blocks']}
    if args.list:
        print(json.dumps({'max_chars_per_page': MAX_CHARS, 'sections': [
            {'id': s['id'], 'title': s['title'], 'pages': len(pages_for_section(s, blocks)),
             'blocks': len(s['block_ids']), 'status': s['status']} for s in sections]}, ensure_ascii=False, indent=2))
        return 0
    if not args.section:
        p.error('Specify --list or --section SECxxx --page N')
    section = next((s for s in sections if s['id'] == args.section), None)
    if not section:
        p.error('Unknown section ID ' + str(args.section))
    pages = pages_for_section(section, blocks)
    if args.page < 0 or args.page >= len(pages):
        p.error('Page out of range. Valid zero-based page range: 0..' + str(len(pages) - 1))
    payload = {'section_id': section['id'], 'section': section['title'],
               'page_index': args.page, 'total_pages': len(pages), 'max_chars': MAX_CHARS,
               'content': pages[args.page], 'next_page': args.page + 1 if args.page + 1 < len(pages) else None}
    # The log only says a text slice was displayed by this command, not that a review was performed.
    log_path = root / 'reading_log.json'
    if log_path.exists():
        log = read_json(log_path)
        if log.get('source_sha256') != manifest['sha256'] or log.get('max_chars') != MAX_CHARS:
            p.error('Reading log source/pagination mismatch; inspect and archive before restarting.')
    else:
        log = {'source_sha256': manifest['sha256'], 'max_chars': MAX_CHARS, 'seen_pages': {}}
    seen = log['seen_pages'].setdefault(section['id'], [])
    if args.page not in seen:
        seen.append(args.page)
        seen.sort()
    write_json(log_path, log)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
