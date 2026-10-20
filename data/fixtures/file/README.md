# fixtures/file

状态：**M1 生成器已落地；M5 消费**。

三类高频管道（子目录）：

| 目录 | 构造 | 期望 |
|---|---|---|
| `bom-conflict/` | BOM 与实际内容矛盾 | `bom_conflict` 单列 |
| `utf16-misalignment/` | 字节数奇 / 错位一字节 | `utf16_misalignment` 证据 |
| `zip-cjk-utf8/` | zip 中文名 + `flag_bits & 0x800` | UTF-8 解释 |
| `zip-cjk-cp437/` | 同内容无 UTF-8 标志 | CP437 假设 + 两种解释并列 |

zip 生成固定 `ZIP_STORED`、`create_system=0`、时间戳 `(1980,1,1,0,0,0)`；golden 逐字节一致。
