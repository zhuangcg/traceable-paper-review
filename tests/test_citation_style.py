import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from citation_style import normalize_citations, misplaced_lines

original='观察关系。[^E0001][^E0004]\nA result. [E0002](#e0002)\n'
expected='观察关系[^E0001][^E0004]。\nA result[E0002](#e0002).\n'
assert normalize_citations(original)==expected
assert normalize_citations(expected)==expected and not list(misplaced_lines(expected))
protected='> Original quote.[^E0001]\n```text\nExample.[^E0001]\n```\n'
assert normalize_citations(protected)==protected
print('PASS: citations precede punctuation; original quotations and code remain unchanged')
