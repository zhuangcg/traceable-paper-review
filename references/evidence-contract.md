# 证据契约：形式正确 ≠ 语义正确

## 证据对象（evidence.json）

采用 JSON **数组**，不是 JSON Lines。每条事实只建一个结论条目，跨句共用时需逐句复核：

```json
[
  {
    "id": "E0001",
    "claim": "论文实际报告或定义的一个具体事实（中文精确转述）",
    "claim_type": "result",
    "status": "verified_direct",
    "supports": [
      {"block_id": "B00042", "quote": "Exactly copied contiguous words from the source"}
    ],
    "semantic_check": "说明摘录如何支持转述、对象及限定条件。",
    "figure_table": "Table 2",
    "reader_note": false
  }
]
```

`claim_type` 可取 `background|problem|theory|definition|data|method|result|discussion|limitation|conclusion|metadata|other`。
`status` 仅可取 `verified_direct|verified_synthesis|uncertain|rejected`。`verified_synthesis` 须 >=2 段支持，或者在 `semantic_check` 解释单个段落如何已包含综合关系；只要出现矛盾，降为 uncertain。
`supports` 一般选择最短且足够的英文原文摘录，必须是块中的**连续字词**；不得将相隔多句拼接成一个 quote。可用多个支持项表示不同片段。摘录必须保留支持结论所需的**完整句子**，通常一至两句；不要为了缩短字数截断必要限定词。跨句或跨段应作为多个 supports 分别保存，不允许拼接后声称逐字匹配。
`figure_table` 是可选项：只有原始块真的提到对应的 Figure/Table，且读过相关图注/表格才能使用；宁可留空。
`semantic_check` 不得为空，需涵盖研究对象、样本/时相、统计口径、限定词、实证支持强度。脚本对其只能检查存在，不能代替人工判断。

## 文中可点击的定位码

必须使用 `verify_evidence.py` 产生的 `citation_map.json` 中 `locator` 字段，样式为 **`[E0001](#e0001)`**。正文每个可核验事实后面直接带链接。

运行 `finalize_notes.py` 后，**同一个 notes.md 文件文末**自动生成对应的 `### E0001` 证据条目，包含逐字原句、源行号、中文论断、解释边界及每片段标注状态。无需打开 `evidence.md` 才能看到原句。标题锚点的生成由阅读器决定，不支持时按编号查找；不根据 MD 行号推算 PDF 页码。

执行标注后再运行 `finalize_notes.py`，逐支持片段附带 PDF 物理页或失败原因和 Markdown 标注状态。部分成功不是全部成功。

## 定量事实及公式的特殊核查

- 对百分比、绝对数、回归系数、p 值、95% CI、样本数、时间、尺度、阈值逐个核对单位和口径。若正文与表格不一致，明确记录冲突，不替作者决定正确值。
- 表格：读表头、行、脚注、单位与星号含义。图形：可直接访问图像时先阅读图注与图内信息；若不能可靠获取图中数值，只有正文明确给出时才能定量复述。
- 公式：保持原符号、上下标和变量定义；如需要数学推导，应标 `[读者推导]`，不能归因于作者。
- 区分观测关联、控制混杂、预测、实验对照与因果识别；不能将“associated with”转译为“导致”。
- 作者对现象的解释可能是推测；“可能/提示/与之相符”等限定词在中文中保持。

## 无法确认时怎么做

- 原 MD 缺图、乱码、表格转写失败、引用不连续：`status=uncertain`、写 `待核验`，不要作为已证实结果使用。
- 找不到足够原文支撑的结论：删掉或标为读者问题；禁止为了满足摘要长度去补全。
- `source_manifest.json` SHA256 与原 Markdown 不一致：旧 locator 失效，必须重新索引并重新核查。

## 为什么机器核验仍有限

标准库脚本能检查文件是否变化、块是否存在、摘录是否真的位于块内、编号与链接是否一致。它**无法自动判断**“引用段落是否真的逻辑支持该句”，也无法保证图像/表格解释正确。这必须由执行该 Skill 的模型通过二次语义阅读完成，最后保留人工可复核的定位信息。
