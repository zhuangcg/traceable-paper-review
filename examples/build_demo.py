"""Rebuild the entirely fictional public example with real annotation scripts."""
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
import pymupdf

REPO=Path(__file__).resolve().parents[1]
S=REPO/'scripts'
BASE=REPO/'examples'
INPUT=BASE/'input'
OUT=BASE/'output'
SECTIONS=[
 ('Background',[
  'This document is an entirely fictional demonstration, not a scientific study.',
  'The example asks whether libraries with longer opening hours also record more visits.',
  'A relationship between opening hours and visits would not establish causation.']),
 ('Methods',[
  'The fictional dataset contains twelve libraries observed during one illustrative week.',
  'Six libraries are placed in a shorter-hours group and six in a longer-hours group.',
  'The method compares the average number of visits between the two groups.']),
 ('Results',[
  'The shorter-hours group has an illustrative mean of 120 visits per library.',
  'The longer-hours group has an illustrative mean of 180 visits per library.',
  'The difference between the two illustrative group means is 60 visits.']),
 ('Discussion',[
  'Library size and neighborhood population could explain part of the observed difference.',
  'The example does not measure uncertainty or test the effects of changing opening hours.'])]
EXTRA='This Markdown-only sentence deliberately demonstrates a missing PDF match.'
CLAIMS=[
 '本材料纯属虚构演示，不是科学研究。','演示问题是开放时间较长的图书馆是否也有更多到访。','两项指标存在关系并不证明因果。',
 '虚构数据包含一周内十二家图书馆。','将十二家图书馆分为六家与六家的两组。','方法是比较两组每馆到访次数的均值。',
 '短开放时间组的示意均值为每馆120次。','长开放时间组的示意均值为每馆180次。','两组示意均值之差为60次。',
 '图书馆规模和周边人口可能解释部分差异。','演示没有测量不确定性，也没有测试延长开放时间的效果。',
 '此句故意仅存在于 Markdown，用于演示 PDF 漏标提示。']
def run(name,*args):
    p=subprocess.run([sys.executable,str(S/name),*map(str,args)],capture_output=True,text=True,encoding='utf8')
    if p.returncode: raise RuntimeError(p.stdout+p.stderr)
    print(p.stdout)
def dump(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    if OUT.exists(): raise SystemExit('Example output exists; choose a fresh checkout to rebuild.')
    INPUT.mkdir(parents=True,exist_ok=True)
    source=INPUT/'paper.md'
    source.write_text('## Library hours and visits — FICTIONAL DEMO\n\n'+
      '\n\n'.join('### '+name+'\n\n'+'\n\n'.join(lines) for name,lines in SECTIONS)+
      '\n\n'+EXTRA+'\n',encoding='utf8')
    pdf=pymupdf.open()
    for page_number,group in enumerate((SECTIONS[:2],SECTIONS[2:]),1):
        page=pdf.new_page(width=595,height=842)
        page.insert_text((48,45),'TRACEABLE PAPER REVIEW / FICTIONAL DEMO',fontname='helv',fontsize=12)
        y=82
        for heading,paragraphs in group:
            page.insert_text((48,y),heading.upper(),fontname='hebo',fontsize=15); y+=29
            for paragraph in paragraphs:
                for line in textwrap.wrap(paragraph,width=72,break_long_words=False):
                    page.insert_text((48,y),line,fontname='helv',fontsize=12); y+=18
                y+=16
            y+=18
        page.insert_text((48,800),'Synthetic content. No real research findings. / '+str(page_number),fontsize=10)
    pdf.set_metadata({'title':'Library hours and visits — FICTIONAL DEMO','author':'Traceable Paper Review contributors'})
    pdf.save(INPUT/'paper.pdf'); pdf.close()
    run('prepare_source.py',source,'--out',OUT)
    blocks=json.loads((OUT/'source_index.json').read_text(encoding='utf8'))['blocks']
    sentences=[s for _,lines in SECTIONS for s in lines]+[EXTRA]
    types=['background','problem','theory','data','method','method','result','result','result','discussion','limitation','other']
    evidence=[]
    for n,(quote,claim,kind) in enumerate(zip(sentences,CLAIMS,types),1):
        b=next(b for b in blocks if quote in b['text'])
        evidence.append({'id':f'E{n:04d}','claim':claim,'claim_type':kind,'status':'verified_direct',
          'supports':[{'block_id':b['id'],'quote':quote}],
          'semantic_check':'仅核实虚构演示文本的表述；不是现实世界的科学证据。','reader_note':False})
    dump(OUT/'evidence.json',evidence)
    coverage=json.loads((OUT/'coverage.json').read_text(encoding='utf8'))
    for section in coverage:
        run('read_sections.py',OUT,'--section',section['id'],'--page',0)
        section.update(status='reviewed',summary='检查完整的自建演示段落',review_notes='演示文本全文已明确给出，不涉及外部实证。')
    dump(OUT/'coverage.json',coverage)
    tags={key:{'tag':'未涉及','status':'absent','reason':'演示不采用该类理论或政策','evidence_ids':[]} for key in ['phenomenon','theory','method','data','policy']}
    for key,tag,eid in [('phenomenon','图书馆到访差异','E0002'),('method','组均值比较','E0006'),('data','虚构到访记录','E0004')]:
        tags[key]={'tag':tag,'status':'grounded','reason':'自建示例明确描述','evidence_ids':[eid]}
    dump(OUT/'tags.json',tags)
    labels=['提出开放时间与到访量是否相关的问题','构造十二家图书馆并分为两组','比较两组平均到访次数及其差值','列出规模与人口等替代解释并限制因果推断']
    ids=['E0002','E0005','E0009','E0010']
    dump(OUT/'storyline.json',{'status':'coherent','rationale':'演示研究步骤，不表示因果。',
      'nodes':[{'id':f'N{i}','label':label,'evidence_ids':[eid]} for i,(label,eid) in enumerate(zip(labels,ids),1)],
      'edges':[{'from':f'N{i}','to':f'N{i+1}','relation':'研究步骤'} for i in range(1,4)],'breaks':[]})
    note="""## 图书馆开放时间与到访记录：纯演示

> 全部文字和数字均为自建虚构材料，用来展示流程，不代表真实研究。

## 内容提要

演示比较开放时间较短与较长的两组图书馆，示意均值分别为120和180次[E0002](#e0002)[E0007](#e0007)[E0008](#e0008)。这些数字来自演示设定，不能推出延长开放时间会增加到访[E0001](#e0001)[E0003](#e0003)。

## 研究背景与研究问题

问题是两类图书馆的到访次数是否不同，而不是检验某项开放时间政策的效果[E0002](#e0002)[E0011](#e0011)。

## 理论基础与关键概念

本演示未采用正式理论框架。相关关系与因果关系需要区分[E0003](#e0003)。

## 研究区域、数据与指标

示例没有真实研究区。虚构记录覆盖十二家图书馆的一周，两组各六家[E0004](#e0004)[E0005](#e0005)。

## 研究设计与方法

可以把方法理解为先算每组“每家馆平均来了多少次”，再比较两个平均数。输入是两组虚构到访记录，操作是计算组均值，输出是均值与差值[E0006](#e0006)[E0009](#e0009)。

## 研究结果

短开放时间组均值为120，长开放时间组为180；差值是60次[E0007](#e0007)[E0008](#e0008)[E0009](#e0009)。这只是演示组间差异，未衡量抽样不确定性[E0011](#e0011)。

## 讨论与解释

馆舍规模与周边人口可能同时改变到访量，因此不能仅由均值差推出开放时间的因果效果[E0010](#e0010)[E0003](#e0003)。

## 核心研究主线

```mermaid
flowchart TD
 N1["提出开放时间与到访量是否相关的问题"] -->|建立示意数据| N2["构造十二家图书馆并分为两组"]
 N2 -->|比较组均值| N3["计算两组平均到访次数及其差值"]
 N3 -->|检查解释边界| N4["列出规模和人口等替代解释并限制因果推断"]
```

N1 [E0002](#e0002)；N2 [E0005](#e0005)；N3 [E0009](#e0009)；N4 [E0010](#e0010)。箭头表示演示步骤。

## 五维关键词标签

- **现象**：#phenomenon/图书馆到访差异 [E0002](#e0002)
- **理论**：未涉及
- **方法**：#method/组均值比较 [E0006](#e0006)
- **数据**：#data/虚构到访记录 [E0004](#e0004)
- **政策**：未涉及

## 待核验事项与后续研究

最后一条故意只放进 Markdown，因此应在 PDF 显示未匹配，并在笔记里保留说明[E0012](#e0012)。

## 阅读覆盖与证据质量

全文是可直接检查的自建演示；PDF 为两页文字层文档。成功定位不代表现实世界的结论有效。
"""
    (OUT/'notes.md').write_text(note,encoding='utf8')
    for command,args in [('verify_evidence.py',[]),('annotate_markdown.py',[]),('annotate_pdf.py',[INPUT/'paper.pdf']),('finalize_notes.py',[]),('audit_note.py',[])]:
        run(command,OUT,*args)
    run('finish_review.py',OUT,'--paper-id','DEMO-001','--clean')
    # Public fixtures use a portable source reference, not the builder's private path.
    review=json.loads((OUT/'review.json').read_text(encoding='utf8')); review['paper']['source']='../input/paper.md'; dump(OUT/'review.json',review)

if __name__=='__main__': main()
