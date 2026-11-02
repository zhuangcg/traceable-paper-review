---
name: traceable-paper-review
description: 对单篇论文做中文全文精读，把解读连回原文证据，并为读者生成基础高亮与中文批注、详细笔记和研究流程图。适用于本地论文 PDF 或现成 MinerU Markdown。
metadata:
  version: "1.6.0"
  language: zh-CN
---

## 最短流程与能力

1. 将本 SKILL.md 所在绝对目录设为 `SKILL_DIR`；用当前 Python 执行 `python "$SKILL_DIR/scripts/check_env.py" <工作目录>` 一次。只有需要判断云端或安装时才可加 `--check-network`；网络可达不保证 pip 或 API 可用。
2. Python 3.9+ 加可用 Markdown 可以生成笔记、证据和 Markdown 标注；PDF 高亮还需 PyMuPDF 和可读文字层。PDF 转 Markdown 需要另外的解析器，不能只靠 PyMuPDF 宣称全文解析成功。
3. 一次收集尚未明确的选项：所需输出、独立副本或覆盖、需要转换时选择本地或云端。已有明确选择不重复问。未说明时默认已有 Markdown 的标注、本地处理和独立副本；不能静默降级用户明确要求的 PDF 标注。特定 PDF 上传云端须明确同意，未回答不代表同意。无法实现时告知并继续独立工作。
4. 要求 PDF 高亮时，预检可用则直接使用当前解释器；否则创建或复用 `<工作目录>/.venv`，通过其中 Python 执行 `-m pip install -r "$SKILL_DIR/requirements-pdf.txt"`。同一安装命令最多重试一次，不安装无关的 `fitz` 包、不切换渠道、不修改系统 Python。仍失败则继续笔记和 Markdown，并在逐条支持和最终报告中写明 PDF 高亮不可用。
5. 上下文接近耗尽时先落盘检查点，再按 [execution-options.md](references/execution-options.md) 处理。原件覆盖遵循该文件；云端上传遵循本说明的安全条件。
6. 依次使用 `run_pipeline.py` 的 prepare、verify、annotate、finish；各阶段之间仍须真正全文阅读、建立证据、撰写笔记和人工复核。完整命令见文末。
7. 同一未变化的命令连续失败两次即停止并报告；审计与修复最多三轮，仍失败则保留工作和失败原因。不得绕过权限拒绝反复尝试。

## 目标和输入

逐篇阅读一个明确版本的论文，交付可追溯、让非本领域读者也能理解的中文笔记。优先使用现有 Markdown 的原始文本，分析过程中不修改源文件、不重复解析 PDF；仅在下方覆盖选项明确授权后替换源文件。用户要求 PDF 标注时，仅使用 PDF 现有文字层定位。必要时可人工查看同版本 PDF 图表并区分原文、图像和读者判断。仅有 PDF 时使用已有工具；无可用能力时说明具体缺失；Agent 可为用户要求的 PDF 处理在任务目录的独立虚拟环境安装必要依赖，告知安装目标并遵守当前环境权限。不要安装系统级软件或无关依赖。版本不一致或有疑问不得混用。

先识别原文、图表和补充材料；已有笔记或源文件不得静默覆盖。使用独立工作目录。绝不把摘要或片段检索冒充全文阅读，不虚构原句、数字、页码、图表、理论或因果关系。

上下文接近耗尽时，先记录检查点并遵循 [execution-options.md](references/execution-options.md)。

## 全文阅读与证据

1. 用 `python "$SKILL_DIR/scripts/prepare_source.py" <paper.md> --out <workdir>` 建立原始行号索引、源哈希、章节和图像清单。根据 `references/reading-protocol.md` 建立论文地图，运行 `python "$SKILL_DIR/scripts/read_sections.py" <workdir> --list`，再逐节逐页读取全部内容；禁止仅展示截断的前几行就记录已阅读。阅读日志只记录脚本输出，不证明模型实际看到或理解。对每节填写 `coverage.json` 中的状态与依据。缺失补充材料明确说明，图片仅做缩略图检查时说明无法核实的细节。
2. 按 `references/evidence-contract.md` 建 `evidence.json`。每条可核实的事实绑定原文连续片段与块 ID，记录语义范围；综合多处分别绑定。定量结果核对单位、样本、分母、方向、符号和例外；图文矛盾分别记录，无法确认不作肯定陈述。运行 `python "$SKILL_DIR/scripts/verify_evidence.py" <workdir>`，校验源哈希和原文摘录。脚本通过不代表语义正确。
3. 写 `notes.md`，用 `citation_map.json` 给出的标准 Markdown 链接 `[E0001](#e0001)` 就近引用；文末由 `finalize_notes.py` 生成对应的 `### E0001` 证据条目，包含原句、行号、中文解释和每个支持片段的 PDF/Markdown 标注状态。普通 Markdown 标题与链接比脚注扩展更通用；不同渲染器对标题锚点规则不完全相同，不支持跳转时仍可按编号直接查找。保留同文件原句，不能只给外部链接。引用必须在句末标点之前，例如“观察到相关关系[E0001](#e0001)。”；多个引用连续放在标点前，不写成“结论。[E0001](#e0001)”。finalize_notes.py 会整理旧格式，audit_note.py 会拒绝仍放错位置的引用。

## PDF 准备与依赖

仅有 PDF 时，提供本地解析或可选 MinerU 云端解析。只有用户明确同意上传该 PDF 后，才执行 `python "$SKILL_DIR/scripts/mineru_cloud.py" <论文.pdf> --out <新的转换目录> --confirm-upload`；设置令牌不等于上传授权。从环境变量 `MINERU_TOKEN` 读取令牌，不展示或写入笔记。将返回的 `full.md` 和图片目录交给 `prepare_source.py`；保留 PDF，在笔记记录 PDF 哈希及转换来源，并检查公式、表格、图片和缺页。失败时说明原因，不静默上传或用摘要代替。接口和额度以 https://mineru.net/apiManage/docs 为准。

优先建议用 [MinerU 官方项目](https://github.com/opendatalab/MinerU) 将复杂 PDF 转为 Markdown，保留图片目录并检查公式和图注。MinerU 是可选前处理工具，其模型、硬件和安装要求以官方说明为准；未经允许不要上传私人论文到第三方服务。只有 PDF 时可使用已有转换能力，不能跳过正文文本的准备和核查。PDF 高亮依赖 PyMuPDF 及可读取的文字层；扫描件需另行 OCR 后核对，不能承诺仅安装 PyMuPDF 就能高亮扫描件。

## 精读写作

按 `assets/notes-template.md` 覆盖问题、理论、数据、变量、方法、结果、稳健性、讨论和局限，逐项引用，不只复述摘要。对于每个复杂方法和重要结果，先用日常语言解释其问题、输入、操作、输出及如何解读，再给精确术语、公式、参数、适用边界。可使用清楚标记为“帮助理解的示意”的小例子；示例数字不是论文结果。明确作者结论、作者推测、读者分析三者区别。按照论文复杂性决定细节，不以篇幅填充替代解释。

研究主线用 Mermaid：每个节点至少一句具体、独立可理解的短句，包含关键对象、操作或观察，例如“将个人停留点连接成轨迹网络，再按空间邻近性划分模块”；不要只写“数据”“方法”“结果”。箭头标明操作或论证关系，图下逐节点链接证据。没有证据的环节标记断裂，不把流程箭头写成因果效应。`storyline.json` 按 `references/storyline-contract.md` 记录。

保留现象、理论、方法、数据、政策五维标签，每维最多一项。笔记中实际标签必须以 # 开头，分别用 #phenomenon/、#theory/、#method/、#data/、#policy/ 命名空间；例如 #method/组均值比较。不要只输出不带 # 的关键词。没有充分证据填“未涉及”，不生成 #未涉及，不捏造。遵循 `references/tag-ontology.md`。

## 彩色标注与核验

证据按 `claim_type` 分色：背景、问题、理论、概念为蓝色；数据与方法绿色；结果橙色；讨论、局限和结论紫色；其他灰色。颜色是阅读辅助，不代表证据等级；每条同时保留类别、编号和中文解释，不只依靠颜色区分。

- Markdown：有原文 MD 时运行 `python "$SKILL_DIR/scripts/annotate_markdown.py" <workdir>`，生成独立 `paper.annotated.md`、复制引用的本地图片，并输出逐片段 `markdown_annotation_report.json`。只在原文块中存在唯一且不会破坏 Markdown 结构的精确片段插入 `<mark>`；公式、HTML、跨行或重叠等不安全情况跳过并记录。颜色依赖阅读器对 HTML/style 的支持；标号和证据清单是后备，脚本不直接改写原文件。
- PDF：用户要求标注时，检测 PyMuPDF；缺失可在任务级虚拟环境安装后运行 `python "$SKILL_DIR/scripts/annotate_pdf.py" <workdir> <source.pdf>`。仅对已有 MD 核验证据及同页唯一的规范化完整文本创建标准彩色高亮和中文评论。保留标点、数学符号、正负和比较符，匹配不唯一或不足时不猜测。输出单独 PDF 和逐片段 `annotation_report.json`；物理页不等于印刷页码。仅 PDF 无法标注时也需在笔记逐项说明原因。
- 完成两种标注后运行 `python "$SKILL_DIR/scripts/finalize_notes.py" <workdir>`。无报告时写明未执行；未匹配、歧义、短文本、重叠、格式不安全等每个支持片段均须列出原因。部分支持片段成功不代表整条证据全部标注。
- 运行 `python "$SKILL_DIR/scripts/audit_note.py" <workdir>`；审计通过仅说明结构和摘录机械检查通过。逐项核对结论语义与原文，目视检查全部有批注页面及典型位置，检查颜色、注释内容和双栏错位。报告原文、图表和补充材料的限制、标注成功和失败数量，不声称全部准确。

## 精简交付与收尾

默认生成独立标注副本。用户要求标注但未表达偏好时，提供副本与覆盖指定输入 PDF 和／或 Markdown 的选择；未得到选择则使用副本。仅要求标注不等于授权覆盖。仅对用户明确指定的文件，在标注、语义及页面检查和 `finish_review.py --clean` 全部成功后执行替换；标注脚本本身不覆盖输入。

逐个替换时，先在不冲突的新路径保存原文件的逐字节备份并核对哈希；替换前核对输入仍与分析时一致。文件已变更、被占用、不可用或权限不足时保留原件并报告。Markdown 须确认原文件所在目录下图片及证据链接可用（必要时调整指向最终笔记的链接），无法验证则不替换。在输入文件同目录写入临时文件并原子替换，逐项报告结果和备份路径；若替换了 Markdown，更新 `review.json` 指向保留的原始备份并保留原始哈希，笔记说明证据行号和哈希针对该备份。PDF 的备份另外记录。不得覆盖已有备份或静默删除备份。PDF 与 Markdown 的选择分别处理并报告。

默认仅交付：`notes.md`（精读、具体流程图、原句及逐片段标注状态）、`review.json`（汇总证据），以及用户需要的 `paper.annotated.pdf` / `paper.annotated.md` 和后者引用的图片。不要把索引、阅读日志、多个证据副本、CSV、字段说明等处理过程文件全部交给用户。

完成语义复核和标注页面检查后，运行 `python "$SKILL_DIR/scripts/finish_review.py" <workdir> --paper-id <文献库编号> --clean`。脚本重新运行机械审计，验证证据和标注报告，写入并回读 `review.json` 成功后，才清理固定名单内的生成文件。源文件、笔记、彩色副本、图片和未识别文件均保留。对既有目录操作前确认其中名单文件是本技能生成的；不要扩展删除范围或递归删除目录。未完成核查或审计失败时不得清理、不得报完成。

`review.json` 在顶层保存一次论文标识与源哈希，每条论断内嵌多个 supports。保留内容、类型、核验状态、解释边界、逐字原句、位置和标注状态；省去重复的 UID、路径、颜色及派生标签。字段见 `references/delivery-contract.md`。原文变更视为新版本，本地证据编号不因排序重新分配。

CSV 仅在用户明确要求表格导出时，清理前运行 `export_evidence.py` 并给收尾命令加 `--keep-csv`，不要作为默认交付。清理后的目录为完成态，若需重新索引、修改证据或生成标注，使用原论文建立新的工作目录，不能把完成态 JSON 冒充原始工作账本。

## 常用命令

将 `SKILL_DIR` 设为已安装技能所在绝对路径，下例的 `python` 表示选定的解释器。以下仅为各阶段入口，不省略阅读与复核。

```text
python "$SKILL_DIR/scripts/check_env.py" <工作目录>
python "$SKILL_DIR/scripts/run_pipeline.py" prepare <工作目录> --markdown <论文.md>
python "$SKILL_DIR/scripts/read_sections.py" <工作目录> --section SEC001 --page 0
# 全文阅读、填写覆盖、图像、证据、标签及研究主线。
python "$SKILL_DIR/scripts/run_pipeline.py" verify <工作目录>
# 撰写 notes.md；仅当明确要求且能力可用时加 --pdf <论文.pdf>。
python "$SKILL_DIR/scripts/run_pipeline.py" annotate <工作目录> [--pdf <论文.pdf>]
# 人工核对证据及标注页面后执行；需要 CSV 时加 --keep-csv。
python "$SKILL_DIR/scripts/run_pipeline.py" finish <工作目录> [--paper-id <文献库编号>]
```

合并阶段失败时保留已产生文件并检查错误；直接重跑可能遇到已有输出，不得绕过审计或清理保护。
