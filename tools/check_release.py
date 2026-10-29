"""Check the public fixture, local links and accidental private paths."""
import hashlib
import json
import re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
errors=[]
private=re.compile(r'(?i)[A-Z]:[\\/](?:Users|PaperManage|MySkill)[\\/]|[A-Z]:[\\/]PaperManage|P1[0-9]{3}|sk-[A-Za-z0-9]{20,}')
for path in root.rglob('*'):
    if not path.is_file() or '__pycache__' in path.parts or '.git' in path.parts: continue
    if path.suffix in ('.md','.py','.json','.yml','.txt'):
        text=path.read_text(encoding='utf-8-sig')
        if private.search(text): errors.append('Possible private value: '+str(path.relative_to(root)))
        if path.suffix=='.md':
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
                if target.startswith(('http:','https:','#','mailto:')): continue
                relative=target.split('#')[0]
                if relative and not (path.parent/relative).exists(): errors.append('Broken link: '+str(path.relative_to(root))+' -> '+relative)
review=json.loads((root/'examples/output/review.json').read_text(encoding='utf8'))
source=root/'examples/input/paper.md'
assert review['paper']['sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
assert not Path(review['paper']['source']).is_absolute()
assert len(review['evidence'])==12
supports=[s for e in review['evidence'] for s in e['supports']]
assert sum(s['pdf']['status']=='matched' for s in supports)==11
assert sum(s['md']['status']=='matched' for s in supports)==12
assert any(s['pdf']['status']=='not_found' for s in supports)
notes=(root/'examples/output/notes.md').read_text(encoding='utf8')
assert 'E0012' in notes and '未标注' in notes
assert sorted(p.name for p in (root/'examples/output').iterdir())==['notes.md','paper.annotated.md','paper.annotated.pdf','review.json']
if errors: raise SystemExit('\n'.join(errors))
print('PASS: public text scan, local links, portable source, demo counts and compact output')
