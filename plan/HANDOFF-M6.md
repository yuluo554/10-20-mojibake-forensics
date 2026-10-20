# HANDOFF-M6 · 发布（tag + Release + 发布留档）

> 上一棒：M5（`file` 原始字节管道 + `scan` CI 门禁 + 退出码 4 全面退役）。本文件是 M6 的交接单；动手前先跑布局门。

## 一、当前进度 + 证据

- **M5 已完成（2026-10-20）**：
  - `file`：`src/mojibake_forensics/file.py` 实现 `inspect_path()` / `inspect_bytes()` / `run()` / `render()`。只读二进制打开（`rb`），永不写回；分节报告 `bom`（UTF-8/UTF-16LE/BE/UTF-32 先后嗅探）+ `bom_conflict`（BOM 声明与内容矛盾时列 `content` 证据：body_hex / as_utf8 / as_gb18030）、`utf16_misalignment`（奇字节数 + 错位一字节证据 `shifted_text`，不自动改）、`zip_names`（`flag_bits & 0x800` 判 UTF-8；无标志列 CP437 与 UTF-8 两种解释 + note「工具不选择」；只读中央目录，不解压成员）、`csv_candidates`（`--preset csv-excel-win`：cp1252/gbk/shift_jis 可解码性 + 分隔符嗅探）。文件不存在 → `file_unreadable` 退出码 2。
  - `scan`：`src/mojibake_forensics/scan.py` 实现 `line_hit()` / `scan_directory()` / `scan()` / `run()` / `render()`。命中判据 = K9（`readability(line)<0.5` + 存在无损候选 `readability(result)≥0.8` + gain `≥0.3`；候选走 `attr.search`，不重新枚举）；命中定位「相对路径 + 行号 + 候选集」；分桶 `new[]` / `baselined[]` / `stale[]`（基线指向已不存在文件 → stale，不影响退出码）；基线 JSON 语法/结构错误 → `baseline_invalid` 退出码 2 且不产出任何文件；全程只读。
  - **退出码 4 全面退役**：`report.EXIT_NOT_READY` 常量删除；`cli._exit_code_for` 去掉 `not_ready` 分支；测试改为「缺文件 → 退出码 2」的实证断言 + `test_exit_code_4_is_retired`；`data/README.md` §4.7、`README.md` 退出码表同步。五个子命令现在只用 0/1/2/3。
  - 新测试 `tests/test_file.py`（12 条）与 `tests/test_scan.py`（12 条）：三类管道 fixture golden 逐字节断言 + 输入文件前后字节一致（只读）、干净语料 0 报告 0 改动（mtime+内容快照）、污染语料退出码 1 且可定位（ja.md/zh.md + 行号 + 候选含 日本語/中文測試）、stale 不影响退出码、基线覆盖命中进 `baselined` 不计 `new`、坏基线退出码 2 零文件产出、双跑逐字节一致、JSON 键序 canonical、报告无绝对路径、codec 不可用 → 3。
- **证据位置**：
  - `py tools/check_sprint_layout.py` → 全绿（本棒已复跑）。
  - `py -3.8 -m pytest -q` / `py -3.12 -m pytest -q` → 全绿（175 条，新增 24 条）。
  - `py -3.12 bench/run.py --check` → `golden matches`（M5 未动共享层，逐字节一致）。
  - 冒烟：`file --path data/fixtures/file/{四个 fixture}` 输出与 `expect.json` expected 块逐字段一致，退出码 0；`scan --dir data/fixtures/scan/clean --baseline ...` → ok / 0 new / 退出码 0；`scan --dir data/fixtures/scan/polluted --baseline ...` → attention / 2 new（ja.md:1 日本語、zh.md:1 中文測試）/ 退出码 1。
  - `git log --oneline`。

## 二、当前事实 · 状态不变量

1. **五个子命令全部落地**：`attr`(M2) / `explain`(M3) / `recover`(M4) / `file`(M5) / `scan`(M5)；退出码只有 0/1/2/3，`EXIT_NOT_READY` 已删。
2. **`attr.search` 仍是候选唯一入口**：scan 的逐行检测也走它（K9 候选集），未引入第二套枚举。
3. **`replay_chain` 复算唯一口径不变**；`file` 不重放链路（原始字节证据面）。
4. **`file` / `scan` 全程只读**：`file` 打开模式 `rb`；`scan` 不写目标目录任何文件；`--out` 类写入只存在于 recover 且永不覆盖输入。
5. **K1–K9 口径不变**（K 表见 `plan/HANDOFF-M5.md` §四；K9 = scan 命中判据，`data/README.md` §4.8）。
6. **CI 仍未实跑**：任何 DoD 只能写"本地等价校验，未接远端，CI 待首推验证"。
7. **环境事实**（2026-10-20 实测，会过期）：`python` 是商店占位符 → 用 `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`；Git Bash 打印 UTF-8 中文可能乱码，验收用解析器读。
8. **报告脱敏（K7）**：`file` 只报 `os.path.basename`；`scan` 只报相对路径；报告无时间/主机名/绝对路径/Python 版本（envelope 的 `python_version` 沿用既有 schema 字段，K1 允许）。
9. **发布留档要求**（M6 起布局门强制）：`plan/RELEASE-M6.md` 两栏（`## 一、tag 前事实` / `## 二、tag 后追加`）+ 覆盖对账小节 + ≥3 行三态（实现/不适用/待首推）。

## 三、下一棒待办（M6）

- [ ] 脱敏四步（代码 / 文档 / 提交元数据 / tag tagger 邮箱）；核对报告面无本机路径。
- [ ] tag 前：跑全套门（布局门 + 双解释器 pytest + `bench/run.py --check` + fixture `--check` 循环）；`plan/RELEASE-M6.md` 第一栏（tag 前事实）落盘。
- [ ] `git tag -s` 或 annotated tag `v0.1.0`（tagger 邮箱脱敏）；GitHub Release + 手工源码包（`git archive` + `gzip -9n` + `SHA256SUMS`），本地留副本 + sha256 记录。
- [ ] tag 后：`plan/RELEASE-M6.md` 第二栏（tag 后追加）+ 覆盖对账表；干净环境按 README 跑通四场景（attr / explain / recover / scan）。
- [ ] 提交面脱敏复查（`git log` 作者/邮箱）；附件与 tag 树共有文件逐字节一致。
- [ ] 写 `plan/HANDOFF-M7.md` 或收尾说明（收尾棒也适用）。

## 四、既定口径清单（K 编号，动了会打挂测试）

| 编号 | 约定 | 位置 |
|---|---|---|
| K1 | 输出 schema 固定 `mojibake-forensics/1`；字段只增不改 | `report.py`、`README.md` §字段 |
| K2 | `ENCODERS` / `DECODERS` / `MAX_DEPTH=3` 冻结（解码器 7 个） | `codecs_table.py`、`data/README.md` §4.1/§4.2 |
| K3 | 退出码 0/1/2/3 语义单点定义；**`EXIT_NOT_READY` 已删除（M5）** | `report.py`、`data/README.md` §4.7 |
| K4 | JSON 序列化参数与 LF/尾换行冻结 | `report.py` |
| K5 | 无损性判据 = 逆序逐步重放，禁止 `errors='replace'` / `ignore` | `paths.py`、`data/README.md` §4.3 |
| K6 | 排序键 `(-score_total, depth, path_string)` | `score.py`、`data/README.md` §4.4 |
| K7 | 报告不含时间/主机名/绝对路径/Python 版本（bench 亦同） | `report.py`、`bench/run.py` |
| K8 | 状态副本三处一致；缺口表不提已 ✅ 里程碑 | `plan/00`、`plan/05`、`README.md`、`plan/06` |
| K9 | `scan` 命中判据 = 逐行；input `<0.5`、candidate `≥0.8`、gain `≥0.3` | `data/README.md` §4.8、`plan/03` §七 |
| K10 | `file` 全程只读、zip 只读中央目录不解压、双解释并列不选择 | `file.py`、`plan/03` §六 |

## 五、本机环境坑（实测 2026-10-20）

- `python` 是商店占位符 → 用 `py` / `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`。
- Git Bash 打印 UTF-8 中文可能显示乱码；验收文件用 `py -3.12` 读或解析器回读，不靠控制台肉眼。
- pytest 版本：3.8 → 7.4.4；3.12 → 8.4.2；两通道全绿。
- `bench/golden/attr.json` 不要手改；M5 未冻结新 golden（`--check` 逐字节一致）。
- `tests/independent_replay.py` 以子进程方式跑（stdin JSON），pytest 里用 `sys.executable`。
- fixture 文本对比用 `io.open(..., newline="")`；`Path.write_text` 在 3.8 无 `newline` 参数。
- `scan` 的 mtime 快照断言（`tests/test_scan.py::_snapshot`）依赖文件不被触碰；任何给 fixture 目录新增文件的改动都会翻红。
- 本机事实会过期：引用前先复测并带日期。

## 六、DoD 逐项 checklist（M6）

- [ ] tag 前全套门绿：布局门 + `py -3.8/-3.12 -m pytest -q` + `bench/run.py --check` + fixture `--check` 循环。
- [ ] `plan/RELEASE-M6.md` 两栏（tag 前 / tag 后）+ 覆盖对账表；≥3 行三态。
- [ ] `v0.1.0` annotated tag + GitHub Release + 手工源码包（`git archive` + `gzip -9n` + `SHA256SUMS`）；本地副本 + sha256 记录。
- [ ] 脱敏四步完成；干净环境按 README 跑通四场景；提交面无本机身份。
- [ ] CI 类 DoD 写"本地等价校验，未接远端，CI 待首推验证"。

## 七、关键命令速查

```bash
# 布局门（新对话第一件事）
python tools/check_sprint_layout.py

# 测试（双解释器）
py -3.8 -m pytest -q
py -3.12 -m pytest -q

# 57 例探针
py -3.12 bench/run.py --check

# file 冒烟（M5 已完成）
py -3.12 -X utf8 -m mojibake_forensics file --path data/fixtures/file/bom-conflict/bom-conflict.bin --json
py -3.12 -X utf8 -m mojibake_forensics file --path data/fixtures/file/utf16-misalignment/utf16-misalignment.bin --json
py -3.12 -X utf8 -m mojibake_forensics file --path data/fixtures/file/zip-cjk-utf8/zip-cjk-utf8.zip --json
py -3.12 -X utf8 -m mojibake_forensics file --path data/fixtures/file/zip-cjk-cp437/zip-cjk-cp437.zip --json
py -3.12 -m mojibake_forensics file --path missing.bin --json          # file_unreadable, 退出码 2

# scan 冒烟（M5 已完成）
py -3.12 -X utf8 -m mojibake_forensics scan --dir data/fixtures/scan/clean --baseline data/fixtures/scan/clean-corpus.json --json   # 0 new, 退出码 0
py -3.12 -X utf8 -m mojibake_forensics scan --dir data/fixtures/scan/polluted --baseline data/fixtures/scan/clean-corpus.json --json # 2 new, 退出码 1

# fixture 重建 / 校验
for g in $(find data/fixtures -name gen.py | sort); do py -3.12 "$g" --check; done

# 环境事实复测
py -0p
```
