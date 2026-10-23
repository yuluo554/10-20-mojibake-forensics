# fixtures/scan

状态：**M1 生成器已落地；M5 消费**。

- `clean-corpus.json`：**只含统计与相对路径清单**，不含语料原文；期望 `new == []`。
- `polluted/`：由合成短句经固定链路转坏；期望 `new` 非空、退出码 1。
- `stale` 条目（基线指向已不存在文件）只提示，不影响退出码。
- `gen.py --check` 重生成逐字节一致。
- **基线根 = 本目录**（`data/README.md` §4.6）：基线里的路径写 `clean/en-01.md`、`polluted/ja.md`，
  报告也照此输出；`--dir clean` / `--dir polluted` 只决定走哪棵子树。⇒ 一份基线同时服务两棵子树，
  `stale` 不会因为收窄 `--dir` 而误报。
- `expect.json` 是**活判据**：`tests/test_scan.py::test_expect_json_matches_reality` 逐格断言
  `clean` / `polluted` 的 `new` / `baselined` / `stale` / `files_scanned` / `exit_code`。
