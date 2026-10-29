## Traceable Paper Review

[![Skill checks](https://github.com/zhuangcg/traceable-paper-review/actions/workflows/tests.yml/badge.svg)](https://github.com/zhuangcg/traceable-paper-review/actions/workflows/tests.yml)

中文 · [English](README.en.md) · [技能说明（中文）](SKILL.zh-CN.md) · [Skill instructions](SKILL.md)

![研究手账风项目头图](docs/images/hero.png)

**结论有出处，论文有标注。**

既把 AI 的解读连回原文，也替读者完成基础高亮与注释，让你拿到论文就能沿着标注开始读。

这是给 Codex 和 Claude Code 用的论文精读技能，同时照顾两件事：

- **核查解读：** 每条重要论断保留原句与位置，方便检查 AI 有没有读对。
- **带着标注读：** 生成分色高亮和中文批注的论文副本，省去从空白开始手动标注的工夫。

它不会假装所有片段都能标成功；没有匹配到的证据会在笔记里说明。

### 先看效果

![真实运行脚本生成的虚构案例](docs/images/case-study.png)

[公开案例](examples/README.md) 完全自建、纯属虚构，用实际脚本生成：12 条证据中，11 条在 PDF 成功高亮，1 条故意只放进 Markdown，用来展示漏标提示；Markdown 中则标出了全部 12 条。这是该演示的结果，不代表真实论文的通用准确率。

[精读笔记](examples/output/notes.md) · [标注 PDF](examples/output/paper.annotated.pdf) · [标注 Markdown](examples/output/paper.annotated.md) · [汇总 JSON](examples/output/review.json)

### 它能帮你做什么

| 你在意的事 | 技能怎么处理 |
|---|---|
| 方法太绕 | 先讲输入、操作、输出和边界，再给公式与术语 |
| 总结不知道靠不靠谱 | 论断后跟证据编号，同文件保留原句与位置 |
| 流程图像几个空标签 | 每个节点写具体句子，讲清实际步骤 |
| 想回到论文继续看 | 背景蓝、数据与方法绿、结果橙、讨论与局限紫 |
| 有些地方没标出来 | 每个片段都写成功、失败原因或尚未执行 |
| 不想收到十几个中间文件 | 最终只留笔记、一个 JSON 和需要的标注副本 |

引用统一放在标点前，例如：`作者报告了相关关系[E0001](#e0001)。`

### 需要装什么？PDF 怎么准备？

- **精读、证据和检查：** Python 3.9+ 标准库；本项目演示在 Python 3.11 上运行。
- **PDF 高亮：** 还需要 PyMuPDF，以及有可读取文字层的 PDF。它不负责把扫描图片自动变成可靠正文。
- **只有 PDF：** 先准备可读 Markdown。复杂排版、表格和公式，推荐先用 **[MinerU 官方 GitHub：opendatalab/MinerU](https://github.com/opendatalab/MinerU)** 转换，再把 Markdown 连同图片目录交给技能。转换后仍要检查乱码、公式和图注；不能保证转换后所有证据都能高亮。
- **AI Agent 可以安装：** 为完成你要求的处理，Agent 可以在任务目录创建虚拟环境、安装必要依赖，告知安装位置并遵守当前环境权限。未经允许，不应把私人论文提交在线转换服务。

按 [PyMuPDF 官方安装说明](https://pymupdf.readthedocs.io/en/latest/installation.html)，可使用独立环境：

macOS / Linux：

```bash
python -m venv .venv
.venv/bin/python -m pip install PyMuPDF
```

Windows PowerShell：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install PyMuPDF
```

之后用该虚拟环境中的 Python 运行技能脚本。包名是 **PyMuPDF**，不要误装无关的 `fitz` 包。MinerU 有自己的模型和硬件条件，请看它的官方 README，不把它当作一个很小的必装依赖。

### 安装到 Codex / Claude Code

仓库根目录就是完整技能。下面已使用本项目的实际地址；按你使用的工具选择安装位置，不要只下载一个 SKILL.md。

| 工具 | 个人安装（所有项目可用） | 仅当前项目 |
|---|---|---|
| Codex | `~/.agents/skills/traceable-paper-review/` | `.agents/skills/traceable-paper-review/` |
| Claude Code | `~/.claude/skills/traceable-paper-review/` | `.claude/skills/traceable-paper-review/` |

macOS / Linux，按你使用的工具选择一条：

```bash
git clone https://github.com/zhuangcg/traceable-paper-review.git ~/.agents/skills/traceable-paper-review
# Claude Code:
git clone https://github.com/zhuangcg/traceable-paper-review.git ~/.claude/skills/traceable-paper-review
```

Windows PowerShell：

```powershell
git clone https://github.com/zhuangcg/traceable-paper-review.git (Join-Path $env:USERPROFILE '.agents\skills\traceable-paper-review')
# Claude Code:
git clone https://github.com/zhuangcg/traceable-paper-review.git (Join-Path $env:USERPROFILE '.claude\skills\traceable-paper-review')
```

仅项目使用时，把目标换成表中的项目路径。已有同名目录时先检查差异；不要盲目删除旧技能。若工具尚未发现技能，开启新会话再检查。路径依据：[Codex 官方文档](https://learn.chatgpt.com/docs/build-skills)、[Claude Code 官方文档](https://code.claude.com/docs/en/skills)。

### 直接让 AI 帮你装

**给 Codex 的提示词**

```text
请从 https://github.com/zhuangcg/traceable-paper-review.git 安装完整的 traceable-paper-review 技能，
个人安装位置为 ~/.agents/skills/traceable-paper-review。
先阅读 SKILL.md 和脚本；如有同名技能，保留它并核对差异。
检查 Python。需要 PDF 支持时，可以在本次任务目录创建虚拟环境
并安装 PyMuPDF，遵守当前环境权限，告知安装位置。
不要运行远程安装脚本管道，不要索取凭据。
完成后报告路径、版本，以及是否需要开启新会话来发现技能。
```

**给 Claude Code 的提示词**

```text
请从 https://github.com/zhuangcg/traceable-paper-review.git 安装完整的 traceable-paper-review 技能，
个人安装位置为 ~/.claude/skills/traceable-paper-review。
先审查指令和脚本，保留已有安装，检查 Python。
需要时可以在本地虚拟环境安装 PyMuPDF，遵守当前环境权限；
不要改动无关设置。说明如何用 /traceable-paper-review 调用。
若不能实际检查客户端，不要声称已完成客户端识别验证。
```

### 装好之后怎么用

Codex 中可提及 `$traceable-paper-review`；Claude Code 中可用 `/traceable-paper-review`。

```text
请用 traceable-paper-review 全文精读 <论文文件夹>。
优先使用已有 Markdown，并保留图片。
复杂方法和结果先用通俗语言解释，再给出原文证据。
引用放在句末标点前；流程图每个节点用具体完整短句。
生成彩色 PDF、Markdown 副本，并逐项说明没有标注成功的片段。
若依赖缺失，可以在任务级虚拟环境安装必要依赖。
最终结果精简保存到 <新的输出目录>。
```

需要先转 PDF 时，可让 Agent 参考 [MinerU 官方安装与使用说明](https://github.com/opendatalab/MinerU)，先检查设备条件，并在没有额外授权时保持文档在本地处理。


标签在笔记中统一写成 #phenomenon/现象名称、#method/方法名称 等形式；缺席维度不生成标签。

### 最后会留下什么

```text
notes.md
review.json
paper.annotated.pdf       # 要求且条件满足时
paper.annotated.md        # 要求时
<Markdown 实际引用的图片目录>
```

只有汇总写入成功、最终审计通过后，才删除已知的生成中间文件。原论文、未知文件均保留。后续重新改证据或标注时，建立新的工作目录；CSV 仅在明确要求时导出。

**边界也说清楚：** 双栏、分页、公式和转换差异都可能漏标；匹配成功也不代表科学结论成立。Markdown 颜色和跳转依赖阅读器；Zotero 导入尚未验证。技能会把这些限制留在笔记里。

### 开发与许可

`python tools/run_tests.py` 运行测试；PDF 测试需要 PyMuPDF。要重建公开演示，请在不含 examples/output 的新副本中运行 `python examples/build_demo.py`。

代码与自建演示材料采用 [MIT](LICENSE)。依赖遵循各自许可证；项目不附带第三方论文。Logo、头图为 AI 生成，提示词和素材记录见 [ASSETS](docs/ASSETS.md)。本项目与 OpenAI、Anthropic、MinerU 无隶属关系。
