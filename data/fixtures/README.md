# data/fixtures

全部 fixture 为**程序化合成**，不含真实公司、产品、人员、客户数据。生成器只依赖标准库，不 import `mojibake_forensics`——真值必须能由 `codecs` 独立复算。

## 目录

| 路径 | 内容 | 消费里程碑 |
|---|---|---|
| `genlib.py` | 共享确定性工具：规范 JSON、hex、sha256、`--check` 逐字节比对 | M1–M5 |
| `attr/` | 归因样例（3 条固定链路） | M2 |
| `explain/` | 正例 + 故意改错 codec 的负例 | M3 |
| `recover/{kun-jin-kao,tang-tang,question-mark,replacement-char,silent-drop}/` | 五类不可逆各一例；`common.py` 提供共享 payload 形状 | M4 |
| `file/{bom-conflict,utf16-misalignment,zip-cjk-utf8,zip-cjk-cp437}/` | 原始字节管道；`common.py` 提供确定性 zip 构造 | M5 |
| `scan/` | 干净语料基线（只含统计与路径）+ 污染语料 | M5 |

## 纪律

- `expect.json` 顶层只有 `input` / `expected` / `criteria` / `note`；**禁止 `observed_*`**。
- 每个 `gen.py` 支持 `--check`：在内存重算，与入仓 `expect.json` 及 artifact 逐字节比对；不写任何文件。
- 文本 fixture 用 `.md` / `.json`；字节 fixture（`.bin` / `.zip`）在 `.gitattributes` 标 `binary`。
- zip 固定 `ZIP_STORED`、`create_system=0`、时间戳 `(1980,1,1,0,0,0)`；3.8 与 3.12 重算一致。
- 五类不可逆的 `LOST` / `NOT_MOJIBAKE` 期望附丢失点；`silent-drop` / `question-mark` 明确标 `requires_provenance`——字符串本身无法反推丢失字符。

## 命令

```bash
python data/fixtures/attr/gen.py --check
python data/fixtures/recover/kun-jin-kao/gen.py --check
python data/fixtures/file/zip-cjk-utf8/gen.py --check
python data/fixtures/scan/gen.py --check
```

重新生成（会写入 `expect.json` / artifact）：

```bash
python data/fixtures/<module>/gen.py
```

数值口径唯一来源：`data/README.md` §四；探针复跑记录：§1.3.1。
