#!/usr/bin/env python3
"""Add a plain-Markdown evidence section and per-support annotation status."""
import argparse
import json
import re
from pathlib import Path
from verify_evidence import check
from annotate_pdf import label_for
from annotation_state import load_reports, state
from citation_style import normalize_citations

START='<!-- TPR:EVIDENCE:START -->'
END='<!-- TPR:EVIDENCE:END -->'
REF=re.compile(r'\[(E\d{4,})\]\(#\1\)', re.I)
OLD_START='<!-- TPR:FOOTNOTES:START -->'
OLD_END='<!-- TPR:FOOTNOTES:END -->'

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('workdir',type=Path); root=p.parse_args().workdir.resolve()
    result=check(root,write=False,include_map=True)
    if not result['pass']: p.error(str(result['errors']))
    path=root/'notes.md'; body=path.read_text(encoding='utf8')
    for begin,end in [(START,END),(OLD_START,OLD_END)]:
        if (begin in body) != (end in body): p.error('Evidence markers inconsistent')
        if begin in body:
            left,tail=body.split(begin,1); _,right=tail.split(end,1); body=left+right
    body=re.sub(r'\[\^(E\d{4,})\](?!:)',lambda m:f'[{m[1]}](#{m[1].lower()})',body).rstrip()
    body=normalize_citations(body)
    if re.search(r'^\[\^E\d{4,}\]:',body,re.M): p.error('Manual footnote definitions found; preserve and migrate them explicitly')
    ids=list(dict.fromkeys(REF.findall(body)))
    if not ids or any(eid not in result['citation_map'] for eid in ids): p.error('No valid evidence references, or unverified reference')
    items={x['id']:x for x in json.loads((root/'evidence.json').read_text(encoding='utf8'))}
    blocks={x['id']:x for x in json.loads((root/'source_index.json').read_text(encoding='utf8'))['blocks']}
    manifest=json.loads((root/'source_manifest.json').read_text(encoding='utf8'))
    try: reports, available = load_reports(root, items, manifest)
    except (ValueError,OSError) as exc: p.error(str(exc))
    out=[START,'','## 原文证据与标注状态','', '标注按每条原文片段分别报告；未找到或未生成时不会猜测位置。','', '颜色：蓝色＝背景与理论；绿色＝数据与方法；橙色＝结果；紫色＝讨论与局限；灰色＝其他。','']
    for label in ('PDF','Markdown'):
        entries=[(eid,n,reports.get((label,eid,n))) for eid in ids for n in range(1,len(items[eid]['supports'])+1)]
        matched=sum(1 for _,_,row in entries if row and row.get('status')=='matched')
        missed=[f'{eid}（片段{n}）' for eid,n,row in entries if not row or row.get('status')!='matched']
        out.append(f'- {label}：{matched}/{len(entries)} 个片段已标注；未标注：'+('、'.join(missed) if missed else '无')+'。')
    out.append('')
    for eid in ids:
        item=items[eid]; out += [f'### {eid}', '', '**类别：** '+label_for(item.get('claim_type')),'','**对应论断：** '+item['claim'],'','**解释边界：** '+item['semantic_check'],'']
        for n,sup in enumerate(item['supports'],1):
            b=blocks[sup['block_id']]; quote=' '.join(sup['quote'].split())
            out += [f'**片段 {n}｜源 MD L{b["start_line"]}–L{b["end_line"]}：**','', '> '+quote,'']
            for label in ('PDF','Markdown'):
                row=state(reports,available,label,eid,n)
                if row['status']=='not_generated': desc='未生成标注报告'
                elif row['status']=='not_recorded': desc='未标注：报告缺少该片段记录'
                elif row['status']=='matched':
                    desc='已高亮'+(f'（物理页 {row["pdf_page"]}）' if label=='PDF' else f'（源文行 {row["line"]}）')
                else:
                    reasons={'not_found':'未找到唯一的精确匹配','ambiguous':'存在多个匹配位置','skipped_short':'片段过短，无法安全定位','invalid_geometry':'无法建立可靠高亮位置','unsafe_markup':'含表格、公式或其他不安全的 Markdown 结构','not_unique':'原文块内未能唯一逐字定位','overlap':'与另一处高亮重叠'}
                    desc='未标注：'+reasons.get(row['status'],row.get('reason',row['status']))
                out.append(f'- {label}：{desc}')
            out.append('')
    out += [END,'']; path.write_text(body+'\n\n'+'\n'.join(out),encoding='utf8')
    print(json.dumps({'pass':True,'evidence':len(ids)},ensure_ascii=False))

if __name__=='__main__': main()
