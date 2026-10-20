# fixtures/attr

状态：**M1 生成器已落地；M2 已消费**（`tests/test_attr.py` 逐例断言真值入候选集且代表链路一致）。

计划内容：

- `gen.py`：固定链路生成"已解坏的 str"，真值写 `expect.json`。
- `expect.json`：`input` / `expected_candidates` / `criteria` / `note`；不得出现 `observed_*`。
- 覆盖点：候选恒为列表、真答案在候选集内、排序键稳定、双跑一致。
