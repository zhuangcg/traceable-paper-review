import json, subprocess, sys, tempfile
from pathlib import Path
S = Path(__file__).resolve().parents[1] / 'scripts'
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp); src = root / 'paper.md'; work = root / 'out'
    sentence = 'This is a unique sentence about a useful result.'
    table_sentence = 'This table text must not receive inserted Markdown links.'
    src.write_text('# Example\n\n' + sentence + '\n\n<table><tr><td>'+table_sentence+'</td></tr></table>\n', encoding='utf8')
    subprocess.run([sys.executable,str(S/'prepare_source.py'),str(src),'--out',str(work)],check=True,capture_output=True)
    blocks=json.loads((work/'source_index.json').read_text(encoding='utf8'))['blocks']
    bid=next(b['id'] for b in blocks if sentence in b['text'])
    table_bid=next(b['id'] for b in blocks if table_sentence in b['text'])
    (work/'evidence.json').write_text(json.dumps([{'id':'E0001','claim':'结果','claim_type':'result','status':'verified_direct','supports':[{'block_id':bid,'quote':sentence}], 'semantic_check':'该句直接支持结果。'}, {'id':'E0002','claim':'表格','claim_type':'data','status':'verified_direct','supports':[{'block_id':table_bid,'quote':table_sentence}],'semantic_check':'表格数据。'}],ensure_ascii=False),encoding='utf8')
    subprocess.run([sys.executable,str(S/'annotate_markdown.py'),str(work)],check=True,capture_output=True)
    result=(work/'paper.annotated.md').read_text(encoding='utf8')
    assert '<mark style="background-color:#ffcf78">'+sentence+'</mark>' in result
    assert sentence in src.read_text(encoding='utf8') and '<mark' not in src.read_text(encoding='utf8')
    report=json.loads((work/'markdown_annotation_report.json').read_text(encoding='utf8'))
    assert report['annotations'][0]['status']=='matched'
    assert report['annotations'][1]['status']=='unsafe_markup' and '<td><mark' not in result
    print('PASS')
