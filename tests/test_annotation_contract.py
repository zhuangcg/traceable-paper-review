import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from annotate_pdf import tokens

def test_symbols():
    for a, b in [('result -0.3', 'result 0.3'), ('rate 5%', 'rate 5'), ('p < 0.05', 'p > 0.05'), ('1.5', '1,5'), ('1/5','15')]:
        assert tokens(a) != tokens(b), (a, b)

def test_roles():
    from annotate_pdf import color_for
    assert len({color_for(x) for x in ('background','method','result','discussion')}) == 4

if __name__ == '__main__':
    test_symbols(); test_roles(); print('PASS')
