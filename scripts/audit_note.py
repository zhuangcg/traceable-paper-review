#!/usr/bin/env python3
"""Dependency-free mechanical audit for a traceable academic paper note.
PASS means structural/excerpt checks, NOT scientific/semantic correctness.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from verify_evidence import check as check_evidence
from read_sections import pages_for_section, MAX_CHARS
from citation_style import misplaced_lines

DIMENSIONS = {'phenomenon': '现象', 'theory': '理论', 'method': '方法',
              'data': '数据', 'policy': '政策'}
REQUIRED = ['TL;DR', '研究背景与研究问题', '理论基础与关键概念', '研究区域、数据与指标',
            '研究设计与方法', '研究结果', '讨论与解释', '核心研究主线', '五维关键词标签',
            '待核验事项与后续研究', '阅读覆盖与证据质量']
FOOTNOTE_REF = re.compile(r'\[(E\d{4,})\]\(#\1\)', re.I)
FOOTNOTE_DEF = re.compile(r'^### (E\d{4,})$', re.M)
FOOTNOTE_START = '<!-- TPR:EVIDENCE:START -->'
FOOTNOTE_END = '<!-- TPR:EVIDENCE:END -->'
ANY_EID = re.compile(r'\bE\d{4,}\b')
PAPER_FACT_HINT = re.compile(r'论文|作者|本文|研究|数据显示|结果|发现|使用|采用|提出|表明|估计|显著|基于|指出')


def load(root, filename, errors):
    path = root / filename
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        errors.append(filename + ': ' + str(exc))
        return None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workdir', type=Path)
    args = p.parse_args()
    root = args.workdir.expanduser().resolve()
    errors, warnings = [], []
    r = check_evidence(root, write=False, include_map=True)
    errors.extend(r['errors'])
    warnings.extend(r['warnings'])
    if not r['pass']:
        warnings.append('Evidence excerpts have not passed verification; first run verify_evidence.py.')
    evidence = load(root, 'evidence.json', errors)
    coverage = load(root, 'coverage.json', errors)
    visuals = load(root, 'visuals.json', errors)
    tags = load(root, 'tags.json', errors)
    storyline = load(root, 'storyline.json', errors)
    citations = load(root, 'citation_map.json', errors)
    if isinstance(citations, dict) and r.get('pass') and citations != r.get('citation_map'):
        errors.append('citation_map.json is stale or edited; rerun verify_evidence.py before writing notes.')
    index = load(root, 'source_index.json', errors)
    manifest = load(root, 'source_manifest.json', errors)
    reading_log = load(root, 'reading_log.json', errors)
    note = root / 'notes.md'
    if not note.exists():
        errors.append('Missing notes.md')
        text = ''
    else:
        text = note.read_text(encoding='utf-8')
    evidence_dict = {e.get('id'): e for e in (evidence or []) if isinstance(e, dict) and e.get('id')}
    verified = {eid for eid, e in evidence_dict.items() if str(e.get('status','')).startswith('verified_')}

    for heading in REQUIRED:
        if not any(re.search(r'^##\s+' + re.escape(label) + r'\s*$', text, re.M) for label in ([heading, '内容提要'] if heading == 'TL;DR' else [heading])):
            errors.append('Missing required notes.md section: ' + heading)

    if text.count(FOOTNOTE_START) != 1 or text.count(FOOTNOTE_END) != 1:
        errors.append('Generated same-file evidence footnotes missing/duplicated; run finalize_notes.py')
    body, separator, footnote_section = text.partition(FOOTNOTE_START)
    used = set(FOOTNOTE_REF.findall(body))
    for number in misplaced_lines(body):
        errors.append('Evidence citation must precede sentence punctuation at notes.md L'+str(number))
    defs = FOOTNOTE_DEF.findall(footnote_section if separator else '')
    for eid in used:
        if eid not in verified:
            errors.append('Note references unverified/missing evidence: ' + eid)
        if defs.count(eid) != 1:
            errors.append('Footnote definition missing or duplicated for: ' + eid)
        if isinstance(citations, dict) and eid in citations and citations[eid]['locator'] not in body:
            errors.append('Note citation not using canonical footnote reference: ' + eid)
        item = evidence_dict.get(eid, {})
        match = re.search(r'^### ' + re.escape(eid) + r'\s*$(.*?)(?=^### E\d{4,}\s*$|<!-- TPR:EVIDENCE:END -->)', footnote_section, re.M | re.S)
        own_section = match.group(1) if match else ''
        for sup in item.get('supports', []):
            # Normalized exact excerpts must also appear in the SAME note, not merely evidence.md.
            excerpt = ' '.join(sup.get('quote', '').split())
            if excerpt and excerpt not in own_section:
                errors.append('Footnote does not reproduce actual source excerpt for: ' + eid)
        if item.get('claim') and item['claim'] not in own_section:
            errors.append('Footnote lacks corresponding claim: ' + eid)
        if own_section.count('- PDF：') != len(item.get('supports', [])) or own_section.count('- Markdown：') != len(item.get('supports', [])):
            errors.append('Annotation status missing for a support: ' + eid)
    extra_defs = set(defs) - used
    if extra_defs:
        errors.append('Unused footnote definitions: ' + ','.join(sorted(extra_defs)))
    for eid in sorted(set(ANY_EID.findall(text))):
        if eid not in evidence_dict:
            errors.append('Unknown evidence ID mentioned in notes.md: ' + eid)

    if isinstance(reading_log, dict) and isinstance(manifest, dict):
        if reading_log.get('source_sha256') != manifest.get('sha256') or reading_log.get('max_chars') != MAX_CHARS:
            errors.append('Reading log source hash/pagination does not match current source')
    if not isinstance(coverage, list):
        errors.append('coverage.json must be an array')
    else:
        for item in coverage:
            sec = item.get('id', 'unknown')
            status = item.get('status')
            if status not in ('reviewed', 'skipped_with_reason'):
                errors.append(sec + ' pending/invalid section coverage: ' + str(status))
            if status == 'reviewed' and (not str(item.get('summary','')).strip() or not str(item.get('review_notes','')).strip()):
                errors.append(sec + ' reviewed without summary/review_notes')
            if status == 'reviewed' and isinstance(index, dict) and isinstance(reading_log, dict):
                block_map = {b['id']: b for b in index['blocks']}
                total = len(pages_for_section(item, block_map))
                seen_pages = set(reading_log.get('seen_pages', {}).get(sec, []))
                missing = set(range(total)) - seen_pages
                if missing:
                    errors.append(sec + ' marked reviewed but pages not displayed: ' + str(sorted(missing)))
            if status == 'skipped_with_reason':
                if not str(item.get('reason','')).strip():
                    errors.append(sec + ' skipped without reason')
                if re.search(r'results?|methods?|discussion|conclusions?|introduction|引言|结果|方法|讨论|结论|数据|附录|补充|appendix|supplement', item.get('title',''), re.I):
                    errors.append(sec + ' core chapter skipped: ' + str(item.get('title','')))
    if not isinstance(visuals, list):
        errors.append('visuals.json must be an array')
        visuals = []
    for im in visuals:
        status = im.get('status')
        if status not in ('inspected', 'unavailable', 'not_relevant'):
            errors.append(im.get('id', '?') + ' image not reviewed: ' + str(status))
        elif status in ('unavailable', 'not_relevant') and not str(im.get('reason','')).strip():
            errors.append(im.get('id', '?') + ' missing reason for ' + status)
        if status == 'unavailable':
            warnings.append(im.get('id', '?') + ' unavailable; results dependent on this image must be qualified.')
        for eid in im.get('evidence_ids', []):
            if eid not in verified:
                errors.append(im.get('id','?') + ' has unknown/unverified evidence_id: ' + str(eid))

    if not isinstance(tags, dict):
        errors.append('tags.json must be an object with 5 mandatory dimensions')
        tags = {}
    grounded = []
    for dim, cn in DIMENSIONS.items():
        entry = tags.get(dim)
        if not isinstance(entry, dict):
            errors.append('Missing tags dimension: ' + dim)
            continue
        tag, status, ids = entry.get('tag'), entry.get('status'), entry.get('evidence_ids')
        if status == 'grounded':
            if not isinstance(tag, str) or not tag.strip() or tag == '未涉及':
                errors.append(dim + ' grounded without a real tag')
            else:
                grounded.append((dim, tag.casefold().replace(' ', '')))
                if ('#' + dim + '/' + tag) not in text:
                    errors.append(dim + ' grounded tag missing in notes: #' + dim + '/' + tag)
            if not isinstance(ids, list) or not ids or any(eid not in verified for eid in ids):
                errors.append(dim + ' grounded tag must cite verified evidence IDs')
        elif status == 'absent':
            if tag != '未涉及' or ids != [] or not str(entry.get('reason','')).strip():
                errors.append(dim + ' absent tag requires 未涉及, zero evidence_ids, and a reason')
            if ('#' + dim + '/') in text:
                errors.append(dim + ' absent must not create a searchable hashtag')
        else:
            errors.append(dim + ' invalid tag status: ' + str(status))
        if not re.search(r'^-\s+\*\*' + cn + r'\*\*\s*[:：]', text, re.M):
            errors.append('Missing five-dimensional display slot: ' + cn)
    values = [v for _, v in grounded]
    if len(values) != len(set(values)):
        errors.append('Duplicate tag strings across dimensions; semantic overlap also requires manual audit')
    else:
        warnings.append('Semantic similarity between distinct tag strings is NOT machine-verified; manually compare five roles.')

    if not isinstance(storyline, dict):
        errors.append('storyline.json must be an object')
        storyline = {}
    ss = storyline.get('status')
    nodes = storyline.get('nodes', [])
    edges = storyline.get('edges', [])
    if ss not in ('coherent', 'partial', 'not_supported'):
        errors.append('Invalid storyline.status')
    if not str(storyline.get('rationale','')).strip():
        errors.append('Storyline missing rationale')
    if ss in ('coherent', 'partial'):
        if not isinstance(nodes, list) or len(nodes) < 2:
            errors.append('Storyline should have at least 2 nodes when drawn')
            nodes = []
        if '```mermaid' not in text or 'flowchart' not in text:
            errors.append('Missing Mermaid flowchart for coherent/partial storyline')
        node_ids = set()
        for node in nodes:
            nid = node.get('id', '')
            if nid in node_ids or not re.fullmatch(r'N\d+', nid):
                errors.append('Duplicate/invalid storyline node: ' + nid)
            node_ids.add(nid)
            if nid not in text:
                errors.append('Storyline node missing from Markdown: ' + nid)
            if not node.get('evidence_ids') or any(eid not in verified for eid in node['evidence_ids']):
                errors.append(nid + ' missing verified evidence support')
            for eid in node.get('evidence_ids', []):
                if eid not in text:
                    errors.append(nid + ' evidence ID not reflected in diagram or explanation: ' + eid)
        for e in edges:
            if e.get('from') not in node_ids or e.get('to') not in node_ids or not str(e.get('relation','')).strip():
                errors.append('Invalid/unsupported storyline edge metadata: ' + repr(e))
        if ss == 'partial' and not storyline.get('breaks'):
            errors.append('Partial storyline needs explicit breaks')
    elif ss == 'not_supported' and not storyline.get('breaks'):
        errors.append('not_supported storyline must identify evidence/logic gaps')

    if re.search(r'^reading_status:\s*["\']?verified', text, re.M) and any(im.get('status') == 'unavailable' for im in visuals):
        errors.append('reading_status: verified conflicts with unavailable figures')
    if re.search(r'<(?:准确论文标题|原文|关键|论文|单个术语)', text):
        errors.append('Template placeholders still present in notes.md')
    if not used:
        errors.append('No clickable verified evidence citations found in notes.md')
    # Heuristic only. This is NOT a guarantee of sentence-level citation coverage.
    in_fence, in_frontmatter = False, False
    for lineno, line in enumerate(body.splitlines(), 1):
        if lineno == 1 and line.strip() == '---':
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line.strip() == '---':
                in_frontmatter = False
            continue
        if line.strip().startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence or line.startswith('#') or line.startswith('>'):
            continue
        if line.startswith('|'):
            if re.search(r'\d', line) and not FOOTNOTE_REF.search(line) and not re.match(r'^\|[-|: ]+\|$', line):
                warnings.append('Quantitative Markdown table row may lack a direct citation at L' + str(lineno))
            continue
        if len(line.strip()) >= 55 and PAPER_FACT_HINT.search(line) and not FOOTNOTE_REF.search(line) and '[读者分析]' not in line:
            warnings.append('Possible uncited factual prose at notes.md L' + str(lineno) + ' (manual review)')
    audit = {'pass': not errors, 'scope': 'mechanical source integrity, excerpt matching, structure, basic citation and state checks only',
             'cannot_verify': ['PDF highlight correctness requires visual/manual check', 'semantic entailment', 'completeness of human/AI reading', 'accuracy of figure interpretation',
                               'whether lines without detectable factual keywords require citations', 'semantic independence of tags'],
             'errors': errors, 'warnings': warnings,
             'stats': {'registered_evidence': len(evidence_dict), 'linked_evidence': len(used),
                       'sections': len(coverage or []), 'visuals': len(visuals), 'grounded_tags': len(grounded),
                       'storyline_status': ss}}
    (root / 'audit_report.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit['pass'] else 2


if __name__ == '__main__':
    sys.exit(main())
