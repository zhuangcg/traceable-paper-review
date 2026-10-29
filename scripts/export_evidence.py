#!/usr/bin/env python3
"""Export one lossless CSV row per claim support for database ingestion."""
import argparse
import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path
from verify_evidence import check
from annotation_state import load_reports, state
from annotate_pdf import color_for, label_for

FIELDS = ['schema_version','paper_id','source_version_id','evidence_uid','evidence_id','support_uid','support_index',
          'claim','claim_type','claim_group','verification_status','semantic_check','reader_note',
          'quote','block_id','section','line_start','line_end','source_md','source_sha256',
          'pdf_annotation_status','pdf_annotation_reason','pdf_physical_page',
          'markdown_annotation_status','markdown_annotation_reason','highlight_color']

def export(root, paper_id=None, overwrite=False):
    root=Path(root).resolve(); target=root/'evidence.csv'
    result=check(root,write=False)
    if not result['pass']: raise ValueError(str(result['errors']))
    if target.exists() and not overwrite: raise ValueError('evidence.csv exists; use --overwrite explicitly')
    manifest=json.loads((root/'source_manifest.json').read_text(encoding='utf8'))
    entries=json.loads((root/'evidence.json').read_text(encoding='utf8'))
    items={e['id']:e for e in entries}
    blocks={b['id']:b for b in json.loads((root/'source_index.json').read_text(encoding='utf8'))['blocks']}
    reports, available=load_reports(root,items,manifest)
    version='sha256:'+manifest['sha256']; paper_id=paper_id or version
    rows=[]
    for e in entries:
        eid=e['id']; uid=version+':'+eid
        seen=set()
        for n,s in enumerate(e.get('supports',[]) or [None],1):
            b=blocks[s['block_id']] if s else {}
            signature=json.dumps([s['block_id'],s['quote']],ensure_ascii=False) if s else ''
            if s and signature in seen: raise ValueError(eid+' contains duplicate supports')
            seen.add(signature)
            pdf=state(reports,available,'PDF',eid,n) if s else {'status':'not_applicable','reason':'无证据片段'}
            md=state(reports,available,'Markdown',eid,n) if s else {'status':'not_applicable','reason':'无证据片段'}
            row=dict(schema_version='1',paper_id=paper_id,source_version_id=version,evidence_uid=uid,
                     evidence_id=eid,support_uid=uid+':'+hashlib.sha256(signature.encode('utf8')).hexdigest() if s else '',
                     support_index=n if s else '',claim=e['claim'],claim_type=e.get('claim_type','other'),
                     claim_group=label_for(e.get('claim_type')),verification_status=e['status'],
                     semantic_check=e['semantic_check'],reader_note=str(bool(e.get('reader_note',False))).lower(),
                     quote=s['quote'] if s else '',block_id=s['block_id'] if s else '',
                     section=b.get('section',''),line_start=b.get('start_line',''),line_end=b.get('end_line',''),
                     source_md=manifest['source_md'],source_sha256=manifest['sha256'],
                     pdf_annotation_status=pdf['status'],pdf_annotation_reason=pdf.get('reason',''),
                     pdf_physical_page=pdf.get('pdf_page',''),markdown_annotation_status=md['status'],
                     markdown_annotation_reason=md.get('reason',''),highlight_color=color_for(e.get('claim_type')))
            rows.append(row)
    temp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8-sig',newline='',dir=root,delete=False) as stream:
            temp=Path(stream.name); writer=csv.DictWriter(stream,fieldnames=FIELDS,quoting=csv.QUOTE_ALL)
            writer.writeheader(); writer.writerows(rows)
        os.replace(temp,target)
    finally:
        if temp and temp.exists(): temp.unlink()
    return {'output':str(target),'claims':len(entries),'rows':len(rows),'source_version_id':version}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('workdir',type=Path)
    p.add_argument('--paper-id',help='Stable library ID, e.g. DEMO-001; defaults to source version hash')
    p.add_argument('--overwrite',action='store_true')
    args=p.parse_args()
    try: print(json.dumps(export(args.workdir,args.paper_id,args.overwrite),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError) as exc: p.error(str(exc))

if __name__=='__main__': main()
