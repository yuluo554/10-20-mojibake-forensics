# HANDOFF-M4 · 从 explain 证明进入 recover 判定

> 上一棒：M3（`explain` 证明落地：逐步重放 + 独立复算 + 对照分叉点 + explain 退出码 4 退役）。本文件是 M4 的交接单；动手前先跑布局门。

## 一、当前进度 + 证据

- **M3 已完成（2026-10-20）**：
  - `explain`：`src/mojibake_forensics/explain.py` 实现 `explain()` / `run()` / `render()`。**不重新枚举**：新增 `attr.search(text, encoders, decoders)` 把"枚举 → collapse → rank"提为共享入口，返回带 `chain` 键的已排序候选（`Chain` 仍是唯一中间表示，`plan/02` 口径不破）；`attr.attribute()` 改为调用它，输出与 M2 golden 逐字节不变。
  - 逐步重放 `replay_chain(chain)`：每步把重放状态与 `paths.Step` 记录双向比对（记录的输入 = 重放状态；`state.encode/decode(codec)` = 记录的输出），第一处不一致停在 `failed_step`（1 起），`failure` 带 `reason`（`encode_error` / `decode_error` / `input_mismatch` / `mismatch` / `state_type` / `missing_record`）+ 字节/字符偏移。
  - 状态：verify 全绿 → `status="ok"`（退出码 0）；任一步失败 → `"verify_failed"`（退出码 1）；无候选 → `"no_candidate"` + `depth_limit_reached`（退出码 1，`proofs=[]`）。
  - 对照：`--vs m`（缺省 = top-2 中另一条：pick 1↔2，其余取 1）；`compare_proofs` 输出第一处差异 `divergence`（`kind=step|bytes|text|depth|none` + `at_step` + 偏移 + 两侧值 + `statement`），**只陈述差异**。候选不足两条 → `notes=["no_second_candidate"]`。
  - CLI：`--pick` / `--all` 改为 argparse 互斥组（必居其一）；`--all --vs` → 退出码 2；`--pick`/`--vs` 越界 → `pick_out_of_range` / `vs_out_of_range`（退出码 2，报候选总数）。`_exit_code_for` 增加 `verify_failed → 1`，移除已无来源的 `"explain"` status。
  - **explain 的退出码 4 退役**（CLI 分支 / `test_cli_skeleton` / README / plan/03 / data/README 五处同步；`EXIT_NOT_READY` 常量保留给 `recover` / `file` / `scan`）。
  - 独立重放脚本：`tests/independent_replay.py`（stdin 收 `{"text", "payload"}`，只用标准库 + 报告自身 `path`/`steps` 字段复算，不 import 工具内部状态）；`tests/test_explain.py` 用它对 `--pick 1` 与 `--all`（323 条）全候选取证，并验证篡改一步（改 `output_hex`）即 FAIL。
- **证据位置**：
  - `py tools/check_sprint_layout.py` → 全绿（本棒已复跑，见 git log）。
  - `py -3.8 -m pytest -q` / `py -3.12 -m pytest -q` → 全绿（新增 `tests/test_explain.py`，含独立重放 subprocess 取证）。
  - `py -3.12 bench/run.py --check` → `golden matches`（3.8 / 3.12 双通道一致；`attr.search` 重构未改变任何输出字节）。
  - 冒烟：`explain --text "é›…" --pick 1 --vs 2 --json` → `ok` + `verify=true` + 分叉 `step 2: decode:utf-8 vs decode:latin-1`，退出码 0；`explain --text "/" --pick 1 --json` → `no_candidate`，退出码 1；`--pick 999` / `--vs 999` → 退出码 2；`--all --vs 2` → 退出码 2。
  - `git log --oneline`。
- **当前仍返回退出码 4 的子命令**：`recover` / `file` / `scan`（M4–M5 各自退役）。

## 二、当前事实 · 状态不变量

1. **`attr.search` 是候选唯一入口**：`attribute()` 与 `explain` 都走它；`recover` 也必须走它（`--pick` 取 `ranked[n-1]["chain"]`），不得重新枚举。
2. **`explaine` 的复算口径**：重放状态与记录双向比对；`recover` 的 `verify` 失败降级（M4）应复用同思路：重放结果 ≠ `attr` 候选的 `result` → `LOST(reason="verify_failed")`。
3. **`no_candidate` 时 `proofs=[]`**：explain 不伪造证明；`recover` 判死（M4）同样不许猜字。
4. **`--vs` 缺省语义**：top-2 中的另一条（pick 1↔2，其余取 1）；候选 < 2 → `no_second_candidate` note，不报错。`divergence.statement` 里不得出现 better/best/likely/correct/should（有测试断言）。
5. **对照顺序固定**：op/codec → 字节（encode 步）→ 文本（decode 步）→ 链长；`compare_proofs` 只对 `--pick` 模式的第一条 proof 填 `divergence`。
6. **独立重放脚本是验收形态**（`tests/independent_replay.py`）：M4 的五类不可逆 fixture 校验同样要求"期望值可由标准库独立复算"（`tests/test_fixtures.py` 已是这个路数）。
7. **退出码 0/1/2/3 语义单点**在 `data/README.md` §4.7；`_exit_code_for` 现覆盖 `ok / candidates / recovered / no_candidate / verify_failed / error / not_ready`。
8. **K1–K9 口径不变**（见下表）；`EXIT_NOT_READY` 常量保留到 M5 最后一个子命令退役。
9. **CI 仍未实跑**：任何 DoD 只能写"本地等价校验，未接远端，CI 待首推验证"。
10. **环境事实**（2026-10-20 实测，会过期）：`python` 是商店占位符 → 用 `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`；Git Bash 打印 UTF-8 中文可能乱码，验收用解析器读。

## 三、下一棒待办（M4）

- [ ] 实现 `recover`（`plan/03` §五 为准）：
  - CLI：`--text <s> --pick <n> [--out <path>] [--json]`；`--pick` 必填（缺省 → 退出码 2，提示先跑 `attr`）；`--out` 与输入同路径 → 退出码 2；**永不覆盖输入**。
  - 判定顺序固定：**先判不可逆五类**（`U+FFFD` → `replacement_char`；`锟斤拷` → `kun_jin_kao` + `EF BF BD` 重复位置；`烫烫烫`/`屯屯屯` → `NOT_MOJIBAKE(reason="msvc_fill")`；`?` 截断 → `encode_truncated`；`errors='ignore'` 静默丢失 → `silent_drop`），再按 `--pick` 重放 → `RECOVERED` + `verify`。
  - `verify` 失败 → 降级 `LOST(reason="verify_failed")`；**绝不输出未经验证的修复**。
  - fixture：`data/fixtures/recover/` 五例已落（M1），期望值已在 `expect.json`；`tests/test_fixtures.py` 已独立复算过构造，M4 只需接 CLI/引擎。
- [ ] **退役 `recover` 的退出码 4**（CLI / 测试 / 文档同步；常量保留给 `file` / `scan`）。
- [ ] 测试：五类各一条单测（`LOST`/`NOT_MOJIBAKE` + 丢失点定位 + 无自造字符）；verify 失败降级（monkeypatch）；`--pick` 缺省/越界/`--out` 覆盖输入 → 2；`RECOVERED` 双跑逐字节一致；codec 不可用 → 3。
- [ ] 写 `plan/HANDOFF-M5.md`；M4 完成后回填 `plan/05` 状态表、`plan/00` 里程碑表、`README.md` 状态表（三处同提交）。
- [ ] 跑布局门 + 双解释器 pytest + `bench/run.py --check`。

## 四、既定口径清单（K 编号，动了会打挂测试）

| 编号 | 约定 | 位置 |
|---|---|---|
| K1 | 输出 schema 固定 `mojibake-forensics/1`；字段只增不改 | `report.py`、`README.md` §字段 |
| K2 | `ENCODERS` / `DECODERS` / `MAX_DEPTH=3` 冻结（解码器 7 个） | `codecs_table.py`、`data/README.md` §4.1/§4.2 |
| K3 | 退出码 0/1/2/3 语义单点定义；M2 起 attr、M3 起 explain 不再返回 4 | `report.py`、`data/README.md` §4.7 |
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
- `bench/golden/attr.json` 不要手改；口径变更用 `python bench/run.py --freeze` 重冻结。M3 重构后未再冻结（`--check` 逐字节一致，无需动）。
- `tests/independent_replay.py` 以子进程方式跑（stdin JSON），pytest 里用 `sys.executable`；它不 import 工具，别给它加依赖。
- 本机事实会过期：引用前先复测并带日期。

## 六、DoD 逐项 checklist（M4）

- [ ] 五类不可逆各一条单测：`LOST` / `NOT_MOJIBAKE` + 丢失点定位 + 输出无工具自造字符。
- [ ] `recover --pick N` 重放 → `RECOVERED` + `verify=true`；verify 失败降级 `LOST(reason="verify_failed")`。
- [ ] `--pick` 缺省 / 越界 / `--out` 覆盖输入 → 退出码 2 且零文件写入；codec 不可用 → 3。
- [ ] 双跑逐字节一致；输出无时间/主机名/绝对路径。
- [ ] recover 的退出码 4 退役（CLI / 测试 / 文档同步）。
- [ ] 布局门绿；`pytest -q` 双解释器绿；`bench/run.py --check` 绿。
- [ ] `plan/00` / `plan/05` / `README.md` 状态一致；写 `plan/HANDOFF-M5.md`。

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

# explain 冒烟（M3 已完成）
py -3.12 -m mojibake_forensics explain --text "é›…" --pick 1 --vs 2 --json
py -3.12 -m mojibake_forensics explain --text "é›…" --pick 1
py -3.12 -m mojibake_forensics explain --text "é›…" --all --json
py -3.12 -m mojibake_forensics explain --text "/" --pick 1 --json     # no_candidate, 退出码 1
py -3.12 -m mojibake_forensics explain --text "é›…" --pick 999 --json # pick_out_of_range, 退出码 2

# 独立重放取证（M3 验收形态）
py -3.12 -m mojibake_forensics explain --text "é›…" --all --json \
  | py -3.12 -c "import sys,json; print(json.dumps({'text':sys.argv[1],'payload':json.load(sys.stdin)},ensure_ascii=False))" \
  | py -3.12 tests/independent_replay.py

# recover 冒烟（M4 起）
py -3.12 -m mojibake_forensics recover --text "锟斤拷" --pick 1 --json

# fixture 重建 / 校验
for g in $(find data/fixtures -name gen.py | sort); do py -3.12 "$g" --check; done

# 环境事实复测
py -0p
```
