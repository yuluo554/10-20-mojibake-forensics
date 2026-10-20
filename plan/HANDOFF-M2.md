# HANDOFF-M2 · 从数据先行进入 attr 归因

> 上一棒：M1（fixture 生成器 + 五类不可逆样例 + 干净基线 + 可复算 57 例探针）。本文件是 M2 的交接单；动手前先跑布局门。

## 一、当前进度 + 证据

- **M1 已完成（2026-10-20）**：
  - 引擎：`paths.enumerate_chains` / `verify_lossless` / `collapse_by_result` 与 `score.readability` / `rank` 已落地（M2 直接复用，不再另写第二套）。
  - 基准：`bench/run.py` 生成 57 例；`bench/golden/attr.json` 冻结；`--check` 在 3.8 / 3.12 双通道逐字节一致。
  - fixture：12 个 `gen.py`（`attr` / `explain` / `recover` × 5 / `file` × 4 / `scan`），全部 `--check` 通过；五类不可逆 `expect.json` 齐；干净基线 `expected_new=[]`；file 四件字节已冻结。
  - 测试：新增 `tests/test_bench.py`、`tests/test_fixtures.py`、`tests/test_score.py`；双解释器全绿。
  - 文档：`data/README.md` §1.3.1（可复算探针）、§4.8（`scan` 命中判据）；三处状态副本已翻 M1。
- **证据位置**：
  - `py tools/check_sprint_layout.py` → 全绿。
  - `py -3.8 -m pytest -q` / `py -3.12 -m pytest -q` → 全绿。
  - `py -3.12 bench/run.py --check` → `golden matches`。
  - `for g in $(find data/fixtures -name gen.py); do py -3.12 "$g" --check; done` → 全 PASS。
  - `git log --oneline`。
- **当前所有子命令仍返回退出码 4（`not_ready`）**——M1 只做数据与基准，不是功能完成。

## 二、当前事实 · 状态不变量

> 下一棒动手前必须知道的事实与禁区；不读会踩的坑。

1. **枚举引擎已存在**：`paths.enumerate_chains` 只扩展“无损、非恒等”的前缀；`verify_lossless` 逆序逐步比对；`collapse_by_result` 对每个结果文本保留最浅 / 字典序最小的代表链。M2 的 `attr` 必须复用它，不得再写一套枚举。
2. **打分已存在**：`score.readability` 按 §4.4 逐字符累加后按长度归一化并 clamp 到 `[-1, 1]`；`score.rank` 使用冻结排序键 `(-score_total, depth, path_string)`。**置信度尚未实现**，是 M2 的活。
3. **57 例探针已可复算**（`data/README.md` §1.3.1）：minimal（depth 1，按结果去重）中位 **7** / 最大 **10**；expanded（depth ≤ 2）中位 **33** / 最大 **57**；唯一解 **0/57**；真答案入集 **57/57**（minimal 与 expanded）；真答案排第一 **34/57**（minimal）/ **30/57**（expanded）。§1.3 的 4 / 4.5 / 11 与 79% / 93% 是一次性脚本的历史记录，**不复算**。
4. **解码器是 7 个，不是 6 个**：`codecs_table.DECODERS` 冻结 7 个；文档已更正。任何新数字按 7 复算。
5. **depth 3 未实测于 57 例探针**。M1 在 scan fixture 上侧测到：两行短乱码在 depth ≤ 3 下分别产生 **148 / 232** 个不同结果（未入探针，不作产品指标）。M2 默认 `MAX_DEPTH=3`，必须先测耗时与规模，再决定 `--top` 展示策略；**不得把 depth 2 的数字外推到 3**。
6. **候选恒为列表**：`attr` 永远返回 `candidates[]`；单候选也带 `note="single_candidate_in_bounded_search"`；禁止“已确定 / 正确编码是 / 修复成功”。
7. **退出码 4 只退役 attr 这一块**：M2 让 `attr` 返回 0/1/2/3；`explain` / `recover` / `file` / `scan` 仍返回 4，`EXIT_NOT_READY` 常量保留到 M5。
8. **序列化单点 = `report.dumps()` / `emit()`**：`attr` 不得自己 `json.dump`；参数冻结 `sort_keys=True, ensure_ascii=False, indent=2` + LF + 结尾换行。
9. **不可逆五类先判死**（M4）：`attr` 不负责 `recover`，但不得把 `锟斤拷` / `烫烫烫` / `?` / `U+FFFD` / 静默丢失形态包装成“可恢复候选”。
10. **只读纪律**：`attr` 只读；`--file` 按 UTF-8 读，读不了 → 退出码 2 并提示用 `file` 子命令；`--text` 与 `--file` 互斥。
11. **`scan` 命中判据已定义**（`data/README.md` §4.8）：逐文件逐非空行；`readability(line) < 0.5` 且存在候选 `readability(result) ≥ 0.8` 且提升 `≥ 0.3`。M5 实现；M2 不要改阈值。
12. **干净基线只含统计 + 路径**；fixture 文本用 `.md` / `.json`；file 的 `.zip` / `.bin` 已在 `.gitattributes` 标 `binary`，不要改 `ZIP_STORED` / 固定时间戳 / `create_system=0`。
13. **CI 仍未实跑**：任何 DoD 只能写“本地等价校验，未接远端，CI 待首推验证”。

## 三、下一棒待办（M2）

- [ ] 实现 `attr.run` / `attr.attribute`：
  - 校验 codec；`--source-enc` / `--target-enc` 只能收缩冻结集合，非法名或扩张尝试 → 退出码 2。
  - `--text` / `--file` 互斥；`--file` UTF-8 读取失败 → 退出码 2（提示 `file` 子命令）。
  - `--top` 默认 5、必须 ≥ 1；`--freq` 目前未实现 → 明确报“二期可选”，不得伪造语言先验。
  - 调 `paths.enumerate_chains(max_depth=codecs_table.MAX_DEPTH)` → `collapse_by_result` → `score.rank`。
  - 无候选 → `status="no_candidate"` + `notes=["depth_limit_reached"]`，退出码 1；**不返回空列表冒充成功**。
  - 候选 envelope：`rank` / `path` / `path_string` / `depth` / `score{readability,depth,language,total}` / `confidence{lower,upper}` / `note`；`total_candidates` = 不同结果数，`total_chains` = 链路数（新增字段必须同步 `README.md` 与 `plan/03`）。
  - 置信度按 `data/README.md` §4.5：全部 `score_total <= 0` → `confidence=null` + `note="no_positive_score"`；单候选 `confidence=1.0` + note；截断只影响展示，`total_candidates` 始终报完整数。
- [ ] **退役 attr 的退出码 4**：常量分支、CLI、测试、README 退出码表、`plan/03` 四处同步；不得留下走不到的分支。
- [ ] 测试：候选恒为列表；`--top 1`；`no_candidate`；`--source-enc` / `--target-enc` 非法与扩张；codec 不可用（monkeypatch）→ 3；双跑逐字节一致；非法参数零文件写入。
- [ ] 用 `attr` 跑 57 例硬门（真答案入集 100%），输出 `bench/out/attr.json`；若数字与 §1.3.1 不同，同提交回填。
- [ ] 写 `plan/HANDOFF-M3.md`；M2 完成后回填 `plan/05` 状态表、`plan/00` 里程碑表、`README.md` 状态表（三处同提交）。
- [ ] 跑布局门 + 双解释器 pytest。

## 四、既定口径清单（K 编号，动了会打挂测试）

| 编号 | 约定 | 位置 |
|---|---|---|
| K1 | 输出 schema 固定 `mojibake-forensics/1`；字段只增不改 | `report.py`、`README.md` §字段 |
| K2 | `ENCODERS` / `DECODERS` / `MAX_DEPTH=3` 冻结（**解码器 7 个**） | `codecs_table.py`、`data/README.md` §4.1/§4.2 |
| K3 | 退出码 0/1/2/3 语义单点定义；M2 起 attr 不再返回 4 | `report.py`、`data/README.md` §4.7 |
| K4 | JSON 序列化参数与 LF/尾换行冻结 | `report.py` |
| K5 | 无损性判据 = 逆序逐步重放，禁止 `errors='replace'` / `ignore` | `paths.py`、`data/README.md` §4.3 |
| K6 | 排序键 `(-score_total, depth, path_string)` | `score.py`、`data/README.md` §4.4 |
| K7 | 报告不含时间/主机名/绝对路径/Python 版本（bench 亦同） | `report.py`、`bench/run.py` |
| K8 | 状态副本三处一致；缺口表不提已 ✅ 里程碑 | `plan/00`、`plan/05`、`README.md`、`plan/06` |
| K9 | `scan` 命中判据 = 逐行；input `<0.5`、candidate `≥0.8`、gain `≥0.3` | `data/README.md` §4.8、`plan/03` §七 |

## 五、本机环境坑（实测 2026-10-20）

- `python` 是商店占位符 → 用 `py` / `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`。
- Git Bash 打印 UTF-8 中文可能显示乱码；验收文件用 `py -3.12` 读或解析器回读，不靠控制台肉眼。
- pytest 版本：3.8 → 7.4.4；3.12 → 8.4.2；两通道都可用，当前 71 项全绿。
- `bench/golden/attr.json` 约 114K，3.8 / 3.12 逐字节一致；**不要手改**，口径变更用 `python bench/run.py --freeze` 重冻结。
- file 的 zip fixture 字节在 3.8 / 3.12 一致；不要改 `ZIP_STORED`、时间戳 `(1980,1,1,0,0,0)`、`create_system=0`。
- depth 3 在短句上可到 148 / 232 个结果；`attr` 默认 depth 3，先测耗时/规模，再定 `--top`。
- 本机事实会过期：引用前先复测并带日期。

## 六、DoD 逐项 checklist（M2）

- [ ] 候选枚举 + 无损性硬过滤落地（复用 `paths`，失败边直接丢弃，不 `errors='replace'`）。
- [ ] 三层打分与排序键落地；置信度区间可复算（§4.5）。
- [ ] 真答案在候选集内 100%（57 例）；候选有界；`bench/out/attr.json` 记录规模分布。
- [ ] 双跑逐字节一致；`--top 1` 仍为列表并带 note。
- [ ] 退出码 0/1/2/3 全覆盖；无候选返回 `no_candidate` + `depth_limit_reached`。
- [ ] attr 的退出码 4 退役（常量分支 / CLI / 测试 / 文档四处同步）。
- [ ] 布局门绿；`pytest -q` 双解释器绿。
- [ ] `plan/00` / `plan/05` / `README.md` 状态一致；写 `plan/HANDOFF-M3.md`。

## 七、关键命令速查

```bash
# 布局门（新对话第一件事）
python tools/check_sprint_layout.py

# 测试（双解释器）
py -3.8 -m pytest -q
py -3.12 -m pytest -q

# 57 例探针
py -3.12 bench/run.py --check
py -3.12 bench/run.py --out bench/out/attr.json

# fixture 重建 / 校验
for g in $(find data/fixtures -name gen.py | sort); do py -3.12 "$g" --check; done

# attr 冒烟（M2 起）
py -3.12 -m mojibake_forensics attr --text "é›…" --json
py -3.12 -m mojibake_forensics attr --text "é›…" --top 1 --json

# 环境事实复测
py -0p
```
