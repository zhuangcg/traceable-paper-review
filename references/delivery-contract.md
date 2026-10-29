## 精简交付

默认目录：

```text
notes.md
review.json
paper.annotated.pdf       # 需要 PDF 标注时
paper.annotated.md        # 需要 MD 高亮时
mineru/images/...         # MD 实际引用的图片
```

索引、阅读日志、标注几何报告和审计过程数据在独立工作目录使用。finish_review.py 先重新审计，再生成 review.json 并验证可读取，随后按固定文件名清理。该命令不递归删除目录，不清除未知文件，不改原论文。保留的笔记仍包含可读的原句与失败原因；JSON 用于程序读取。这两份用途不同，不再额外交付 evidence.md、CSV 和重复账本。

## 汇总 JSON

- schema_version：字段版本。
- paper：论文库编号、源文路径及 SHA-256，每篇仅保存一次。
- quality：机械审计结果、警告和图像阅读等检查边界；不表示科学结论已经验证。
- tags：五个标签槽位，没有则为 null；解释详见笔记。
- evidence：论断数组，每项包含 id、type、claim、status、note、supports；仅实际为读者分析时添加 reader_note=true。
- supports：每个原文片段的 quote、section、lines=[起始行,结束行]，以及 pdf/md 标注状态。成功的 PDF 定位保存物理页 page；失败或未执行时保存 status 和 reason。

没有原文支持的 uncertain/rejected 条目仍保留，supports 可以为空。没有页码时省略，不填 0。证据类型和核验状态沿用 evidence-contract.md。论文编号与源哈希加本地证据编号足以定位，避免每项反复保存完整 UID 和路径；数据库导入可据此构造组合键。源文改变即新版本，本地编号应保持其论断含义。

清理后目录不是工作账本，修改或重新标注应从原始论文新建工作目录。CSV 仅按需导出；明确需要保留时给收尾命令添加 --keep-csv。
