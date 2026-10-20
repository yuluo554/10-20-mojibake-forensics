# fixtures/explain

状态：**M3 已消费**。

内容：

- 正例：一条可重放链路（`encode:cp1252>decode:utf-8`），逐步字节断言全绿。
- 负例：故意把链路中解码器从 `utf-8` 改成 `gb18030`，断言 `verify=false` 且指向 step 2、字节偏移 2。
- `expect.json` 只存输入与期望；独立重放脚本（`tests/independent_replay.py`）不依赖工具内部状态。

消费方：`tests/test_explain.py`（`test_fixture_positive_chain_is_reported_step_for_step`、`test_mutated_codec_is_reported_at_the_exact_step`）。
