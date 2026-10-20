# recover/silent-drop

状态：**M1 生成器已落地；M4 消费**。

- 构造：编码/解码使用 `errors='ignore'`，不可映射字符被静默丢弃。
- 期望：`LOST(reason="silent_drop")`；指出信息量为零，不补全。
