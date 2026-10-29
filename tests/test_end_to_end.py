"""Self-contained synthetic test of footnotes and optional PDF highlighting.
Only the PDF branch needs PyMuPDF. No external papers are used.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'


def run(*arguments):
    result = subprocess.run([sys.executable, *map(str, arguments)], capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(f'{arguments}\n{result.stdout}\n{result.stderr}')
    return result.stdout


def main():
    import pymupdf
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        src = d / 'paper.md'
        work = d / 'work'
        first = 'Residential density was positively associated with public transit usage after controlling for demographic characteristics.'
        repeat = 'This demonstration text is repeated and appears twice in the document.'
        absent = 'This relevant detail exists only in the converted Markdown source material.'
        src.write_text(f'# Test Article\n\n## Results\n\n{first}\n\n{repeat}\n\n{absent}\n', encoding='utf-8')
        pdf = d / 'paper.pdf'
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((70,80), 'Test Article', fontsize=14)
        page.insert_text((70,120), first, fontsize=9)
        page.insert_text((70,160), repeat, fontsize=9)
        page.insert_text((70,185), repeat, fontsize=9)
        doc.save(pdf)
        doc.close()
        run(SCRIPTS / 'prepare_source.py', src, '--out', work)
        blocks = json.loads((work / 'source_index.json').read_text(encoding='utf-8'))['blocks']
        find = lambda sentence: next(b for b in blocks if sentence in b['text'])['id']
        evidence = []
        for n, sentence in enumerate([first, repeat, absent], start=1):
            evidence.append({'id':f'E{n:04d}', 'claim':f'示例结论{n}', 'claim_type':'result',
                             'status':'verified_direct', 'supports':[{'block_id':find(sentence),'quote':sentence}],
                             'semantic_check':'仅为测试，不允许解释为因果关系。', 'reader_note':False})
        (work / 'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
        run(SCRIPTS / 'verify_evidence.py', work)
        (work / 'notes.md').write_text('# Test Article\n\n## TL;DR\n\n结论一。[^E0001]\n\n结论二。[^E0002]\n\n结论三。[^E0003]\n', encoding='utf-8')
        run(SCRIPTS / 'finalize_notes.py', work)
        before = (work / 'notes.md').read_text(encoding='utf-8')
        assert first in before and absent in before and '源 MD L' in before
        run(SCRIPTS / 'finalize_notes.py', work)
        after = (work / 'notes.md').read_text(encoding='utf-8')
        assert after == before, 'Footnote regeneration must be idempotent.'
        result = json.loads(run(SCRIPTS / 'annotate_pdf.py', work, pdf))
        assert result['counts'] == {'matched':1, 'ambiguous':1, 'not_found':1}, result
        annotated = pymupdf.open(work / 'paper.annotated.pdf')
        page = annotated[0]
        annotations = list(page.annots())
        assert len(annotations) == 1, 'PDF should contain exactly 1 highlight.'
        assert annotations[0].type[1] == 'Highlight' and '示例结论1' in annotations[0].info['content']
        assert annotations[0].info['subject'] == 'E0001'
        assert all(abs(a-b) < 0.01 for a,b in zip(annotations[0].colors['stroke'], (1,207/255,120/255)))
        # Ensure visible highlight isn't drawn over unrelated text on the page.
        assert annotations[0].rect.y0 >= 105 and annotations[0].rect.y1 <= 140
        pix = page.get_pixmap(matrix=pymupdf.Matrix(1,1), annots=True)
        assert pix.width > 100 and pix.height > 100
        original = pymupdf.open(pdf)
        orig_pix = original[0].get_pixmap(matrix=pymupdf.Matrix(1,1), annots=True)
        assert pix.samples != orig_pix.samples, 'Highlighter should visibly modify rendered PDF.'
        original.close()
        annotated.close()
        run(SCRIPTS / 'finalize_notes.py', work)
        note = (work / 'notes.md').read_text(encoding='utf-8')
        assert 'PDF：已高亮（物理页 1）' in note
        assert 'PDF：未标注：' in note and 'Markdown：未生成标注报告' in note
        report_path = work / 'annotation_report.json'
        saved_report = report_path.read_text(encoding='utf-8')
        report = json.loads(saved_report)
        report['annotations'][0]['quote'] = 'different evidence text'
        report_path.write_text(json.dumps(report), encoding='utf-8')
        stale = subprocess.run([sys.executable,str(SCRIPTS/'finalize_notes.py'),str(work)],capture_output=True,text=True)
        assert stale.returncode != 0 and 'stale' in stale.stderr
        report_path.write_text(saved_report, encoding='utf-8')
        # Tampering with the actual footnote should be caught by the final audit.
        full_headings = ['研究背景与研究问题', '理论基础与关键概念', '研究区域、数据与指标',
                         '研究设计与方法', '研究结果', '讨论与解释', '核心研究主线',
                         '五维关键词标签', '待核验事项与后续研究', '阅读覆盖与证据质量']
        prefix = '# Test Article\n\n## TL;DR\n\n观察到相关性。[^E0001]\n\n'
        for h in full_headings:
            prefix += f'## {h}\n\n'
            if h == '五维关键词标签':
                prefix += '\n'.join(f'- **{name}**：未涉及' for name in ['现象','理论','方法','数据','政策']) + '\n\n'
            if h == '核心研究主线':
                prefix += '未能支持统一主线。\n\n'
        (work / 'notes.md').write_text(prefix, encoding='utf-8')
        run(SCRIPTS / 'finalize_notes.py', work)
        tags = {x: {'tag':'未涉及','status':'absent','reason':'模拟数据不包含此标签','evidence_ids':[]} for x in ['phenomenon','theory','method','data','policy']}
        (work/'tags.json').write_text(json.dumps(tags, ensure_ascii=False), encoding='utf-8')
        (work/'storyline.json').write_text(json.dumps({'status':'not_supported','rationale':'样例不构成完整研究主线','breaks':['没有研究问题']},ensure_ascii=False), encoding='utf-8')
        coverage = json.loads((work/'coverage.json').read_text(encoding='utf-8'))
        for sec in coverage:
            run(SCRIPTS/'read_sections.py', work, '--section', sec['id'],'--page','0')
            sec.update(status='reviewed',summary='已检查模拟文本',review_notes='文本已完整展示并阅读')
        (work/'coverage.json').write_text(json.dumps(coverage, ensure_ascii=False), encoding='utf-8')
        audit = json.loads(run(SCRIPTS/'audit_note.py',work))
        assert audit['pass'],audit
        correct=(work/'notes.md').read_text(encoding='utf-8')
        wrong=correct.replace('观察到相关性[E0001](#e0001)。','观察到相关性。[E0001](#e0001)')
        assert wrong!=correct
        (work/'notes.md').write_text(wrong,encoding='utf-8')
        misplaced=subprocess.run([sys.executable,str(SCRIPTS/'audit_note.py'),str(work)],capture_output=True,text=True)
        assert misplaced.returncode!=0 and 'precede sentence punctuation' in misplaced.stdout
        (work/'notes.md').write_text(correct,encoding='utf-8')
        (work / 'notes.md').write_text((work/'notes.md').read_text(encoding='utf-8').replace(first, 'FABRICATED QUOTE'), encoding='utf-8')
        p = subprocess.run([sys.executable,str(SCRIPTS/'audit_note.py'),str(work)], capture_output=True,text=True)
        assert p.returncode != 0 and 'does not reproduce actual source excerpt' in p.stdout
        print(json.dumps({'test':'PASS', 'pdf':result['counts'], 'footnote_idempotent':True,
                          'modified_quote_detected':True, 'audit_passed_before_tampering':True},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
