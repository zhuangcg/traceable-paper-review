## CSV 证据表

CSV 仅在用户明确要求时导出。工作期 `evidence.json` 是账本，最终默认保留汇总 `review.json`，`evidence.csv` 是可选的数据库导入视图。每行一条“论断—支持片段”关系；无支持片段的论断也保留一行，其片段字段为空。CSV 为 UTF-8 BOM、逗号分隔、全部字段加双引号，内部引号、换行及中文通过标准 csv 库原样保存。不要用简单的逗号切分读取。

| 字段 | 含义 |
|---|---|
| schema_version | 当前为 1；将来变更列含义时升级 |
| paper_id | 文献库编号，由调用者提供；缺省使用版本哈希，不自动推断 DOI |
| source_version_id / source_sha256 | 原 MD 的 SHA-256，明确论文文本版本 |
| evidence_uid / evidence_id | 版本哈希加本地论断编号；本地编号应在修订时保留 |
| support_uid / support_index | 论断 UID 加块与原句内容哈希；序号仅供显示，重排时内容 UID 不变 |
| claim / claim_type / claim_group | 中文论断、细分类英文代码、用于颜色的中文分类 |
| verification_status / semantic_check / reader_note | 核验状态、解释边界、是否读者分析（true/false） |
| quote / block_id / section / line_start / line_end | 逐字原句与 MD 块、章节和块行号；行号不是 PDF 页码 |
| source_md | 源 MD 路径；在别的机器上需另行映射 |
| pdf_annotation_status / pdf_annotation_reason / pdf_physical_page | PDF 标注状态、失败原因、成功时的物理页 |
| markdown_annotation_status / markdown_annotation_reason | MD 标注状态与失败原因 |
| highlight_color | 该类型的预定颜色；有颜色不代表标注成功 |

`verification_status` 保持 verified_direct / verified_synthesis / uncertain / rejected。
`claim_type` 保持 background / problem / theory / definition / data / method / result / discussion / limitation / conclusion / metadata / other。
标注成功为 matched；其余保留原报告状态。未执行为 not_generated，有报告但无该片段为 not_recorded，无支持片段为 not_applicable。缺失页码用空字符串，不填 0 或猜测值。空字符串在数据库导入时可按字段转换成 NULL；reader_note 转成布尔值，行号和页码转成可空整数。

建议数据库将论断按 evidence_uid 去重，把非空支持片段按 support_uid 去重；导入前检查同一 UID 的论断字段是否冲突。不要按中文内容直接合并，也不要以 CSV 行数代替论断数。源文本修改会生成新版本 UID；本文不同版本之间的语义对应需另行确认。CSV 保留精确文本，使用表格软件浏览时以文本方式导入原句和论断列。
