# fixtures/explain

状态：**待 M3**。

计划内容：

- 正例：一条可重放链路，逐步字节断言全绿。
- 负例：故意把链路中一个 codec 名改错，断言 `verify=false` 且指向具体 step。
- `expect.json` 只存输入与期望；重放脚本不依赖工具内部状态。
