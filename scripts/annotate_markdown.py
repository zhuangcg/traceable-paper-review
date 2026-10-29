#!/usr/bin/env python3
"""Create a separate, conservatively highlighted Markdown copy of the source."""
import argparse
import json
import shutil
from pathlib import Path
from annotate_pdf import color_for, sha256
from verify_evidence import check

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workdir', type=Path)
    args = p.parse_args(); root = args.workdir.resolve()
    checked = check(root, write=False)
    if not checked['pass']:
        p.error(str(checked['errors']))
    out = root / 'paper.annotated.md'
    if out.exists(): p.error('Annotated Markdown already exists; use a fresh workdir.')
    manifest = json.loads((root/'source_manifest.json').read_text(encoding='utf8'))
    source = Path(manifest['source_md']); text = source.read_text(encoding='utf-8-sig')
    if source.resolve() == out.resolve(): p.error('Cannot overwrite source.')
    blocks = {b['id']: b for b in json.loads((root/'source_index.json').read_text(encoding='utf8'))['blocks']}
    evidence = json.loads((root/'evidence.json').read_text(encoding='utf8'))
    lines = text.splitlines(keepends=True); starts = [0]
    for line in lines: starts.append(starts[-1]+len(line))
    edits, rows = [], []
    for item in evidence:
        if item['status'] not in ('verified_direct','verified_synthesis'): continue
        for n, sup in enumerate(item['supports'],1):
            block = blocks[sup['block_id']]; quote = sup['quote']; row = {'evidence_id':item['id'],'support':n,'quote':quote}
            start = starts[block['start_line']-1]; end = starts[block['end_line']]
            chunk = text[start:end]; pos = chunk.find(quote)
            if block['kind'] != 'paragraph' or '<table' in chunk.lower() or any(x in quote for x in ('\n','<','>','$','`','[',']')):
                row.update(status='unsafe_markup',reason='包含 Markdown/HTML/公式或跨行，避免破坏原文结构')
            elif pos < 0 or chunk.count(quote) != 1:
                row.update(status='not_unique',reason='原文块内无法唯一逐字定位')
            elif any(start+pos < b and start+pos+len(quote) > a for a,b,*_ in edits):
                row.update(status='overlap',reason='与已有高亮重叠，保留先前片段')
            else:
                a=start+pos; b=a+len(quote); color=color_for(item.get('claim_type'))
                edits.append((a,b,color,item['id'])); row.update(status='matched',color=color,line=block['start_line'])
            rows.append(row)
    for a,b,color,eid in sorted(edits,reverse=True):
        text=text[:a]+f'<mark style="background-color:{color}">'+text[a:b]+'</mark> '+f'[({eid})](notes.md#{eid.lower()})'+text[b:]
    text += '\n\n---\n\n背景／理论：蓝色；数据／方法：绿色；结果：橙色；讨论／局限：紫色；其他：灰色。颜色依赖阅读器支持 HTML，标号链接和证据清单可作替代。\n'
    # Copy only local referenced images whose relative path stays inside the output.
    visuals=json.loads((root/'visuals.json').read_text(encoding='utf8'))
    for image in visuals:
        ref=image.get('source_ref',''); target=(root/ref).resolve()
        if image.get('local_exists') and root in target.parents:
            source_image=Path(image['local_path'])
            if target.exists() and (not target.is_file() or sha256(source_image) != sha256(target)):
                p.error('Existing image differs from source: '+str(target))
            if not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source_image,target)
    out.write_text(text,encoding='utf8')
    (root/'markdown_annotation_report.json').write_text(json.dumps({'source_sha256':manifest['sha256'],'output_sha256':sha256(out),'annotations':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'output':str(out),'matched':len(edits),'total':len(rows)},ensure_ascii=False))

if __name__ == '__main__': main()
