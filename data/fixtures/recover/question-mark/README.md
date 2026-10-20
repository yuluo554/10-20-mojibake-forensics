# recover/question-mark

状态：**待 M4**。

- 构造：目标编码无该字符映射，编码器写入 `?`。
- 期望：`LOST(reason="encode_truncated")` + 截断发生在 encode 方向的定位。
