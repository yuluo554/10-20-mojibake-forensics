# recover/replacement-char

状态：**待 M4**。

- 构造：非法字节序列被 decode 替换为 `U+FFFD`。
- 期望：`LOST(reason="replacement_char")` + 非法字节偏移。
