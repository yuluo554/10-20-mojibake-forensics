# fixtures/scan

状态：**待 M5**。

- `clean-corpus.json`：**只含统计与相对路径清单**，不含语料原文；期望 `new == []`。
- `polluted/`：由合成短句经固定链路转坏；期望 `new` 非空、退出码 1。
- `stale` 条目（基线指向已不存在文件）只提示，不影响退出码。
- `gen.py --check` 重生成逐字节一致。
