#!/usr/bin/env python3
"""Optional, conservative PDF highlighter for already verified Markdown excerpts.
Requires PyMuPDF only for this PDF-annotation step. Never installs dependencies,
never OCRs, never overwrites source PDF, and never accepts fuzzy text matches.
"""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from verify_evidence import check


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def tokens(raw):
    return [x.casefold() for x in re.findall(r'\w+|[^\w\s]', unicodedata.normalize('NFKC', str(raw)))]


def color_for(claim_type):
    return {'background':'#a6cee3', 'problem':'#a6cee3', 'theory':'#a6cee3',
            'definition':'#a6cee3', 'data':'#b2df8a', 'method':'#b2df8a',
            'result':'#ffcf78', 'discussion':'#cbb5e8', 'limitation':'#cbb5e8',
            'conclusion':'#cbb5e8'}.get(claim_type, '#d0d0d0')


def label_for(claim_type):
    return {'background':'背景/理论', 'problem':'背景/理论', 'theory':'背景/理论',
            'definition':'背景/理论', 'data':'数据/方法', 'method':'数据/方法',
            'result':'结果', 'discussion':'讨论/局限', 'limitation':'讨论/局限',
            'conclusion':'讨论/局限'}.get(claim_type, '其他')


def pdf_tokens(page):
    """PDF producer order, not top-to-bottom y sorting (safer for two columns)."""
    expanded = []
    for x0, y0, x1, y1, word, block, line, word_ix in page.get_text('words', sort=False):
        for t in tokens(word):
            expanded.append((t, (x0, y0, x1, y1, int(block), int(line))))
    return expanded


def occurrences(haystack, needles):
    if not needles or len(needles) > len(haystack):
        return []
    fst = needles[0]
    n = len(needles)
    return [(i, i + n) for i, e in enumerate(haystack) if e[0] == fst and
            i + n <= len(haystack) and all(haystack[i+j][0] == needles[j] for j in range(n))]


def merged_rects(words, fitz):
    """Return one bounding rectangle per distinct PDF text line of the exact match."""
    groups = []
    for _, (x0, y0, x1, y1, block, line) in words:
        rect = fitz.Rect(x0, y0, x1, y1)
        if groups and groups[-1][0] == (block, line):
            groups[-1] = ((block, line), groups[-1][1] | rect)
        else:
            groups.append(((block, line), rect))
    return [r for _, r in groups]


def annotate(root, pdf, output, force):
    checked = check(root, write=False)
    if not checked['pass']:
        return {'pass': False, 'errors': checked['errors']}
    if not pdf.exists():
        return {'pass': False, 'errors': ['PDF not found: ' + str(pdf)]}
    if pdf.resolve() == output.resolve():
        return {'pass': False, 'errors': ['Output must differ from original PDF.']}
    if output.exists() and not force:
        return {'pass': False, 'errors': ['Output exists; do not overwrite without --overwrite: ' + str(output)]}
    try:
        import pymupdf as fitz
    except ImportError:
        return {'pass': False, 'errors': ['PyMuPDF is not installed. Notes remain usable. The agent may install PyMuPDF in a task-local virtual environment when authorized; this script does not install dependencies.']}
    manifest = json.loads((root / 'source_manifest.json').read_text(encoding='utf-8'))
    evidence = json.loads((root / 'evidence.json').read_text(encoding='utf-8'))
    try:
        document = fitz.open(pdf)
    except Exception as e:
        return {'pass': False, 'errors': ['Cannot read PDF: ' + str(e)]}
    if document.is_encrypted and not document.authenticate(''):
        document.close()
        return {'pass': False, 'errors': ['Encrypted PDF without accessible text; cannot annotate.']}
    all_pages = [pdf_tokens(page) for page in document]
    try:
        report_output = output.relative_to(root).as_posix()
    except ValueError:
        report_output = str(output)
    output_report = {
        'source_pdf': str(pdf), 'source_pdf_sha256': sha256(pdf),
        'source_markdown_sha256': manifest['sha256'],
        'output_pdf': report_output, 'matching_policy': 'only unique, same-page, exact normalized word-sequence matches; no OCR, no fuzzy placement',
        'annotations': [],
    }
    for item in evidence:
        if item['status'] not in ('verified_direct', 'verified_synthesis'):
            continue
        for support_number, support in enumerate(item['supports'], start=1):
            quote = support['quote']
            needle = tokens(quote)
            record = {'evidence_id': item['id'], 'support': support_number, 'quote': quote}
            if len(needle) < 6:
                record.update({'status': 'skipped_short', 'reason': 'Less than six normalized tokens; not safe to locate automatically.'})
                output_report['annotations'].append(record)
                continue
            matches = []
            for page_ix, expanded in enumerate(all_pages):
                for start, stop in occurrences(expanded, needle):
                    matches.append((page_ix, start, stop))
            if len(matches) != 1:
                record.update({'status': 'not_found' if not matches else 'ambiguous',
                               'reason': 'No exact PDF word-sequence match' if not matches else 'More than one exact occurrence; manual resolution required',
                               'candidate_pdf_pages': sorted(set(m[0] + 1 for m in matches))})
                output_report['annotations'].append(record)
                continue
            page_ix, start, stop = matches[0]
            rects = merged_rects(all_pages[page_ix][start:stop], fitz)
            if not rects or any(r.is_empty for r in rects):
                record.update({'status': 'invalid_geometry', 'reason': 'Located text but could not build valid highlight rectangles'})
                output_report['annotations'].append(record)
                continue
            page = document[page_ix]
            annot = page.add_highlight_annot(rects)
            # Embed the Chinese interpretation inside the highlight's own comment,
            # so Zotero's external-highlight import can carry the explanation too.
            comment = (f'{item["id"]} | {label_for(item.get("claim_type"))} | 证据片段 {support_number}/{len(item["supports"])}；其他片段的标注状态见笔记。\n对应解读：{item["claim"]}\n'
                       f'解释边界：{item.get("semantic_check", "")}\n'
                       f'原文定位：{support["block_id"]} (support {support_number})')
            annot.set_info(title='Traceable Paper Review', subject=item['id'], content=comment)
            color = color_for(item.get('claim_type'))
            annot.set_colors(stroke=tuple(int(color[i:i+2], 16)/255 for i in (1, 3, 5)))
            annot.set_opacity(0.34)
            annot.update()
            record.update({'status': 'matched', 'color': color, 'pdf_page': page_ix + 1, 'rectangles': [list(r) for r in rects],
                           'annotation_xref': annot.xref})
            output_report['annotations'].append(record)
    counts = {}
    for row in output_report['annotations']:
        counts[row['status']] = counts.get(row['status'], 0) + 1
    output_report['counts'] = counts
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        document.save(output, garbage=3, deflate=True)
    except Exception as e:
        document.close()
        return {'pass': False, 'errors': ['PDF save failed: ' + str(e)], 'counts': counts}
    finally:
        document.close()
    output_report['output_sha256'] = sha256(output)
    (root / 'annotation_report.json').write_text(json.dumps(output_report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'pass': True, 'output_pdf': str(output), 'counts': counts, 'matched': counts.get('matched', 0),
            'not_matched': sum(v for k,v in counts.items() if k != 'matched'),
            'warning': 'Only exact unique text matches were annotated. PDF page number is physical page index, not necessarily printed page label.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workdir', type=Path)
    p.add_argument('pdf', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--overwrite', action='store_true', help='Explicitly replace an existing derived annotated PDF; never source PDF')
    args = p.parse_args()
    root = args.workdir.expanduser().resolve()
    pdf = args.pdf.expanduser().resolve()
    output = args.output.expanduser().resolve() if args.output else (root / 'paper.annotated.pdf').resolve()
    result = annotate(root, pdf, output, args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['pass'] else 2


if __name__ == '__main__':
    sys.exit(main())
