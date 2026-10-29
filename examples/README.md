## 公开演示 / Public example

这是完全自建的虚构材料，不是研究论文，也不包含真实研究结论。全部句子和数字只用于展示功能。

This is entirely fictional material, not a research paper or real scientific evidence.

- [输入 Markdown / Input text](input/paper.md)
- [输入 PDF / Input PDF](input/paper.pdf)
- [笔记 / Notes](output/notes.md)
- [标注 PDF / Annotated PDF](output/paper.annotated.pdf)
- [标注 Markdown / Annotated Markdown](output/paper.annotated.md)
- [结构化证据 / Structured evidence](output/review.json)

实际脚本结果 / Actual script results: 12 evidence excerpts; PDF 11 matched, 1 deliberately absent; Markdown 12 highlighted.
The missing passage is E0012. Its failure appears explicitly in the note and JSON.

图文中的中文总结由演示构建脚本预先编写，用于可复现的功能展示；该案例不是独立 AI 精读能力评测。
Chinese notes are predefined in the builder for reproducible functionality checks, not an independent evaluation of an AI reader.

重建时使用一个不含 examples/output 的新副本，安装 PyMuPDF，运行 `python examples/build_demo.py`。
To rebuild, use a fresh copy without examples/output, install PyMuPDF, and run that command.
The public JSON source path is normalized to a relative path after export for portability.
