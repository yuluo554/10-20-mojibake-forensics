# HANDOFF-M1 · 从骨架进入数据先行

> 上一棒：M0（题目定稿 + 方法论装订 + 可运行骨架）。本文件是 M1 的交接单；动手前先跑布局门。

## 一、当前进度 + 证据

- **M0 已完成（2026-10-20）**：
  - 题目与口径：`plan/00-README总览.md`、`plan/01-题目文档.md`、`data/README.md`。
  - 计划套件：`plan/02`–`06` 已落盘。
  - 方法论装订：`AGENTS.md`、`tools/check_sprint_layout.py`、`plan/00` 顶部装订行。
  - 可运行骨架：`pyproject.toml`、`src/mojibake_forensics/**`、`tests/**`、`bench/run.py`、`data/fixtures/**`。
- **证据位置**：`git log --oneline`；`python tools/check_sprint_layout.py`；`python -m pytest -q`；`forensics --help`。
- **当前所有子命令返回退出码 4（`not_ready`）**——这是骨架期语义，不是功能完成。

## 二、当前事实 · 状态不变量

> 下一棒动手前必须知道的事实与禁区；不读会踩的坑。

1. **数值口径唯一来源 = `data/README.md` §四**。`codecs_table.py` 的 `ENCODERS` / `DECODERS` / `MAX_DEPTH` 是代码侧冻结点；两处必须一致。改任一处要同提交改 `bench/run.py`、`plan/01` 摘录、`README.md`。
2. **候选集恒为列表**。即使只有一个候选也要包在 `candidates[]` 并带 `note="single_candidate_in_bounded_search"`；任何"已确定 / 正确编码是 / 修复成功"措辞都禁止。
3. **退出码 4 只属于骨架期**。M2–M5 落地时按"常量 → CLI → 测试 → 文档退出码表"四处同步退役；不得留下走不到的分支。
4. **序列化单点 = `report.py` 的 `dumps()` / `emit()`**。禁止各子命令自己 `json.dump`；参数冻结 `sort_keys=True, ensure_ascii=False, indent=2` + LF + 结尾换行。
5. **不可逆五类先判死，再判可还原**。`U+FFFD`、`锟斤拷`、`烫烫烫/屯屯屯`、`?` 截断、`errors='ignore'`；`verify` 失败必须降级 `LOST`，绝不输出未验证修复。
6. **只读纪律**：`file` / `scan` 只读打开；`recover` 只写 stdout/`--out`，永不覆盖输入。M5 之前不要写任何"原地修复"入口。
7. **布局门状态副本 = 3 处**：`plan/00` 里程碑表、`plan/05` 状态表、`README.md` 状态表。任一处翻转必须三处同提交改；`plan/06` 缺口表不得再提已 ✅ 里程碑（M0 已豁免）。
8. **`bench/out/` 不入仓**；`*.txt` 默认忽略，fixture 文本用 `.json`/`.md`。
9. **CI 尚未实跑**：任何 DoD 只能写"本地等价校验，未接远端，CI 待首推验证"。

## 三、下一棒待办（M1）

- [ ] 建 `data/fixtures/{attr,explain,recover,file,scan}/` 与 `gen.py` / `expect.json` / `README.md`。
- [ ] 五类不可逆各一例：`kun-jin-kao`、`tang-tang`、`question-mark`、`replacement-char`、`silent-drop`。
- [ ] 干净语料基线：只含统计与路径，`new == []`，不含原文。
- [ ] 实现 `bench/run.py` 的 57 例程序化生成与复算（链深 2；链深 3 标未实测）。
- [ ] `--check` 重生成逐字节一致；`expect.json` 无 `observed_*`。
- [ ] 补 `tests/test_fixtures.py`、`tests/test_bench.py`。
- [ ] 跑布局门 + 双解释器 pytest；写 `plan/HANDOFF-M2.md`。
- [ ] M1 完成后回填 `plan/05` 状态表、`plan/00` 里程碑表、`README.md` 状态表（三处同提交）。

## 四、既定口径清单（K 编号，动了会打挂测试）

| 编号 | 约定 | 位置 |
|---|---|---|
| K1 | 输出 schema 固定 `mojibake-forensics/1`；字段只增不改 | `report.py`、`README.md` §字段 |
| K2 | `ENCODERS` / `DECODERS` / `MAX_DEPTH=3` 冻结 | `codecs_table.py`、`data/README.md` §4.1/§4.2 |
| K3 | 退出码 0/1/2/3 语义单点定义；4 为骨架期临时码 | `report.py`、`data/README.md` §4.7 |
| K4 | JSON 序列化参数与 LF/尾换行冻结 | `report.py` |
| K5 | 无损性判据 = 逆序逐步重放，禁止 `errors='replace'` | `paths.py`、`data/README.md` §4.3 |
| K6 | 排序键 `(-score_total, depth, path_string)` | `score.py`、`data/README.md` §4.4 |
| K7 | 报告不含时间/主机名/绝对路径 | `report.py` |
| K8 | 状态副本三处一致；缺口表不提已 ✅ 里程碑 | `plan/00`、`plan/05`、`README.md`、`plan/06` |

## 五、本机环境坑（实测 2026-10-20）

- `python` 是商店占位符 → 用 `py` / `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`。
- Git Bash 打印 UTF-8 中文可能显示乱码；验收文件用 `py -3.12` 读或解析器回读，不靠控制台肉眼。
- pytest 版本：3.8 → 7.4.4；3.12 → 8.4.2；两通道都可用。
- Node 24.15 在，但布局门是 Python 实现，不依赖 Node。
- GitHub git 通道可能间歇阻断；`gh api` 通常可用（M6 才用）。
- 本机事实会过期：引用前先复测并带日期。

## 六、DoD 逐项 checklist（M1）

- [ ] `data/fixtures/**` 清单齐；`git ls-files` 可指认。
- [ ] 五类不可逆各一例，`expect.json` 含 `status` / `loss` / `input`。
- [ ] 干净基线 `new == []`，无原文。
- [ ] `gen.py --check` 逐字节一致（3.8 与 3.12）。
- [ ] `bench/run.py` 57 例可复算，真答案在候选集内 100%（若 M1 只做到基准口径，硬门可在 M2 复跑，但 M1 必须把探针生成器落地）。
- [ ] `pytest -q` 双解释器绿；布局门绿。
- [ ] `plan/00` / `plan/05` / `README.md` 状态一致。
- [ ] `plan/HANDOFF-M2.md` 已写。

## 七、关键命令速查

```bash
# 布局门（新对话第一件事）
python tools/check_sprint_layout.py

# 测试（双解释器）
py -3.8 -m pytest -q
py -3.12 -m pytest -q

# 骨架 CLI 冒烟
py -3.12 -m mojibake_forensics --help
py -3.12 -m mojibake_forensics attr --text "é›…" --json

# fixture 重建（M1 起）
python data/fixtures/<module>/gen.py --check

# 环境事实复测
py -0p
```
