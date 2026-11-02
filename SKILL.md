---
name: traceable-paper-review
description: Use when asked to read or review a paper, create evidence-linked paper notes, or highlight and annotate a PDF or Markdown paper. 适用于精读论文、整理论文笔记、标注 PDF 或 Markdown、追溯原文证据。
metadata:
  version: "1.6.0"
  language: en
---

## Quick path and capabilities

1. Resolve `SKILL_DIR` to the absolute directory containing this SKILL.md, not the current working directory. Resolve `PYTHON` to the current Python executable. Run `python "$SKILL_DIR/scripts/check_env.py" <workdir>` once; use `--check-network` only when a cloud or install decision needs it. Network reachability is not proof that pip or the API works.
2. Python 3.9+ and usable Markdown support notes, evidence and Markdown highlights. PDF highlighting additionally requires PyMuPDF and an accessible text layer. PDF-to-Markdown requires a separate converter; PyMuPDF alone is not a full parser.
3. Collect only unanswered choices together: requested outputs, copy versus source replacement, and local versus cloud conversion if needed. Respect choices already given. Defaults for unspecified choices are Markdown annotation when available, separate copies and local processing. Do not downgrade an explicitly requested PDF output silently. A cloud upload needs explicit consent for the specific PDF; no reply is not consent. Explain blocked capabilities and continue independent work.
4. When PDF highlighting is requested, use the preflight interpreter if PyMuPDF is available. Otherwise create/reuse `<workdir>/.venv`, then run its Python with `-m pip install -r "$SKILL_DIR/requirements-pdf.txt"`. Retry this same install at most once if needed. Never install the unrelated `fitz` package, change channels or modify the system Python. If unavailable, proceed with notes and Markdown, marking PDF highlighting unavailable in each support and the final report. Do not present PDF-only input as fully read without an actual conversion.
5. Read [references/execution-options.md](references/execution-options.md) for context exhaustion and source replacement safeguards. Before resuming, checkpoint progress on disk.
6. Prepare with `run_pipeline.py prepare`; read all sections and build evidence; run `verify`, write notes, run `annotate`, inspect results, then `finish`. See Commands for absolute script paths. These commands do not replace reading or scientific review.
7. Stop after two consecutive failures of the same unchanged command. Repair an audit issue at most three times, then report what failed and preserve work. Never retry an authorization denial through another route.

## Purpose and source selection

Review one clearly identified version of one paper. Default to Chinese notes, retaining precise original terminology. [SKILL.zh-CN.md](SKILL.zh-CN.md) is the equivalent Chinese edition, not a different workflow.

Use existing Markdown as authoritative text; preserve original lines and images. Do not rewrite source files during analysis or reconvert a PDF when usable Markdown exists. Source replacement is permitted only under the explicit annotation choice below. For requested annotations, use the corresponding PDF's existing text layer for positioning. Inspect same-version figures visually when needed; never silently combine versions.

Identify text, images, supplements and existing notes first. Use a separate work directory and preserve user work. Never substitute an abstract or search snippets for full reading, or invent quotes, numbers, pages, figures, theories or causal effects.

When context is close to exhaustion, checkpoint and follow [execution-options.md](references/execution-options.md).

## PDF preparation and dependencies

Recommend [MinerU's official repository](https://github.com/opendatalab/MinerU) for converting complex PDFs to Markdown. Keep its image folder and inspect formulas and captions. MinerU is optional preprocessing; follow its own model, hardware and installation requirements. Do not upload private papers to third-party services without permission.

With PDF-only input, use an available reader/converter once, record text origin and inspect the conversion. Report missing capabilities precisely. Core scripts use Python 3.9+ standard library. PDF highlighting additionally requires PyMuPDF and readable PDF text.

For PDF-only input, offer local processing or the optional MinerU cloud API. Use cloud only after the user explicitly consents to uploading that particular PDF; setting a token alone is not consent. Read the token from `MINERU_TOKEN` without displaying it. Run `python "$SKILL_DIR/scripts/mineru_cloud.py" <paper.pdf> --out <new-conversion-directory> --confirm-upload`. Feed the returned `full.md` and its image directory into `prepare_source.py`; retain the original PDF and record its hash and conversion provenance in the notes. Inspect formulas, tables, images and missing pages. On errors report the limitation; do not silently upload or substitute an abstract. The API and quota can change; consult https://mineru.net/apiManage/docs.

For scanned PDFs, use OCR and verify it; PyMuPDF alone does not guarantee readable text.

## Full reading and evidence

1. Run `python "$SKILL_DIR/scripts/prepare_source.py" <paper.md> --out <workdir>` to index immutable source hashes, lines, sections and images. Follow references/reading-protocol.md. List sections with `python "$SKILL_DIR/scripts/read_sections.py" <workdir> --list`, then read every page of all substantive sections. Truncated previews do not count. Logs prove output, not comprehension. Fill coverage.json with actual checks; identify missing supplements and thumbnail-only inspections.
2. Build evidence.json using references/evidence-contract.md. Bind each factual claim to contiguous original excerpts and block IDs, separating distinct passages into supports. Check samples, units, denominators, signs, direction, comparisons, exceptions and causal qualifications. Preserve conflicts. Run `python "$SKILL_DIR/scripts/verify_evidence.py" <workdir>`; exact excerpts do not establish semantic support.
3. Write notes.md using canonical `[E0001](#e0001)` links. References go BEFORE final punctuation, including adjacent multiple references: `观察到相关关系[E0001](#e0001)。` / `An association was observed[E0001](#e0001).` Do not write `结论。[E0001](#e0001)`. finalize_notes.py repairs old placement; audit_note.py rejects remaining violations.
4. finalize_notes.py creates ordinary same-file evidence headings containing original quotes, lines, interpretations and each support's annotation status. Readers must not need another file to see original words. Heading anchors vary by viewer; printed evidence IDs remain searchable.

## Explain clearly

Follow assets/notes-template.md. Cover the question, theory, data, variables, methods, results, robustness, discussion and limitations in proportion to the paper. The opening summary accepts “内容提要” or “TL;DR”; other standard labels remain Chinese as shown in the template.

For each complex method and key result, explain its purpose, inputs, operation, output and interpretation in ordinary language first. Then provide precise terms, formulas, settings and limits. Label illustrative examples; invented example numbers are not paper results. Distinguish author findings, author speculation and reader analysis.

Every Mermaid node must be a concrete, independently understandable sentence naming an object, operation or observation. Do not use vague “Data → Method → Results” labels. Label arrows with actual research relations and cite each node below the figure. Unsupported connections must be identified as gaps, not invented causal links. Follow references/storyline-contract.md for storyline.json.

Keep five tag slots: phenomenon, theory, method, data, policy. Display every grounded tag with a # prefix and its namespace: #phenomenon/, #theory/, #method/, #data/, #policy/, for example #method/组均值比较. Do not display bare keywords. At most one grounded tag each; use “未涉及” for absence without creating a hashtag for it. Follow references/tag-ontology.md.

## Color annotations and verification

Map claim_type consistently: blue background/problem/theory/definitions; green data/methods; orange results; purple discussion/limitations/conclusions; gray other. Color is not evidence quality; retain textual categories and IDs.

- Run `python "$SKILL_DIR/scripts/annotate_markdown.py" <workdir>` for a separate paper.annotated.md, copied referenced local images and per-support report. Insert highlights only for exact, unique, structurally safe spans. Skip unsafe HTML, formulas, multiline or overlapping text and record reasons. Colors require HTML/style support; IDs and evidence entries are the fallback.
- For requested PDF annotations, run `python "$SKILL_DIR/scripts/annotate_pdf.py" <workdir> <source.pdf>` after preparing PyMuPDF. Require MD-verified excerpts and a unique normalized same-page match. Preserve numbers, punctuation, signs and inequalities. Do not guess ambiguous/missing positions. Create standard colored highlights with Chinese comments in a separate PDF; physical pages are not printed page labels.
- Run `python "$SKILL_DIR/scripts/finalize_notes.py" <workdir>` after annotation. Every support must independently show success, failure with reason, or not executed for PDF and Markdown. Partial success is not complete annotation.
- Run `python "$SKILL_DIR/scripts/audit_note.py" <workdir>`. Recheck meaning and quantities and visually inspect every annotated page for placement, color, comments and column errors. Report missing materials and matched/unmatched counts. Mechanical PASS cannot establish scientific accuracy.

## Compact delivery and cleanup

For source replacement, follow [execution-options.md](references/execution-options.md); default to separate copies.

Deliver notes.md, review.json, requested annotated PDF/Markdown and its referenced images. Do not deliver a pile of indexes, logs, duplicate ledgers, CSV and schema notes.

After semantic and visual checks, run `python "$SKILL_DIR/scripts/finish_review.py" <workdir> --paper-id <library-id> --clean`. It reruns the audit, validates evidence and annotation reports, writes/rereads review.json, then removes only its fixed list of generated sidecars. Preserve sources, notes, annotations, images and unknown files. Confirm allowlisted files in an existing directory are generated artifacts before cleanup. Never expand deletion to other files/directories or clean after a failed audit or unfinished review.

review.json stores identity/source hash once and nests multiple supports under each claim. Retain content, type, verification status, boundaries, quotes, source locations and annotation outcomes; omit repeated UIDs, paths, colors and derived labels. See references/delivery-contract.md. Preserve local IDs when reordering; changed source text is a new version.

CSV is optional: export only when explicitly requested, before cleanup, with --keep-csv at finish. A cleaned directory is a final result, not a working ledger; revisions require a fresh work directory from the source paper.

## Commands

Set `SKILL_DIR` to this skill's absolute directory and `PYTHON` to the chosen interpreter; the examples below use `python` for that interpreter. Replace placeholders with actual paths. Run commands only at the corresponding stage, with explicit paths.

```text
python "$SKILL_DIR/scripts/check_env.py" <workdir>
python "$SKILL_DIR/scripts/run_pipeline.py" prepare <workdir> --markdown <paper.md>
python "$SKILL_DIR/scripts/read_sections.py" <workdir> --section SEC001 --page 0
# Read every section and fill coverage, visuals, evidence, tags and storyline.
python "$SKILL_DIR/scripts/run_pipeline.py" verify <workdir>
# Write notes.md; request --pdf <paper.pdf> only when highlighting is requested and available.
python "$SKILL_DIR/scripts/run_pipeline.py" annotate <workdir> [--pdf <paper.pdf>]
# Inspect evidence and annotated pages, then finish; add --keep-csv only when requested.
python "$SKILL_DIR/scripts/run_pipeline.py" finish <workdir> [--paper-id <library-id>]
```

If a combined stage fails, preserve its outputs and inspect the error before resuming; rerunning may encounter existing files. Do not bypass audit or cleanup guards.
