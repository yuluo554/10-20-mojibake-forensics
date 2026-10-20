# HANDOFF-M5 · 从 recover 判定进入 file 管道 + scan 门禁

> 上一棒：M4（`recover` 确定性还原 + 不可逆判死 + recover 退出码 4 退役）。本文件是 M5 的交接单；动手前先跑布局门。

## 一、当前进度 + 证据

- **M4 已完成（2026-10-20）**：
  - `recover`：`src/mojibake_forensics/recover.py` 实现 `recover()` / `run()` / `render()`。**判定顺序固定**（`plan/03` §5.2）：先判不可逆五类，判死后不再重放——`U+FFFD` → `LOST(replacement_char)` + 偏移；`锟斤拷` → `LOST(kun_jin_kao)` + `EF BF BD` 重复位置（offset/repeat）；`烫烫烫`/`屯屯屯` → `NOT_MOJIBAKE(msvc_fill)`；`?` → `LOST(encode_truncated)` + 偏移。`silent_drop` 只在有出处证据时可判，CLI 面只有已解坏的 str → **不伪造该判定**（与 fixture `requires_provenance` 口径一致）。
  - **`RECOVERED` 必过 verify**：按 `--pick` 取 `attr.search` 已排序候选（不重新枚举），复用 explain 的 `replay_chain` 逐步双向比对；失败降级 `LOST(reason="verify_failed")`，**绝不输出未经验证的修复**（notes=`unverified_repair_suppressed` + `no_invented_characters`）。
  - CLI：`recover` 支持 `--text` / `--file`（与 attr 共面）；`--pick` 必填（缺省 → `missing_pick`，退出码 2）；越界 → `pick_out_of_range`（退出码 2，报候选总数）；`--out` 与 `--file` 输入同路径 → `out_overwrites_input`（退出码 2）；**永不覆盖输入**；`--out` 写 UTF-8 + LF。无候选 → `LOST(reason=no_candidate)` + `depth_limit_reached`（退出码 1），不猜字。
  - **recover 的退出码 4 退役**（CLI 分支 / `test_cli_skeleton` / README / data/README / plan/00 同步；`EXIT_NOT_READY` 常量保留给 `file` / `scan`，M5 结束前删）。
  - 新测试 `tests/test_recover.py`：五类各一条（LOST/NOT_MOJIBAKE + 丢失点偏移 + 无自造字符）、RECOVERED 双跑逐字节一致（JSON 与人读两路）、verify 降级（monkeypatch `replay_chain`）、`--pick` 缺省/越界/0、`--out` 不覆盖输入、codec 不可用 → 3、报告无主机事实。
- **证据位置**：
  - `py tools/check_sprint_layout.py` → 全绿（本棒已复跑）。
  - `py -3.8 -m pytest -q` / `py -3.12 -m pytest -q` → 全绿（新增 `tests/test_recover.py`）。
  - `py -3.12 bench/run.py --check` → `golden matches`（M4 未动共享层，逐字节一致）。
  - 冒烟：`recover --text "é›…" --pick 1 --json` → `recovered` + `雅` + `verify=true`，退出码 0；`recover --text "锟斤拷" --pick 1 --json` → `LOST(kun_jin_kao)`，退出码 1；`recover --text "烫烫烫" --pick 1` → `NOT_MOJIBAKE(msvc_fill)`，退出码 1；`recover --text "abc\ufffddef" --pick 1` → `LOST(replacement_char)` offset=3；`--pick` 缺省/越界 → 退出码 2。
  - `git log --oneline`。
- **当前仍返回退出码 4 的子命令**：`file` / `scan`（M5 退役，M5 结束前删常量）。

## 二、当前事实 · 状态不变量

1. **`attr.search` 是候选唯一入口**：`attribute()` / `explain` / `recover` 都走它；M5 的 `file` 归因若复用候选逻辑也必须走它，不得重新枚举。
2. **`replay_chain` 是复算唯一口径**：explain 与 recover 共用；`recover` 的 verify 失败只降级、不伪造。
3. **不可逆判死先于重放**：判定顺序固定（plan/03 §5.2）；`silent_drop` 需要出处证据，CLI 面不判。
4. **`no_candidate` 不猜字**：attr `candidates=[]`、explain `proofs=[]`、recover `LOST(no_candidate)`，三处口径一致。
5. **退出码 0/1/2/3 语义单点**在 `data/README.md` §4.7；`_exit_code_for` 现覆盖 `ok / candidates / recovered / lost / not_mojibake / no_candidate / verify_failed / error / not_ready`。
6. **K1–K9 口径不变**（见下表）；`EXIT_NOT_READY` 常量在 M5 最后一个子命令（`scan`）退役时删除——四处同步：常量 / CLI / 测试 / 文档退出码表。
7. **M5 `file` 只读**：三类管道 fixture（BOM 冲突 / UTF-16 奇偶错位 / zip 中文名带不带 `0x800`）golden 已在 `data/fixtures/file/`；`scan` 命中判据 = `data/README.md` §4.8（K9），干净语料基线零报告零改动。
8. **CI 仍未实跑**：任何 DoD 只能写"本地等价校验，未接远端，CI 待首推验证"。
9. **环境事实**（2026-10-20 实测，会过期）：`python` 是商店占位符 → 用 `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`；Git Bash 打印 UTF-8 中文可能乱码，验收用解析器读。
10. **bench 子进程偶发非零退出码**（3221225477，Windows 访问违例，一次实测）：`tests/test_bench.py::test_bench_check_is_deterministic` 复跑即绿，非口径漂移；如再现，先单独复跑确认。

## 三、下一棒待办（M5）

- [ ] 实现 `file`（`plan/03` §六 为准）：
  - CLI：`--path <path> [--preset csv-excel-win|zip-names|utf16] [--json]`；只读。
  - 三类管道：BOM 冲突、UTF-16 奇偶错位、zip 中文名（带/不带 `0x800` flag，CP437 对照）。
  - fixture：`data/fixtures/file/` 四例已落（M1），期望值在 `expect.json`。
- [ ] 实现 `scan`（`plan/03` §七 为准）：`--dir --baseline [--format json|human]`；命中判据 = K9（`readability(line)<0.5` + 候选 `≥0.8` + gain `≥0.3`）；干净语料零报告零改动；JSON 先写后定退出码；退出码 2 的路径禁止产出文件。
- [ ] **退役 `file` / `scan` 的退出码 4 并删除 `EXIT_NOT_READY` 常量**（常量 / CLI / 测试 / 文档四处同步）。
- [ ] 测试：三类管道 fixture 逐字节断言；干净语料 0 报告 0 改动（文件 mtime/内容前后一致）；污染语料退出码 1 且可定位；退出码四组稳定；报告不含绝对路径。
- [ ] 写 `plan/HANDOFF-M6.md`；M5 完成后回填 `plan/05` 状态表、`plan/00` 里程碑表、`README.md` 状态表（三处同提交）。
- [ ] 跑布局门 + 双解释器 pytest + `bench/run.py --check`。

## 四、既定口径清单（K 编号，动了会打挂测试）

| 编号 | 约定 | 位置 |
|---|---|---|
| K1 | 输出 schema 固定 `mojibake-forensics/1`；字段只增不改 | `report.py`、`README.md` §字段 |
| K2 | `ENCODERS` / `DECODERS` / `MAX_DEPTH=3` 冻结（解码器 7 个） | `codecs_table.py`、`data/README.md` §4.1/§4.2 |
| K3 | 退出码 0/1/2/3 语义单点定义；attr/explain/recover 均已退役退出码 4 | `report.py`、`data/README.md` §4.7 |
| K4 | JSON 序列化参数与 LF/尾换行冻结 | `report.py` |
| K5 | 无损性判据 = 逆序逐步重放，禁止 `errors='replace'` / `ignore` | `paths.py`、`data/README.md` §4.3 |
| K6 | 排序键 `(-score_total, depth, path_string)` | `score.py`、`data/README.md` §4.4 |
| K7 | 报告不含时间/主机名/绝对路径/Python 版本（bench 亦同） | `report.py`、`bench/run.py` |
| K8 | 状态副本三处一致；缺口表不提已 ✅ 里程碑 | `plan/00`、`plan/05`、`README.md`、`plan/06` |
| K9 | `scan` 命中判据 = 逐行；input `<0.5`、candidate `≥0.8`、gain `≥0.3` | `data/README.md` §4.8、`plan/03` §七 |

## 五、本机环境坑（实测 2026-10-20）

- `python` 是商店占位符 → 用 `py` / `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`。
- Git Bash 打印 UTF-8 中文可能显示乱码；验收文件用 `py -3.12` 读或解析器回读，不靠控制台肉眼。
- pytest 版本：3.8 → 7.4.4；3.12 → 8.4.2；两通道全绿。
- `bench/golden/attr.json` 不要手改；口径变更用 `python bench/run.py --freeze` 重冻结。M3/M4 重构后未再冻结（`--check` 逐字节一致，无需动）。
- `tests/independent_replay.py` 以子进程方式跑（stdin JSON），pytest 里用 `sys.executable`；它不 import 工具，别给它加依赖。
- fixture 文本对比用 `io.open(..., newline="")`；`Path.write_text` 在 3.8 无 `newline` 参数。
- 本机事实会过期：引用前先复测并带日期。

## 六、DoD 逐项 checklist（M5）

- [ ] `file`：三类管道 fixture 全对（BOM / UTF-16 错位 / zip 中文名）；全程只读。
- [ ] `scan`：干净语料零报告零改动；污染语料退出码 1 且可定位到「相对路径 + 行号 + 候选集」。
- [ ] 退出码 0/1/2/3 四组测试；JSON 键序固定；退出码 2 的路径不留输出文件。
- [ ] `file` / `scan` 的退出码 4 退役 + `EXIT_NOT_READY` 常量删除（常量 / CLI / 测试 / 文档四处同步）。
- [ ] 双跑逐字节一致；输出无时间/主机名/绝对路径。
- [ ] 布局门绿；`pytest -q` 双解释器绿；`bench/run.py --check` 绿。
- [ ] `plan/00` / `plan/05` / `README.md` 状态一致；写 `plan/HANDOFF-M6.md`。

## 七、关键命令速查

```bash
# 布局门（新对话第一件事）
python tools/check_sprint_layout.py

# 测试（双解释器）
py -3.8 -m pytest -q
py -3.12 -m pytest -q

# 57 例探针（含 depth3 硬门）
py -3.12 bench/run.py --check
py -3.12 bench/run.py --out bench/out/attr.json

# recover 冒烟（M4 已完成）
py -3.12 -m mojibake_forensics recover --text "é›…" --pick 1 --json   # RECOVERED 雅, 退出码 0
py -3.12 -m mojibake_forensics recover --text "锟斤拷" --pick 1 --json # LOST kun_jin_kao, 退出码 1
py -3.12 -m mojibake_forensics recover --text "烫烫烫" --pick 1 --json # NOT_MOJIBAKE msvc_fill, 退出码 1
py -3.12 -m mojibake_forensics recover --text "abc\ufffddef" --pick 1 --json  # LOST replacement_char offset=3
py -3.12 -m mojibake_forensics recover --text "a?b" --pick 1 --json    # LOST encode_truncated offset=1
py -3.12 -m mojibake_forensics recover --text "é›…" --pick 999 --json  # pick_out_of_range, 退出码 2
py -3.12 -m mojibake_forensics recover --text "é›…" --json             # missing_pick, 退出码 2

# file / scan 冒烟（M5 起）
py -3.12 -m mojibake_forensics file --path data/fixtures/file/bom-conflict/bom-conflict.bin --json
py -3.12 -m mojibake_forensics scan --dir <corpus> --baseline data/fixtures/scan/clean-corpus.json --json

# fixture 重建 / 校验
for g in $(find data/fixtures -name gen.py | sort); do py -3.12 "$g" --check; done

# 环境事实复测
py -0p
```
