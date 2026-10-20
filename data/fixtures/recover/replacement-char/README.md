# recover/replacement-char

状态：**M1 生成器已落地；M4 消费**。

- 构造：非法字节序列被 decode 替换为 `U+FFFD`。
- 期望：`LOST(reason="replacement_char")` + 非法字节偏移。
