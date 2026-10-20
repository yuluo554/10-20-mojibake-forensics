# fixtures/recover

状态：**M1 生成器已落地；M4 消费**。

五类不可逆各一例（子目录）：

| 目录 | 构造 | 期望 |
|---|---|---|
| `kun-jin-kao/` | `EF BF BD` 重复被 GBK 读回 | `LOST(reason=kun_jin_kao)` + 丢失点 |
| `tang-tang/` | MSVC `0xCC` / `0xCD` 填充 | `NOT_MOJIBAKE(reason=msvc_fill)` |
| `question-mark/` | 目标编码无映射 → `?` | `LOST(reason=encode_truncated)` |
| `replacement-char/` | 非法字节 → `U+FFFD` | `LOST(reason=replacement_char)` + 偏移 |
| `silent-drop/` | `errors='ignore'` | `LOST(reason=silent_drop)` |

每个子目录含 `gen.py` / `expect.json` / `README.md`；断言输出不含工具自造字符。
