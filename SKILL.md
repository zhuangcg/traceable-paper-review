---
name: traceable-paper-review
description: Ground interpretations in original evidence and prepare annotated papers for readers. Read one local paper in full to produce detailed Chinese notes, evidence, a concrete flowchart, and optional colored PDF/Markdown annotations.
metadata:
  version: "1.4.0"
  language: en
---

## Purpose and source selection

Review one clearly identified version of one paper. Default to Chinese notes, retaining precise original terminology. [SKILL.zh-CN.md](SKILL.zh-CN.md) is the equivalent Chinese edition, not a different workflow.

Use existing Markdown as authoritative text; preserve original lines and images. Do not rewrite source files or reconvert a PDF when usable Markdown exists. For requested annotations, use the corresponding PDF's existing text layer for positioning. Inspect same-version figures visually when needed; never silently combine versions.

Identify text, images, supplements and existing notes first. Use a separate work directory and preserve user work. Never substitute an abstract or search snippets for full reading, or invent quotes, numbers, pages, figures, theories or causal effects.

## PDF preparation and dependencies

Recommend [MinerU's official repository](https://github.com/opendatalab/MinerU) for converting complex PDFs to Markdown. Keep its image folder and inspect formulas and captions. MinerU is optional preprocessing; follow its own model, hardware and installation requirements. Do not upload private papers to third-party services without permission.

With PDF-only input, use an available reader/converter once, record text origin and inspect the conversion. Report missing capabilities precisely. Core scripts use Python 3.9+ standard library. PDF highlighting additionally requires PyMuPDF and readable PDF text.

When PDF processing is requested, the agent may install needed dependencies in a task-local virtual environment, state the installation target and obey current permissions. Do not install unrelated dependencies or system-wide software. Scanned PDFs need separate OCR and verification; PyMuPDF alone does not guarantee readable text.

## Full reading and evidence

1. Run `prepare_source.py <paper.md> --out <workdir>` to index immutable source hashes, lines, sections and images. Follow references/reading-protocol.md. List sections with `read_sections.py <workdir> --list`, then read every page of all substantive sections. Truncated previews do not count. Logs prove output, not comprehension. Fill coverage.json with actual checks; identify missing supplements and thumbnail-only inspections.
2. Build evidence.json using references/evidence-contract.md. Bind each factual claim to contiguous original excerpts and block IDs, separating distinct passages into supports. Check samples, units, denominators, signs, direction, comparisons, exceptions and causal qualifications. Preserve conflicts. Run `verify_evidence.py <workdir>`; exact excerpts do not establish semantic support.
3. Write notes.md using canonical `[E0001](#e0001)` links. References go BEFORE final punctuation, including adjacent multiple references: `观察到相关关系[E0001](#e0001)。` / `An association was observed[E0001](#e0001).` Do not write `结论。[E0001](#e0001)`. finalize_notes.py repairs old placement; audit_note.py rejects remaining violations.
4. finalize_notes.py creates ordinary same-file evidence headings containing original quotes, lines, interpretations and each support's annotation status. Readers must not need another file to see original words. Heading anchors vary by viewer; printed evidence IDs remain searchable.

## Explain clearly

Follow assets/notes-template.md. Cover the question, theory, data, variables, methods, results, robustness, discussion and limitations in proportion to the paper. The opening summary accepts “内容提要” or “TL;DR”; other standard labels remain Chinese as shown in the template.

For each complex method and key result, explain its purpose, inputs, operation, output and interpretation in ordinary language first. Then provide precise terms, formulas, settings and limits. Label illustrative examples; invented example numbers are not paper results. Distinguish author findings, author speculation and reader analysis.

Every Mermaid node must be a concrete, independently understandable sentence naming an object, operation or observation. Do not use vague “Data → Method → Results” labels. Label arrows with actual research relations and cite each node below the figure. Unsupported connections must be identified as gaps, not invented causal links. Follow references/storyline-contract.md for storyline.json.

Keep five tag slots: phenomenon, theory, method, data, policy. Display every grounded tag with a # prefix and its namespace: #phenomenon/, #theory/, #method/, #data/, #policy/, for example #method/组均值比较. Do not display bare keywords. At most one grounded tag each; use “未涉及” for absence without creating a hashtag for it. Follow references/tag-ontology.md.

## Color annotations and verification

Map claim_type consistently: blue background/problem/theory/definitions; green data/methods; orange results; purple discussion/limitations/conclusions; gray other. Color is not evidence quality; retain textual categories and IDs.

- Run `annotate_markdown.py <workdir>` for a separate paper.annotated.md, copied referenced local images and per-support report. Insert highlights only for exact, unique, structurally safe spans. Skip unsafe HTML, formulas, multiline or overlapping text and record reasons. Colors require HTML/style support; IDs and evidence entries are the fallback.
- For requested PDF annotations, run `annotate_pdf.py <workdir> <source.pdf>` after preparing PyMuPDF. Require MD-verified excerpts and a unique normalized same-page match. Preserve numbers, punctuation, signs and inequalities. Do not guess ambiguous/missing positions. Create standard colored highlights with Chinese comments in a separate PDF; physical pages are not printed page labels.
- Run `finalize_notes.py <workdir>` after annotation. Every support must independently show success, failure with reason, or not executed for PDF and Markdown. Partial success is not complete annotation.
- Run `audit_note.py <workdir>`. Recheck meaning and quantities and visually inspect every annotated page for placement, color, comments and column errors. Report missing materials and matched/unmatched counts. Mechanical PASS cannot establish scientific accuracy.

## Compact delivery and cleanup

Deliver notes.md, review.json, requested annotated PDF/Markdown and its referenced images. Do not deliver a pile of indexes, logs, duplicate ledgers, CSV and schema notes.

After semantic and visual checks, run `finish_review.py <workdir> --paper-id <library-id> --clean`. It reruns the audit, validates evidence and annotation reports, writes/rereads review.json, then removes only its fixed list of generated sidecars. Preserve sources, notes, annotations, images and unknown files. Confirm allowlisted files in an existing directory are generated artifacts before cleanup. Never expand deletion to other files/directories or clean after a failed audit or unfinished review.

review.json stores identity/source hash once and nests multiple supports under each claim. Retain content, type, verification status, boundaries, quotes, source locations and annotation outcomes; omit repeated UIDs, paths, colors and derived labels. See references/delivery-contract.md. Preserve local IDs when reordering; changed source text is a new version.

CSV is optional: export only when explicitly requested, before cleanup, with --keep-csv at finish. A cleaned directory is a final result, not a working ledger; revisions require a fresh work directory from the source paper.

## Commands

Resolve scripts against the installed skill directory; do not assume it is the shell's current directory.

```text
python scripts/prepare_source.py <paper.md> --out <workdir>
python scripts/read_sections.py <workdir> --list
python scripts/read_sections.py <workdir> --section SEC001 --page 0
# Read every page; fill evidence, coverage, visuals, tags, storyline.
python scripts/verify_evidence.py <workdir>
python scripts/annotate_markdown.py <workdir>
python scripts/annotate_pdf.py <workdir> <paper.pdf>
# Write notes.md with canonical references.
python scripts/finalize_notes.py <workdir>
python scripts/audit_note.py <workdir>
python scripts/finish_review.py <workdir> --paper-id <library-id> --clean
```
