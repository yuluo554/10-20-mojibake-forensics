# file/utf16-misalignment

状态：**待 M5**。

- 构造：UTF-16 字节数为奇，或整体错位一字节。
- 期望：`utf16_misalignment` 给出"错位一字节后能否解出合法文本"的证据；只报不改。
