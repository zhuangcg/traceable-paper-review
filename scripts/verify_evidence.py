#!/usr/bin/env python3
"""Verify exact evidence excerpts and emit deterministic inline citation locators.
Only mechanical grounding is checked; semantic support requires human/model review.
"""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

STATUSES = {'verified_direct', 'verified_synthesis', 'uncertain', 'rejected'}
CLAIM_TYPES = {'background','problem','theory','definition','data','method','result','discussion','limitation','conclusion','metadata','other'}
ID_RE = re.compile(r'^E\d{4,}$')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def normalize(value):
    return ' '.join(unicodedata.normalize('NFC', value).replace('\u00a0', ' ').split())


def safe(text):
    return str(text).replace('\n', ' ').replace('`', '\\`')


def check(workdir, write=True, include_map=False):
    errors, warnings = [], []
    try:
        manifest = load(workdir / 'source_manifest.json')
        index = load(workdir / 'source_index.json')
        evidence = load(workdir / 'evidence.json')
    except (FileNotFoundError, ValueError) as ex:
        return {'pass': False, 'errors': [str(ex)], 'warnings': []}
    source_path = Path(manifest['source_md'])
    if not source_path.exists():
        errors.append('Source Markdown missing: ' + str(source_path))
    elif hashlib.sha256(source_path.read_bytes()).hexdigest() != manifest['sha256']:
        errors.append('Source SHA256 changed: previous evidence anchors are invalid.')
    if not isinstance(evidence, list):
        errors.append('evidence.json must be an array')
        evidence = []
    blocks = {b['id']: b for b in index['blocks']}
    seen, citation_map, rendered = set(), {}, ['# 原文证据账本', '', '> 注意：摘录精确匹配并不等于语义推断经过科学验证。', '']
    for item in evidence:
        if not isinstance(item, dict):
            errors.append('Evidence array contains a non-object')
            continue
        eid = item.get('id', '')
        if not ID_RE.fullmatch(eid):
            errors.append('Invalid evidence ID: ' + str(eid))
            continue
        if eid in seen:
            errors.append('Duplicate evidence ID: ' + eid)
            continue
        seen.add(eid)
        if item.get('claim_type') not in CLAIM_TYPES:
            errors.append(eid + ' invalid or missing claim_type')
        if not isinstance(item.get('reader_note', False), bool):
            errors.append(eid + ' reader_note must be boolean')
        status = item.get('status')
        if status not in STATUSES:
            errors.append(eid + ' invalid status')
            continue
        claim = item.get('claim', '')
        if not isinstance(claim, str) or not claim.strip():
            errors.append(eid + ' missing claim')
        if not isinstance(item.get('semantic_check'), str) or not item.get('semantic_check', '').strip():
            errors.append(eid + ' missing semantic_check (semantic review required)')
        supports = item.get('supports', [])
        if not isinstance(supports, list) or (status.startswith('verified_') and not supports):
            errors.append(eid + ' verified claim must have supports')
            supports = []
        if status == 'verified_synthesis' and len(supports) < 2 and '综合' not in str(item.get('semantic_check', '')):
            warnings.append(eid + ' synthesis has only one support; check reasoning explicitly')
        positions = []
        for support in supports:
            if not isinstance(support, dict):
                errors.append(eid + ' support must be an object')
                continue
            block_id = support.get('block_id')
            block = blocks.get(block_id)
            if not block:
                errors.append(eid + ' unknown block: ' + str(block_id))
                continue
            quote = support.get('quote', '')
            if not isinstance(quote, str) or not quote.strip():
                errors.append(eid + ' has empty quote at ' + block_id)
                continue
            if normalize(quote) not in normalize(block['text']):
                errors.append(eid + ' quote not found verbatim in ' + block_id)
                continue
            if len(quote.split()) > 90:
                warnings.append(eid + ': long excerpt (>90 tokens); prefer the shortest complete supporting sentence(s).')
            positions.append((block, quote))
        if status.startswith('verified_') and len(positions) != len(supports):
            errors.append(eid + ' not all supporting excerpts verified')
        if status.startswith('verified_') and positions:
            locparts = []
            for b, _ in positions:
                sec = b['section'].split(' > ')[-1]
                page = (', p.' + str(b['page'])) if b.get('page') is not None else ''
                locparts.append('§' + sec + page + '，源文 L' + str(b['start_line']) + '–L' + str(b['end_line']))
            # Keep order while removing duplicated locators.
            locparts = list(dict.fromkeys(locparts))
            locator = '[' + eid + '](#' + eid.lower() + ')'
            citation_map[eid] = {'locator': locator, 'support_blocks': [x[0]['id'] for x in positions], 'source_locators': locparts}
            rendered.extend(['<a id="' + eid.lower() + '"></a>', '', '## ' + eid + ' · ' + safe(item.get('claim','')), '',
                             '- 状态：`' + status + '`', '- 内联定位：' + locator,
                             '- 语义核查说明：' + safe(item.get('semantic_check','')), ''])
            for b, quote in positions:
                rendered.extend(['- 源文件：`' + safe(manifest['source_md']) + '`',
                                 '- 源文位置：`' + b['id'] + '`，' + safe(b['section']) +
                                 '，行 ' + str(b['start_line']) + '–' + str(b['end_line']) +
                                 (('，明示页码 p.' + str(b['page'])) if b['page'] is not None else '，未提供可信 PDF 页码'),
                                 '- 原文摘录：', '> ' + safe(quote), ''])
        elif status in ('uncertain', 'rejected'):
            rendered.extend(['<a id="' + eid.lower() + '"></a>', '', '## ' + eid + ' · [待核验/不支持] ' + safe(claim), '',
                             '- 状态：`' + status + '`', '- 问题：' + safe(item.get('semantic_check','')), ''])
    if write and not errors:
        dump(workdir / 'citation_map.json', citation_map)
        (workdir / 'evidence.md').write_text('\n'.join(rendered).rstrip() + '\n', encoding='utf-8')
    result = {'pass': not errors, 'errors': errors, 'warnings': warnings,
              'evidence_total': len(evidence), 'verified_total': len(citation_map)}
    if include_map:
        result['citation_map'] = citation_map
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workdir', type=Path)
    args = p.parse_args()
    result = check(args.workdir.expanduser().resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['pass'] else 2)


if __name__ == '__main__':
    main()
