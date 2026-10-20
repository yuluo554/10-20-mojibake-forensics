# recover/tang-tang

状态：**待 M4**。

- 构造：MSVC Debug 用 `0xCC` / `0xCD` 填充未初始化栈，被当作文本读取。
- 期望：`NOT_MOJIBAKE(reason="msvc_fill")`——这不是编码事故，不参与"修复"。
