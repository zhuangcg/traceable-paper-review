## GitHub release preparation

Repository: https://github.com/zhuangcg/traceable-paper-review

Suggested description:

结论有出处，论文有标注。A Codex / Claude Code skill for evidence-linked paper notes and ready-to-read annotated papers.

Suggested topics: agent-skills, codex, claude-code, academic-reading, pdf-annotation, evidence, markdown, research-tools.

## Before publishing

- Clone examples, installation prompts and the checks badge use the actual repository URL.
- Use README.md as the Chinese landing page; README.en.md and both skill editions are linked.
- The logo and notebook hero are illustrations; the case image comes from the original fictional demo.
- The included PDFs contain only original synthetic material. No personal paper collection or local backups belong in the repository.
- Run python tools/run_tests.py and python tools/check_release.py.
- Publish source under MIT; runtime libraries keep their own terms.

## Verification boundaries

Local script checks, the synthetic two-page example, citation placement, annotation colors/comments, cleanup and public-file scans were exercised.
The GitHub Actions workflow is provided but has not run remotely.
Codex and Claude Code installation paths were checked against official documentation; a fresh client installation from a public GitHub URL has not been exercised.
MinerU installation, OCR workflows and Zotero import were not exercised.
The synthetic notes are predefined in their builder; they are not an independent model-quality benchmark.
