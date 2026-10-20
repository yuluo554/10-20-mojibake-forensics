# recover/tang-tang

状态：**M1 生成器已落地；M4 消费**。

- 构造：MSVC Debug 用 `0xCC` / `0xCD` 填充未初始化栈，被当作文本读取。
- 期望：`NOT_MOJIBAKE(reason="msvc_fill")`——这不是编码事故，不参与"修复"。
