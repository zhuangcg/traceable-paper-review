"""Validate annotation reports against current evidence, source and outputs."""
import json
from pathlib import Path
from annotate_pdf import sha256

def load_reports(root, items, manifest):
    rows, available = {}, set()
    for name, label in [('annotation_report.json','PDF'),('markdown_annotation_report.json','Markdown')]:
        path = root / name
        if not path.exists(): continue
        report = json.loads(path.read_text(encoding='utf8'))
        if report.get('source_markdown_sha256',report.get('source_sha256')) != manifest['sha256']:
            raise ValueError(label+' annotation report belongs to a different source')
        output = root / Path(report.get('output_pdf','paper.annotated.pdf')) if label=='PDF' else root/'paper.annotated.md'
        if not output.is_file() or report.get('output_sha256') != sha256(output):
            raise ValueError(label+' annotated output missing or changed')
        available.add(label)
        for row in report.get('annotations',[]):
            eid, n = row.get('evidence_id'), row.get('support')
            item = items.get(eid)
            if not item or not isinstance(n,int) or not 1 <= n <= len(item.get('supports',[])) or row.get('quote') != item['supports'][n-1]['quote']:
                raise ValueError(label+' annotation report is stale for current evidence')
            key = (label,eid,n)
            if key in rows: raise ValueError('Duplicate annotation record: '+str(key))
            if row.get('status') not in {'matched','not_found','ambiguous','skipped_short','invalid_geometry','unsafe_markup','not_unique','overlap'}:
                raise ValueError('Invalid annotation status: '+str(key))
            if row['status']=='matched':
                position=row.get('pdf_page' if label=='PDF' else 'line')
                if type(position) is not int or position < 1:
                    raise ValueError('Invalid matched annotation position: '+str(key))
            rows[key] = row
    return rows, available

def state(rows, available, label, eid, number):
    return rows.get((label,eid,number), {'status':'not_recorded' if label in available else 'not_generated',
                                      'reason':'报告未包含该片段' if label in available else '未执行标注'})
