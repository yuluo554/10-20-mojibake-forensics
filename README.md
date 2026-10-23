# Mojibake Forensics · 乱码尸检

> 版本：`0.1.1` · [Release](https://github.com/yuluo554/10-20-mojibake-forensics/releases/tag/v0.1.1) · 纯本地 Python CLI · 零网络 · 零模型 · 标准库编码表

**乱码尸检**回答的问题不是"这段字节是什么编码"，而是：**手里这个已经解坏的 `str`，是被哪一步 `encode` / `decode` 转坏的？还能不能回去？哪一步不可逆？**

输出恒为**有界候选集 + 每一步的字节证明 + 不可逆判定**，**永不假装猜出唯一答案**。这是与"自动修乱码"工具的产品立场差异：多解是常态，证据比自信重要。

> 当前状态：**M6.1 补丁版发布完成**（`v0.1.1` tag + Release 附手工源码包；五个子命令全部落地：`attr` 有界候选 + `explain` 逐步字节证明与对照 + `recover` 确定性还原与不可逆判死 + `file` 原始字节管道 + `scan` CI 门禁）。退出码只有 0/1/2/3 四组，**不会伪造候选或修复结果**。

## 项目状态

| 里程碑 | 状态 | 说明 |
|---|---|---|
| M0 | ✅ 已完成（2026-10-20） | 题目定稿 + 方法论装订 + 可运行骨架 |
| M1 | ✅ 已完成（2026-10-20） | 数据先行：fixture 生成器 + 五类不可逆样例 + 干净基线 + 可复算 57 例探针 |
| M2 | ✅ 已完成（2026-10-20） | `attr`：候选枚举 + 无损性过滤 + 三层打分 + 置信度区间；57 例硬门 57/57 |
| M3 | ✅ 已完成（2026-10-20） | `explain`：逐步字节证明 + 独立复算 + 对照分叉点 |
| M4 | ✅ 已完成（2026-10-20） | `recover`：确定性还原 + 不可逆判死 |
| M5 | ✅ 已完成（2026-10-20） | `file` 原始字节管道 + `scan` CI 门禁 |
| M6 | ✅ 已完成（2026-10-20，`v0.1.0`） | GitHub 发布：`v0.1.0` tag + Release 附产物 + 发布留档（`plan/RELEASE-M6.md`） |
| M6.1 | ✅ 已完成（2026-10-23，`v0.1.1`） | 补丁版：`scan` 坏路径报 2、基线根单一定义、`expect.json` 活判据、CI v7 + 脱敏门入 CI、Linux 语义测试全绿（`plan/RELEASE-M6.1.md`） |

## 为什么需要它

- **检测器**（chardet / uchardet / charset-normalizer / chardetng）回答的是 `bytes → 编码名`；它们不回答"已解坏的 `str` 是哪一步转坏的"。
- **修复器**（ftfy）处理已解码 `str`，但其官方文档明确把 CJK 遗留编码排除在外；且不报候选集、不报"哪一步丢了字节"。
- 中文侧常见做法仍是人肉查表（如 `unicode-encoding-error-table` 的六类归纳）。

本工具把中间那一层补上：**候选集 + 字节证明 + 不可逆判定**。`mojibake explain` 类工具已经存在；本项目的差异只在上述四条产品承诺，不在"谁先做 explain"上做任何主张。

## 安装

需要 Python ≥ 3.8，运行时**零第三方依赖**。

```bash
python -m pip install .
forensics --help
```

开发环境：

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

> Windows 本机 `python` 可能是商店占位符，请用 `py` / `py -3.8` / `py -3.12`；中文输出建议 `py -X utf8`。

## 五个子命令（接口已定，引擎按里程碑落地）

```text
forensics attr    --text <s> [--file <path>] [--source-enc ...] [--target-enc ...] [--top N] [--json]
forensics explain --text <s> (--pick N | --all) [--vs M] [--json]
forensics recover --text <s> --pick N [--out <path>] [--json]
forensics file    --path <path> [--preset csv-excel-win|zip-names|utf16] [--json]
forensics scan    --dir <path> --baseline <clean-corpus.json> [--format json|human]
```

### 四个目标场景（M2–M5 完成后可复现）

```bash
# 1) 归因：已解坏的 str → 有界候选 + 置信度区间
forensics attr --text "é›…é›…"

# 2) 证明：每一步 encode/decode 的字节转储 + 复算断言 + 与 top-2 的分叉点
forensics explain --text "é›…é›…" --pick 1 --vs 2

# 3) 判死：不可逆类只报 LOST + 丢失点，不猜字
forensics recover --text "锟斤拷" --pick 1

# 4) CI 门禁：干净语料零报告（退出码 0）；污染语料有新增（退出码 1）
forensics scan --dir data/fixtures/scan/clean --baseline data/fixtures/scan/clean-corpus.json --format json
forensics scan --dir data/fixtures/scan/polluted --baseline data/fixtures/scan/clean-corpus.json --format json
#    报告里的路径相对「基线文件所在目录」，所以分别是 clean/… 与 polluted/…（data/README.md §4.6）
#    目录写错（如 cleen）→ 退出码 2，不会静默报成功
```

> 五个子命令全部可直接运行（链深上限 3；`--top` 只影响展示）：`attr` 自 M2、`explain` 自 M3、`recover` 自 M4、`file` / `scan` 自 M5 起。`file` 与 `scan` 全程只读。

### `file` 原始字节管道与 `scan` 门禁（M5）

- `file --path <path> [--preset ...]`：只读诊断。分节报告 `bom`（含 `bom_conflict`）/ `utf16_misalignment`（奇字节数 + 错位一字节证据，不自动改）/ `zip_names`（`flag_bits & 0x800` 判 UTF-8，无标志时列 CP437 与 UTF-8 两种解释，工具不选择）/ `csv_candidates`（`cp1252` / `gbk` / `shift_jis` + 分隔符嗅探）。文件不存在 → 退出码 2；全程不解压成员内容、不改输入。
- `scan --dir --baseline`：逐文件、逐非空行命中判据（`data/README.md` §4.8：`readability(line)<0.5` + 候选 `≥0.8` + gain `≥0.3`）；命中分类 `new` / `baselined` / `stale`（基线指向已不存在文件 → `stale`，不影响退出码）；**基线根 = 基线文件所在目录**，`--dir` 只收窄走哪棵子树，报告路径因此保留 `clean/` / `polluted/` 前缀（§4.6）；JSON 先写后定退出码：无 `new` → 0，有 `new` → 1，坏输入（含 `--dir` 不存在或不是目录）→ 2 且**不产出任何文件**；全程只读，干净语料基线零报告零改动。

### `recover` 判定（M4）

- **判定顺序固定**（`plan/03` §5.2）：先判不可逆五类——`U+FFFD` → `LOST(reason=replacement_char)` + 偏移；`锟斤拷` → `LOST(reason=kun_jin_kao)` + `EF BF BD` 重复位置；`烫烫烫`/`屯屯屯` → `NOT_MOJIBAKE(reason=msvc_fill)`；`?` → `LOST(reason=encode_truncated)` + 偏移；`silent_drop` 只在有出处证据时可判，CLI 面不伪造。判死后不再重放。
- **`RECOVERED` 必过 verify**：按 `--pick` 取 `attr.search` 已排序候选，复用 explain 的逐步重放（不重新枚举）；失败降级 `LOST(reason=verify_failed)`，**绝不输出未经验证的修复**。
- `--pick` 必填（缺省 → 退出码 2，提示先跑 `attr`）；越界 → 退出码 2；`--out` 与 `--file` 输入同路径 → 退出码 2；**永不覆盖输入**。
- `LOST` / `NOT_MOJIBAKE` 输出 `loss`（`step` / `offset` / `replaced_with` / `cause`），输出不含工具自造字符。

### `attr` 输出字段（M2）

```json
{
  "status": "candidates",
  "total_candidates": 323,
  "total_chains": 888,
  "candidates": [
    {"rank": 1, "result": "雅", "path": [...], "path_string": "encode:cp1252>decode:utf-8",
     "depth": 1,
     "score": {"readability": 1.0, "depth": 0.5, "language": 0.0, "total": 1.25},
     "confidence": {"lower": 0.0005, "upper": 0.1491},
     "note": "truncated_to_top_n"}
  ]
}
```

- `candidates` **恒为列表**，按冻结排序键 `(-score_total, depth, path_string)` 排序；`--top` 只截断展示。
- `total_candidates` = 不同结果文本数；`total_chains` = 通过无损性硬过滤的链路数。两者**始终报完整数**，不受 `--top` 影响。
- `confidence` 是候选**之间**的相对份额区间（`data/README.md` §4.5），不是概率；全部候选 `score_total <= 0` 时为 `null` + `note="no_positive_score"`；单候选为 `1.0` + `note="single_candidate_in_bounded_search"`。
- `status="no_candidate"` 时 `candidates=[]` + `notes=["depth_limit_reached"]`，退出码 1——**不返回空列表冒充成功**。

### `explain` 输出字段（M3）

```json
{
  "status": "ok",
  "mode": "pick",
  "pick": 1,
  "total_candidates": 323,
  "total_chains": 888,
  "proofs": [
    {
      "rank": 1,
      "result": "雅",
      "path": [...],
      "path_string": "encode:cp1252>decode:utf-8",
      "depth": 1,
      "steps": [
        {"index": 1, "op": "encode", "codec": "cp1252", "input": "é›…", "output_hex": "E9 9B 85", "verify": true},
        {"index": 2, "op": "decode", "codec": "utf-8", "input_hex": "E9 9B 85", "output": "雅", "verify": true}
      ],
      "verify": true,
      "failed_step": null,
      "output": "雅",
      "divergence": {"vs_rank": 2, "kind": "step", "at_step": 2, "statement": "step 2: op/codec differs: decode:utf-8 vs decode:latin-1", ...}
    }
  ]
}
```

- `explain` 只读：先跑一次只读 `attr` 搜索（不落盘），再对选中的候选**逐步重放**；每步把"重放得到的输入/输出"与链路记录比对，第一个不一致处停在 `failed_step`（1 起）。它**不重新枚举**候选。
- 每步 `verify` 独立复算：`output.encode(codec)` / `bytes.decode(codec)` 必须与该步记录一致；失败步带 `failure`（`reason` + 字节/字符偏移）。
- `verify` 全绿 → `status="ok"`（退出码 0）；任一步失败 → `status="verify_failed"`（退出码 1），`failed_step` 指向具体步。
- `divergence` 只陈述与对照候选（`--vs m`，缺省为 top-2 中的另一条；仅 `--pick` 模式提供）的**第一处差异**：步/字节/字符偏移与两侧值，**不判断哪个更好**。候选不足两条时 `notes=["no_second_candidate"]`。
- `--pick N` 越界（`pick_out_of_range`）与 `--vs` 越界（`vs_out_of_range`）都是退出码 2；`--all` 输出全部候选证明（无对照）。
- 证明可被独立脚本重放：`tests/independent_replay.py` 只用标准库与报告自身的 `path` / `steps` 字段复算每一步（不 import 工具内部状态）。

## 输出与退出码

- 人读：稳定文本，无颜色、无时间戳。
- 机读：`--json` 输出规范 JSON（键排序、UTF-8 不转义、LF、结尾换行）。
- 每次输出都带 `criteria`（编码器/解码器集合与链深上限），提醒读者：候选是**给定集合与链深下的全部无损可能**，不等于事实真相。

| 退出码 | 含义 |
|---|---|
| 0 | 成功，且无"需要人处理"的结论 |
| 1 | 成功执行，但结论需要人处理（`no_candidate` / `LOST` / `scan` 有新增） |
| 2 | 用法 / 输入错误（参数、文件不存在、基线 JSON 语法错误、`--pick` 越界） |
| 3 | 环境不满足（codec 不可用、Python 版本过低、标准库模块缺失） |

退出码语义唯一权威：`data/README.md` §4.7；代码常量在 `src/mojibake_forensics/report.py`。

## 已知边界

- **不承诺唯一解**：候选恒为列表，置信度恒为区间。文档、输出、README 三处表述一致。
- **链深上限 3**：探针深度为 2，M2 实测在链深 3 候选中位数 **125**、最大 **241**（57 例）；超过上限报 `depth_limit_reached`，不静默截断。
- **CJK 优先**：首期覆盖 `gb18030` / `gbk` / `big5` / `shift_jis` / `euc-jp` / `euc-kr`，西文 `cp1252` / `latin-1` / `cp437` 作为通道参与；不做全量代码页覆盖。
- **不做原地修复 / 批量改名**：本工具是尸检，不是整容；`file` / `scan` 全程只读，`recover` 只写 stdout 或 `--out`，永不覆盖输入。
- **不做云分析 / 上传 / 遥测**：纯本地、零网络；报告不写绝对路径、主机名、用户名。
- **词频语言先验默认关闭**：二期可选；`--freq` 当前**明确报错**（`freq_not_implemented`，退出码 2），不静默忽略、不伪造语言先验；第三方词表原文不入仓。
- **不重做 charset 检测器**：检测器回答的是另一个问题；本工具只在内部复用标准库 codec。
- **不可逆五类不猜字**：`U+FFFD`、`锟斤拷`、`烫烫烫/屯屯屯`、`?` 截断、`errors='ignore'` 静默丢失 → `LOST` / `NOT_MOJIBAKE` + 丢失点。

## 开发与验证

```bash
python tools/check_sprint_layout.py       # 方法论布局门（新对话第一件事）
python tools/check_layout_mutations.py    # 布局门变异验证（临时目录，不动工作树）
python tools/check_release.py --pre-tag   # 发布门（M6 前骨架）
python tools/check_desensitize.py         # 脱敏门（须在 git 工作树内跑；解包树里会因无 .git 而非零退出）
python -m pytest -q                      # 单元与常驻测试
python bench/run.py                      # 57 例探针 → bench/out/attr.json
python bench/run.py --check              # 与 bench/golden/attr.json 逐字节比对
```

项目布局：

```text
src/mojibake_forensics/   CLI + 判定层 + 核心层 + 口径层
data/README.md            依据查证、数据源、数值口径（唯一权威）
data/fixtures/            attr / explain / recover / file / scan
bench/                    57 例探针（产物 bench/out/ 不入仓）
plan/                     00–06 计划、HANDOFF、发布留档
tools/                    布局门、变异验证、发布门
tests/                    单元 + 常驻守门
```

## 数值口径

编码器/解码器集合、链深、无损性判据、三层打分、置信度、误改率为零、退出码、`scan` 命中判据——**八项只在 `data/README.md` §四定义一次**。任何改动必须同一次提交同步代码、基准、计划摘录与 README。

## 方法论

本仓库遵循 `ai-tool-project-sprint` 方法论（装订日期 2026-10-20）；入口见 `AGENTS.md`。任何新对话先跑 `python tools/check_sprint_layout.py`。

## 许可证

MIT（见 `LICENSE`）。许可证最终选择登记在 `plan/06` 待拍板决策 P1。
