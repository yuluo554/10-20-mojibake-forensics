# fixtures/attr

状态：**待 M2**。

计划内容：

- `gen.py`：固定链路生成"已解坏的 str"，真值写 `expect.json`。
- `expect.json`：`input` / `expected_candidates` / `criteria` / `note`；不得出现 `observed_*`。
- 覆盖点：候选恒为列表、真答案在候选集内、排序键稳定、双跑一致。
