# HANDOFF-M3 · 从 attr 归因进入 explain 证明

> 上一棒：M2（`attr` 归因落地：有界候选 + 无损硬过滤 + 三层打分 + 置信度区间 + attr 退出码 4 退役）。本文件是 M3 的交接单；动手前先跑布局门。

## 一、当前进度 + 证据

- **M2 已完成（2026-10-20）**：
  - `attr`：`src/mojibake_forensics/attr.py` 实现 `attribute()` / `run()` / `render()`：`enumerate_chains(MAX_DEPTH=3)` → `collapse_by_result` → `score.rank` → `--top` 截断 → 置信度区间。候选恒为列表；`total_candidates`（不同结果数）/ `total_chains`（无损链路数）始终报完整数，不受 `--top` 影响。
  - 置信度（`data/README.md` §4.5）：分母 = 完整候选集总分；守卫 `Σ score_j <= 0` → `null` + `no_positive_score`（不造数）；单候选 → `1.0` + `single_candidate_in_bounded_search`；被截断候选标 `truncated_to_top_n`。
  - `--freq` 明确报 `freq_not_implemented`（退出码 2），不伪造语言先验；`--source-enc` / `--target-enc` 只可收缩冻结集合；`--file` 只读 UTF-8，读不了 → 退出码 2 且不回显绝对路径。
  - **attr 的退出码 4 退役**：CLI `_exit_code_for` 增加 `no_candidate → 1`；`attr` 人读输出走 `report.emit(..., human=render(payload))`。`EXIT_NOT_READY` 常量**保留**给 `explain` / `recover` / `file` / `scan`（M3–M5 逐个退役）。
  - 基准：`bench/run.py` 新增 `depth3` 块，调用真实 `attr` 在 `MAX_DEPTH=3` 重跑 57 例；`bench/golden/attr.json` 已重冻结并逐字节一致。
- **证据位置**：
  - `py tools/check_sprint_layout.py` → 全绿。
  - `py -3.8 -m pytest -q` / `py -3.12 -m pytest -q` → 全绿（含新增 `tests/test_attr.py`、改写 `tests/test_bench.py` / `tests/test_cli_skeleton.py`）。
  - `py -3.12 bench/run.py --check` → `golden matches`（3.8 / 3.12 双通道一致）。
  - `py -3.12 -m mojibake_forensics attr --text "é›…" --json` → `status="candidates"`、`total_candidates=323`、退出码 0；`attr --text abc --json` → `no_candidate` + `depth_limit_reached`、退出码 1。
  - `git log --oneline`。
- **当前仍返回退出码 4 的子命令**：`explain` / `recover` / `file` / `scan`（M3–M5 各自退役）。

## 二、当前事实 · 状态不变量

> 下一棒动手前必须知道的事实与禁区；不读会踩的坑。

1. **`attr` 是唯一可运行判定**：`explain` / `recover` / `file` / `scan` 仍是骨架（`not_ready` + 退出码 4）。
2. **置信度口径在 §4.5 已补全**：分母 = 完整候选集；守卫 `Σ score_j <= 0`；单候选 `1.0` + note；截断标 `truncated_to_top_n`。`attr` 的 `confidence` 不随 `--top` 变化。
3. **链深 3 已实测**（不再是"未实测"）：候选中位 **125** / 最小 **50** / 最大 **241**，链路数中位 **447** / 最大 **1654**，真答案入集 **57/57**、排第一 **30/57**。数字在 `bench/golden/attr.json` 的 `depth3` 块，是**小样本证据，不作阈值**。`data/README.md` §1.3.1、`bench/README.md`、`plan/01`、`plan/05`、`plan/00` 都已同步；**不得再写"链深 3 未实测"**。
4. **`attr` 人读输出经 `report.emit(..., human=...)`**：`attr.render(payload)` 返回稳定文本；CLI 先 `module.run` → 后 `emit`。新增子命令可按同模式提供 `render()`。
5. **候选链路是唯一中间表示**（`plan/02`）：`paths.Chain` 由 `attr` 产出（`candidates[*].path` / `path_string` / `depth`）；`explain` 只做逐步重放与对照，**不得重新枚举**（`plan/03` §四 / 一.3）。
6. **`paths.replay` / `verify_lossless` 已存在**（M1）：`explain` 复用它做每步重放；`step.as_dict()` 已有输入/输出文本与十六进制字段。
7. **`--pick` 从 1 起**；`attr` 的 `rank` 也是从 1 起。`explain --pick N` 越界 → 退出码 2（待 M3 实现）。
8. **序列化单点 = `report.dumps()` / `emit()`**；参数冻结 `sort_keys=True, ensure_ascii=False, indent=2` + LF + 结尾换行（K4）。
9. **退出码 0/1/2/3 语义单点**在 `data/README.md` §4.7；`report.py` 的 `EXIT_*` 与 README 引用它。`EXIT_NOT_READY=4` 常量**保留**到 `explain` / `recover` / `file` / `scan` 各自退役时（plan/03 一律删常量）。
10. **只读纪律**：`explain` 只读，不重算 `attr` 的候选，不落盘（除用户指定的 `--out` 之外）。
11. **CI 仍未实跑**：任何 DoD 只能写"本地等价校验，未接远端，CI 待首推验证"。
12. **环境事实**（2026-10-20 实测，会过期）：`python` 是商店占位符 → 用 `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`；Git Bash 打印 UTF-8 中文可能乱码，验收用解析器或 `py -3.12` 读。

## 三、下一棒待办（M3）

- [ ] 实现 `explain`：
  - CLI：`--text <s>`（与 `attr` 同规则：`--text` / `--file` 互斥；`--file` UTF-8 读取失败 → 退出码 2 提示 `file` 子命令）、`--pick <n>` 或 `--all`（二者必居其一）、`--vs <m>`（默认 top-2）、`--json`。
  - 处理：先跑一次只读 `attr` 取候选（不落盘）；按 `--pick`（1 起）或全部候选，对每条候选**逐步重放**（复用 `paths.replay` / `Step`），每步记录输入/输出文本与十六进制；独立复算断言 `output.encode(codec)` 或 `bytes.decode(codec)` == 本步记录。
  - 对照：`--vs m` 与 top-2 候选比较，输出第一处字节/链路**分叉点**；**只陈述差异，不判断哪个更好**。
  - 失败路径：`--pick` 越界 → 退出码 2；某步 `verify=false` → `status="verify_failed"` + `failed_step` 指向具体 step，退出码 1；`codec_unavailable` → 退出码 3。
- [ ] **退役 `explain` 的退出码 4**（常量分支 / CLI / 测试 / 文档四处同步）。
- [ ] 测试：独立重放脚本（不 import 工具内部状态）对 `verify` 全绿；故意改错一个 codec 名 → 该步 `verify=false` 且 `failed_step` 正确；`--pick` 越界 → 2；`--vs` 分叉点逐字节断言；双跑逐字节一致；非法参数零文件写入；codec 不可用（monkeypatch）→ 3。
- [ ] 用 `explain` 跑 `/` 冒烟 + 真链路证明（fixture `data/fixtures/explain/` 已存在）。
- [ ] 写 `plan/HANDOFF-M4.md`；M3 完成后回填 `plan/05` 状态表、`plan/00` 里程碑表、`README.md` 状态表（三处同提交）。
- [ ] 跑布局门 + 双解释器 pytest。

## 四、既定口径清单（K 编号，动了会打挂测试）

| 编号 | 约定 | 位置 |
|---|---|---|
| K1 | 输出 schema 固定 `mojibake-forensics/1`；字段只增不改 | `report.py`、`README.md` §字段 |
| K2 | `ENCODERS` / `DECODERS` / `MAX_DEPTH=3` 冻结（**解码器 7 个**） | `codecs_table.py`、`data/README.md` §4.1/§4.2 |
| K3 | 退出码 0/1/2/3 语义单点定义；M2 起 attr 不再返回 4，explain 亦然 | `report.py`、`data/README.md` §4.7 |
| K4 | JSON 序列化参数与 LF/尾换行冻结 | `report.py` |
| K5 | 无损性判据 = 逆序逐步重放，禁止 `errors='replace'` / `ignore` | `paths.py`、`data/README.md` §4.3 |
| K6 | 排序键 `(-score_total, depth, path_string)` | `score.py`、`data/README.md` §4.4 |
| K7 | 报告不含时间/主机名/绝对路径/Python 版本（bench 亦同） | `report.py`、`bench/run.py` |
| K8 | 状态副本三处一致；缺口表不提已 ✅ 里程碑 | `plan/00`、`plan/05`、`README.md`、`plan/06` |
| K9 | `scan` 命中判据 = 逐行；input `<0.5`、candidate `≥0.8`、gain `≥0.3` | `data/README.md` §4.8、`plan/03` §七 |

## 五、本机环境坑（实测 2026-10-20）

- `python` 是商店占位符 → 用 `py` / `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`。
- Git Bash 打印 UTF-8 中文可能显示乱码；验收文件用 `py -3.12` 读或解析器回读，不靠控制台肉眼。
- pytest 版本：3.8 → 7.4.4；3.12 → 8.4.2；两通道都可用，当前全绿。
- `bench/golden/attr.json` 约 114K+，3.8 / 3.12 逐字节一致；含 `depth3` 块。**不要手改**，口径变更用 `python bench/run.py --freeze` 重冻结。
- depth 3 候选规模已实测（中位 125 / 最大 241）；`attr` 默认 depth 3，快速。
- 本机事实会过期：引用前先复测并带日期。

## 六、DoD 逐项 checklist（M3）

- [ ] 独立重放：每条链路不 import 工具内部状态也能逐步 `verify` 全绿；改错 codec 名 → 该步 `failed_step` 精确。
- [ ] `--vs` 对照输出首处分叉点字节；只陈述差异。
- [ ] `--pick` 越界 / `--file` 读取失败 → 退出码 2 且零文件写入；codec 不可用 → 3。
- [ ] 双跑逐字节一致；输出无时间/主机名/绝对路径。
- [ ] explain 的退出码 4 退役（常量分支 / CLI / 测试 / 文档四处同步）。
- [ ] 布局门绿；`pytest -q` 双解释器绿。
- [ ] `plan/00` / `plan/05` / `README.md` 状态一致；写 `plan/HANDOFF-M4.md`。

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

# attr 冒烟（已完成）
py -3.12 -m mojibake_forensics attr --text "é›…" --json
py -3.12 -m mojibake_forensics attr --text "é›…" --top 1 --json
py -3.12 -m mojibake_forensics attr --text "abc" --json

# explain 冒烟（M3 起）
py -3.12 -m mojibake_forensics explain --text "é›…" --pick 1 --json
py -3.12 -m mojibake_forensics explain --text "é›…" --pick 1 --vs 2 --json

# fixture 重建 / 校验
for g in $(find data/fixtures -name gen.py | sort); do py -3.12 "$g" --check; done

# 环境事实复测
py -0p
```