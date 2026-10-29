"""Keep evidence references inside sentence-final punctuation, outside code/quotes."""
import re
REFERENCE = r'(?:\[E\d{4,}\]\(#e\d{4,}\)|\[\^E\d{4,}\])'
AFTER_PUNCTUATION = re.compile(r'([。！？.!?])[ \t]*((?:'+REFERENCE+r'[ \t]*)+)', re.I)

def misplaced_lines(text):
    fenced=False
    for number,line in enumerate(text.splitlines(),1):
        if line.lstrip().startswith(('```','~~~')):
            fenced=not fenced
        elif not fenced and not line.lstrip().startswith('>') and AFTER_PUNCTUATION.search(line):
            yield number

def normalize_citations(text):
    lines=text.splitlines(keepends=True)
    for number in misplaced_lines(text):
        lines[number-1]=AFTER_PUNCTUATION.sub(lambda m:m[2].rstrip()+m[1],lines[number-1])
    return ''.join(lines)
