import json
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_source import parse
from finish_review import finish
from audit_note import REQUIRED
from verify_evidence import check
S=Path(__file__).resolve().parents[1]/'scripts'

def fixture(root,name='paper.md'):
    src=root/name; sentence='This complete sentence reports a carefully qualified observed result.'
    src.write_text('## Results\n\n'+sentence+'\n',encoding='utf8')
    manifest,index,coverage,visuals=parse(src)
    bid=next(b['id'] for b in index['blocks'] if sentence in b['text'])
    evidence=[{'id':'E0001','claim':'观察结果','claim_type':'result','status':'verified_direct','semantic_check':'只表示观察关联。','supports':[{'quote':sentence,'block_id':bid}]}]
    tags={x:{'tag':'未涉及','status':'absent','reason':'测试材料没有该维度','evidence_ids':[]} for x in ('phenomenon','theory','method','data','policy')}
    for sec in coverage: sec.update(status='reviewed',summary='完整检查短段落',review_notes='确认观察结果')
    for n,x in [('source_manifest.json',manifest),('source_index.json',index),('coverage.json',coverage),('visuals.json',visuals),('evidence.json',evidence),('tags.json',tags),('storyline.json',{'status':'not_supported','rationale':'只有一句测试文本','breaks':['无完整研究设计']})]:
        (root/n).write_text(json.dumps(x,ensure_ascii=False),encoding='utf8')
    for sec in coverage: subprocess.run([sys.executable,str(S/'read_sections.py'),str(root),'--section',sec['id']],capture_output=True,check=True)
    checked=check(root,write=False,include_map=True); assert checked['pass']
    (root/'citation_map.json').write_text(json.dumps(checked['citation_map']),encoding='utf8')
    note='## Test\n\n'+ '\n\n'.join('## '+h+'\n\n'+('观察结果。[E0001](#e0001)' if h=='TL;DR' else '\n'.join('- **'+x+'**：未涉及' for x in ('现象','理论','方法','数据','政策')) if h=='五维关键词标签' else '') for h in REQUIRED)
    (root/'notes.md').write_text(note,encoding='utf8')
    subprocess.run([sys.executable,str(S/'finalize_notes.py'),str(root)],capture_output=True,check=True)
    return src

with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
    root=Path(temp); src=fixture(root); original=src.read_bytes()
    (root/'user.txt').write_text('Keep this unrelated file',encoding='utf8')
    saved=(root/'notes.md').read_text(encoding='utf8')
    (root/'notes.md').write_text('Invalid incomplete note',encoding='utf8')
    try: finish(root,clean=True)
    except ValueError as exc: assert 'audit failed' in str(exc)
    else: raise AssertionError('Must refuse cleanup before successful audit')
    assert (root/'evidence.json').is_file() and not (root/'review.json').exists()
    (root/'notes.md').write_text(saved,encoding='utf8')
    finish(root,'P-test',True)
    review=json.loads((root/'review.json').read_text(encoding='utf8'))
    assert review['paper']['id']=='P-test' and review['evidence'][0]['supports'][0]['pdf']['status']=='not_generated'
    assert review['evidence'][0]['supports'][0]['quote'] in original.decode('utf8')
    assert not (root/'evidence.json').exists() and (root/'user.txt').is_file() and src.read_bytes()==original
with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
    root=Path(temp); src=fixture(root,'evidence.md')
    try: finish(root,clean=True)
    except ValueError as exc: assert 'source or linked file' in str(exc)
    else: raise AssertionError('Cleanup must not delete original source')
    assert src.is_file()
print('PASS: lossless final evidence, audit gate, source and unknown-file protection, cleanup')
