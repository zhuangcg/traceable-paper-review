import csv
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_source import parse
from export_evidence import export

with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
    root=Path(folder); src=root/'paper.md'
    q1='A complete result contains commas, "quotes", and 中文.\nA second line belongs to the same block.'
    q2='Another independent source supports this claim.'
    src.write_text('## Results\n\n'+q1+'\n\n'+q2+'\n',encoding='utf8')
    manifest,index,_,_=parse(src)
    for name,value in [('source_manifest.json',manifest),('source_index.json',index)]:
        (root/name).write_text(json.dumps(value),encoding='utf8')
    bid=lambda q: next(b['id'] for b in index['blocks'] if q in b['text'])
    items=[{'id':'E0001','claim':'中文论断, "原样保存"','claim_type':'result','status':'verified_synthesis',
            'supports':[{'block_id':bid(q),'quote':q} for q in (q1,q2)],'semantic_check':'综合两处原句。'},
           {'id':'E0002','claim':'待核验','claim_type':'method','status':'uncertain','supports':[],'semantic_check':'没有足够证据。'}]
    file=root/'evidence.json'; file.write_text(json.dumps(items),encoding='utf8')
    result=export(root,'P-test'); assert result['claims']==2 and result['rows']==3
    with (root/'evidence.csv').open(encoding='utf-8-sig',newline='') as stream: rows=list(csv.DictReader(stream))
    assert rows[0]['quote']==q1 and rows[0]['claim']==items[0]['claim']
    assert rows[0]['evidence_uid']==rows[1]['evidence_uid']
    assert rows[0]['support_uid']!=rows[1]['support_uid']
    assert rows[0]['pdf_annotation_status']=='not_generated'
    assert rows[2]['support_index']=='' and rows[2]['verification_status']=='uncertain'
    assert rows[2]['pdf_annotation_status']=='not_applicable'
    before=(root/'evidence.csv').read_bytes()
    try: export(root)
    except ValueError: pass
    else: raise AssertionError('Must refuse implicit overwrite')
    export(root,'P-test',True); assert before==(root/'evidence.csv').read_bytes()
    items[0]['supports'].append(items[0]['supports'][0])
    file.write_text(json.dumps(items),encoding='utf8')
    try: export(root,'P-test',True)
    except ValueError as ex: assert 'duplicate' in str(ex)
    else: raise AssertionError('Duplicate supports should fail')
    assert before==(root/'evidence.csv').read_bytes()
    src.write_text('Changed source',encoding='utf8')
    try: export(root,'P-test',True)
    except ValueError as ex: assert 'SHA256' in str(ex)
    else: raise AssertionError('Changed source should fail')
    print('PASS: lossless roundtrip, multi-support keys, uncertain claims, missing annotations, determinism, duplicate and stale-source guards')
