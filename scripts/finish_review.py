#!/usr/bin/env python3
"""Create a compact final review and optionally remove known generated sidecars."""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from annotation_state import load_reports, state
from verify_evidence import check

SIDECARS = (
    'source_manifest.json','source_index.json','coverage.json','visuals.json',
    'reading_log.json','citation_map.json','evidence.json','evidence.md',
    'tags.json','storyline.json','annotation_report.json',
    'markdown_annotation_report.json','audit_report.json',
    'evidence.csv','evidence-schema.md',
)

def finish(root, paper_id=None, clean=False, keep_csv=False):
    root=Path(root).resolve()
    if (root/'review.json').exists():
        raise ValueError('review.json already exists; use a fresh workdir')
    result=check(root,write=False)
    if not result['pass']: raise ValueError(str(result['errors']))
    manifest=json.loads((root/'source_manifest.json').read_text(encoding='utf8'))
    source=Path(manifest['source_md']).resolve()
    cleanup_names=[name for name in SIDECARS if not (keep_csv and name=='evidence.csv')]
    if clean:
        for name in cleanup_names:
            path=root/name
            if path.is_symlink() or path.resolve()==source:
                raise ValueError('Cleanup would touch a source or linked file: '+name)
        for name in ('notes.md','paper.annotated.md'):
            file=root/name
            if file.exists():
                links=re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',file.read_text(encoding='utf8'))
                if any(link.split('#')[0] in cleanup_names for link in links):
                    raise ValueError(name+' still links to an intermediate file; update links before cleanup')
    script=Path(__file__).with_name('audit_note.py')
    audit_run=subprocess.run([sys.executable,str(script),str(root)],capture_output=True,text=True,encoding='utf8')
    if audit_run.returncode: raise ValueError('Final audit failed: '+audit_run.stdout+audit_run.stderr)
    audit=json.loads((root/'audit_report.json').read_text(encoding='utf8'))
    items=json.loads((root/'evidence.json').read_text(encoding='utf8'))
    blocks={b['id']:b for b in json.loads((root/'source_index.json').read_text(encoding='utf8'))['blocks']}
    reports,available=load_reports(root,{x['id']:x for x in items},manifest)
    evidence=[]
    for item in items:
        entry={'id':item['id'],'type':item['claim_type'],'claim':item['claim'],
               'status':item['status'],'note':item['semantic_check'],'supports':[]}
        if item.get('reader_note'): entry['reader_note']=True
        if item.get('figure_table'): entry['figure_table']=item['figure_table']
        for n,sup in enumerate(item.get('supports',[]),1):
            b=blocks[sup['block_id']]
            support={'quote':sup['quote'],'section':b['section'],'lines':[b['start_line'],b['end_line']]}
            for label,key in [('PDF','pdf'),('Markdown','md')]:
                row=state(reports,available,label,item['id'],n)
                info={'status':row['status']}
                if row.get('reason'): info['reason']=row['reason']
                if label=='PDF' and row['status']=='matched': info['page']=row['pdf_page']
                support[key]=info
            entry['supports'].append(support)
        evidence.append(entry)
    tags=json.loads((root/'tags.json').read_text(encoding='utf8'))
    visuals=json.loads((root/'visuals.json').read_text(encoding='utf8'))
    value={'schema_version':1,
           'paper':{'id':paper_id or manifest['sha256'],'source':manifest['source_md'],'sha256':manifest['sha256']},
           'quality':{'mechanical_audit':'passed','warnings':audit['warnings'],
                      'limits':list(dict.fromkeys(audit['cannot_verify']+[x['reason'] for x in visuals if x.get('reason')]))},
           'tags':{key:x['tag'] if x['status']=='grounded' else None for key,x in tags.items()},
           'evidence':evidence}
    target=root/'review.json'; temp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf8',dir=root,delete=False) as stream:
            temp=Path(stream.name); json.dump(value,stream,ensure_ascii=False,indent=2); stream.write('\n')
        if json.loads(temp.read_text(encoding='utf8'))!=value: raise ValueError('Review serialization failed')
        os.replace(temp,target)
    finally:
        if temp and temp.exists(): temp.unlink()
    removed=[]
    if clean:
        for name in cleanup_names:
            path=root/name
            if path.is_file(): path.unlink(); removed.append(name)
    return {'output':str(target),'claims':len(evidence),
            'supports':sum(len(x['supports']) for x in evidence),'removed':removed}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('workdir',type=Path)
    p.add_argument('--paper-id'); p.add_argument('--clean',action='store_true')
    p.add_argument('--keep-csv',action='store_true',help='Retain CSV only when explicitly requested')
    args=p.parse_args()
    try: print(json.dumps(finish(args.workdir,args.paper_id,args.clean,args.keep_csv),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError) as exc: p.error(str(exc))

if __name__=='__main__': main()
