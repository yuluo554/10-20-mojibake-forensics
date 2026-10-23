# data · 依据查证、数据源可获取性与数值口径

> 本文件是**数值口径的唯一权威**（§四）。`plan/01` 与代码里的表述均为便于阅读的摘录；若与 §四冲突，**以 §四为准**，并在同一提交内修正摘录。
>
> - **基准日**：2026-10-20
> - **下次复核**：`next_review: 2026-11-20` —— 覆盖 §1.1 基线工具星数（会随 GitHub 变化漂移）与 §1.4 检索式 `total_count`（会随索引变化漂移）两项。**复核是阅读动作，不是门禁**：本文件任何数值都不得转成代码断言阈值（见上条探针数字性质）。
> - **外部来源可达性**：本环境 **V2EX / 知乎 / Reddit 不可达**（sov2ex 503、v2ex 超时、reddit 403）——**未编造任何 V2EX / 知乎 / Reddit 链接**，中文痛点证据改用 GitHub issue + 中文仓库 README + HN 评论三类可直连来源。
> - **探针数字性质**：§一.3 的 57 例探针为**小样本自测的方法可行性证据，不是产品指标**；不得写进 README 首屏当卖点，不得作代码断言阈值（唯一例外是"真答案在候选集内 100%"作为 M2 的硬门——它是判据正确性的验证，不是性能指标）。

---

## 一、依据查证记录（三态：✅ 已核对原文 / ⬜ 软论据）

### 1.1 基线工具的覆盖与边界（✅ 已核对 README / 官方文档原文，基准日 2026-10-20）

| 编号 | 对象 | 星数 | 结论（原文要点） | 来源 |
|---|---|---|---|---|
| FTFY-DOC | ftfy 6.3.1 | 4068★ | 输入是**已解码的 `str`**；**明确弃权 CJK**："We also can't handle the legacy encodings used for Chinese, Japanese, and Korean, such as `shift-jis` and `gb18030`."；有 `fix_and_explain()` 但先验是"保守不动"，**不报候选集、不报置信度** | ftfy 官方文档 |
| UCHARDET | uchardet | 658★ | `bytes` → 编码名 | 项目 README |
| CHARDET | chardet | 2680★ | `bytes` → 编码名（自述 99.7% / 3138 files） | 项目 README |
| CHARSET-NORM | charset-normalizer | 803★ | `bytes` → 编码名 | 项目 README |
| CHARDETNG | chardetng | 130★ | `bytes` → 编码名 | 项目 README |
| CONFUSABLES | confusable_homoglyphs | 166★ | 形近字判定；**2024-01 已归档**，数据内嵌不随 Unicode 版本走 | 仓库元信息 |
| UNISEC | unicode-security（Rust） | 19★ | 只实现 UAX #39 计算，**无 CLI、无报告** | 项目 README |
| TROJAN | Trojan Source（论文库）/ anti-trojan-source | 1287★ / 90★ | 只覆盖 bidi | 仓库 |
| ICUSPOOF | ICU uspoof | 3618★ | 工业库，需自己写代码接 | ICU 文档 |

> 星数为**基准日快照**，会随时间漂移；引用时必须带基准日。

### 1.2 需求侧原话（✅ 逐条对照 URL，基准日 2026-10-20）

| 编号 | 类别 | 原话（节选，未改写） | 来源 |
|---|---|---|---|
| FTFY-34 | 中文 GBK 支持请求（2015） | "What'd be needed is an analysis of how GB\* encodings pushed through the CP1252 / Latin-1 sieve can be distinguished from UTF-8 Mojibakes and handled `fix_one_step_and_explain()`." | https://github.com/rspeer/python-ftfy/issues/34 |
| FTFY-166 | 一手案例：ftfy 解不动 | 用户贴 `é›…é›…`，`fix_encoding()` 原样不动；手写 `encode("cp1252").decode("utf8")` 才得到 `雅雅` | https://github.com/rspeer/python-ftfy/issues/166 |
| HN-33053918-a | 日文 zip 乱码常态 | "I still regularly see mojibake from Japanese ZIP files."（lifthrasiir） | https://news.ycombinator.com/item?id=33053918 |
| HN-33053918-b | 找不到工具 | "Is there software for detection of Mojibake or fixing it where it occurs? (other than ftfy mentioned in another comment)"（pabs3） | 同上 |
| HN-33053918-c | 至今无法修复 | "Most of the mojibaké I do see appears when staff at the Japanese university where I teach send around zipped folders of files with Japanese names... I haven't yet found a way to repair them."（tkgally） | 同上 |
| CN-TABLE | 中文只能人肉查表 | `justjavac/unicode-encoding-error-table`（**256★**）是**人工**归纳六类（古文码 / 口字码 / 符号码 / 拼音码 / 问句码 / 锟拷码）的速查表 | https://github.com/justjavac/unicode-encoding-error-table |
| CN-ISSUE | 中文 issue 直问 | "中文注释显示乱码，请问采用的是哪种编码方式？" | https://github.com/zhaohaojie1998/Grey-Wolf-Optimizer-for-Path-Planning/issues/7 |
| CN-WEEKLY | 同行自承做不到 | "自动检测仅覆盖有效 UTF-8 和带 BOM 的 UTF-16，其他编码需手选，避免假装能可靠猜出所有编码。"（阮一峰周刊 #11560） | https://github.com/ruanyf/weekly/issues/11560 |

### 1.3 本地探针实测（✅ 本机实测；**小样本自测，非产品指标**）

一次性脚本（不入仓成品）的口径：**10 个编码器 × 7 个解码器、链深 2、10 个中/日/韩样本 × 8 个真实事故场景 = 57 例**。

> 口径更正（M1，2026-10-20）：出题期的一次性脚本描述写的是"6 个解码器"，但代码侧冻结集合 `DECODERS` 实际是 7 个（`utf-8` / `gb18030` / `big5` / `shift_jis` / `euc-kr` / `cp1252` / `latin-1`，见 §4.1）。M1 的 `bench/run.py` 按代码集合复算为 7；57 例形状来自 10 样本 × 8 场景，不受解码器个数影响。

| 指标 | 实测值 | 用途 |
|---|---|---|
| 候选集规模 | 中位数 **4**、均值 **4.5**、最大 **11** | 证明候选集**有界**，可完整输出 |
| 唯一无损解 | **0 / 57（0%）** | **证伪"唯一解"叙事** → 产品立场改为"有界候选 + 可验证证明" |
| 真答案落在候选集内 | **57 / 57（100%）** | 证明无损性判据可靠 → M2 的硬门 |
| 真答案排第一（粗打分） | 45 / 57（79%） | 说明打分只是排序辅助 |
| 真答案排第一（加"浅层优先"） | 53 / 57（93%） | 说明排序永远不完美 |

> **不得**把上面任何数字写成 README 卖点、代码常量、阈值或断言（唯一允许的断言是"真答案在候选集内 100%"这一**判据正确性**门槛，见 §四.3）。
> 探针链深为 **2**；首期 M1 枚举上限设为 **链深 3**。**链深 3 已于 M2 由 `attr` 实测**（见 §1.3.1 末行）：候选规模显著扩张（中位 125 / 最大 241），真答案仍 100% 在集内；数字只作可行性证据，不外推。

#### 1.3.1 M1 可复算复跑（`bench/run.py`，2026-10-20）

> §1.3 的数字来自**未入仓的一次性脚本**，无法逐字节复现；M1 把探针实现落到 `bench/run.py`，冻结 `bench/golden/attr.json`，`--check` 重算逐字节一致（3.8 与 3.12 双通道通过）。**M1 起以本表为准**；§1.3 保留为历史记录。

| 指标 | 可复算值 | 说明 |
|---|---|---|
| 用例数 | **57 / 57 可用** | 10 样本 × 8 场景 = 80 组合；严格编解码失败、文本无变化、真值链不可验证的 23 例不计 |
| 候选集规模（minimal = depth 1 最小无损恢复，按结果文本去重） | 中位 **7.0**、均值 **6.421053**、最大 **10** | 与 §1.3 的 4 / 4.5 / 11 同量级；**不锁具体数字** |
| 候选集规模（expanded = depth ≤ 2，按结果文本去重） | 中位 **33.0**、均值 **33.385965**、最大 **57** | 深度 2 扩张较大；产品只展示 top-N，`total_candidates` 报完整数 |
| 唯一无损解 | **0 / 57** | 定性结论与 §1.3 一致 |
| 真答案落在候选集内 | **57 / 57**（minimal 与 expanded 均 100%） | M2 硬门 |
| 真答案排第一（固定排序键，minimal） | **34 / 57（59.6%）** | 排序只是辅助；不承诺第一 |
| 真答案排第一（固定排序键，expanded） | **30 / 57（52.6%）** | 同上 |
| 链深 3（`attr` 实测，2026-10-20 / M2） | 候选中位 **125**、均值 **121.754386**、最小 **50**、最大 **241**；链路数中位 **447**、最大 **1654**；真答案入集 **57/57**；真答案排第一 **30/57** | 由 `bench/run.py` 的 `depth3` 块调用真实 `attr` 测得，**同源可复算**；仍是小样本证据，不作产品指标 |

> **与 §1.3 的差异如实登记**：一次性脚本的 4 / 4.5 / 11 与 79% / 93% 无法从入仓代码复现（脚本未存档，候选集定义也未冻结）。M1 冻结的定义是：候选 = 逐字节逆序验证通过、结果不等于输入的无损链；minimal 只取 depth 1，expanded 取 depth ≤ 2，均按结果文本去重并保留最浅 / 字典序最小的代表链。**定性结论不变**：多解是常态、真答案不漏、排序不完美。

### 1.4 开源空白检索（⬜ 软论据：`gh api` 检索式 + total_count，基准日 2026-10-20）

| 检索式 | total_count | 头部 / 有效头部 |
|---|---|---|
| `mojibake` | 271 | python-ftfy 4068★ |
| `mojibake fixer` | 45 | ftfy |
| `mojibake recovery` | 4 | 头部 3★ |
| `mojibake detect` | 11 | text-encoding-guard 44★ |
| `mojibake explain` | **1** | luanma **1★**（2026-10-19 创建） |
| **`mojibake attribution`** | **0** | — |
| **`character encoding diagnosis`** | **0** | — |
| **`utf-8 read as gbk`** | **0** | — |
| `gbk mojibake` | 9 | 头部 3★ |
| `chinese encoding repair` | 2 | 44★ |
| `encoding repair` | 103 | 44★ |
| `encoding forensics` | 77 | 头部 26★ |
| `garbled encoding diagnose` | 1 | 0★ |
| **`text garble scanner`** | **0** | — |
| `乱码` | 1104 | llcom 1254（串口工具附带功能）/ unicode-encoding-error-table 256 |
| `encoding detection` | 2076 | charlock_holmes 1082 |

**结论（⬜ 软论据，不是市场调查）**：归因层（已解坏的 `str` → 哪一步转坏）在 CJK 侧无人做；"归因结果可验证 + 多解并列"这一组合也没有工具做。
**但必须如实写**：`mojibake explain` 已有 1 个 1★ 项目（2026-10-19 创建），所以**不得宣称首创 explain**。差异只能落在四条：不承诺唯一解 / 多解并列 / 不可逆判死 / 证明可复算。
**禁止措辞**：本仓库任何文档不得写"首创""空白""无人做过"。

---

## 二、数据源可获取性记录

| 数据源 | 三态 | 获取方式 | 备注 / 阻断原因 |
|---|---|---|---|
| Python 标准库编解码器（`codecs` / `encodings`） | ✅ 已获取（随解释器冻结） | `python -c "import encodings; ..."` | 本题**唯一必需数据源**；不同 Python 版本的同名 codec 行为可能有细微差异 → 报告头写 `python_version` |
| CJK 编码名清单（`gb18030` / `gbk` / `big5` / `shift_jis` / `euc-jp` / `euc-kr`） | ✅ 已获取 | 标准库 `codecs.lookup()` 逐个探测 | 不可用者在启动时显式报 `codec_unavailable`，不静默跳过 |
| 需求侧原话（ftfy issue × 2、HN × 3、中文仓库 × 3） | ✅ 已获取 | 直接打开链接核对，原话照抄 | 链接若失效，按"原话已存档于本文件"处理，**不重新编造** |
| GitHub 检索 total_count | ✅ 已获取（一次性快照） | `gh api` 检索接口 | 基准日 2026-10-20；数字会漂移，属 ⬜ 软论据 |
| 中文词频表（可选语言先验） | ⬜ 未获取 | 需自备；默认关闭 | **许可边界**：只接受可再分发的词表（如 CC-BY / 公共领域）；**不把任何第三方词表原文入仓**，只允许用户用 `--freq <path>` 本地加载；许可不可再分发者一律不入仓、不写进默认路径 |
| 干净中文文本语料（误报基线用） | ✅ 已构造（M1 使用自写合成短句；未采集公开文本原文） | 本地构造 | 基线文件只含统计与相对路径；**不含语料原文**（见 §三）；如后续接入公开文本，仍只提统计 |
| V2EX / 知乎 / Reddit | ❌ **不可达** | — | sov2ex 503、v2ex 超时、reddit 403；**未编造任何此类链接** |
| 真实用户乱码样本 | ⬜ 不入仓 | 不采集 | 样本常含客户数据（发票 / 病历 / 合同）；fixture 全部程序化合成 |

---

## 三、合成数据纪律

- **全部 fixture 为程序化构造**，不含任何真实公司、产品、人员、客户数据。
- **构造方式**：先取一段**合成原文**（自行编写的示例文本，或公开文本的极小片段且已改写），按固定链路 `原文 → encode(A) → decode(B)` 生成乱码串；**真值 = 原文**，登记在 `expect.json`。生成过程必须可由脚本复现（固定编码器名、固定链路、固定文本）。
- **五类不可逆样本**（M4 必测）：
  1. `锟斤拷`：由 `EF BF BD`（U+FFFD）重复序列被 GBK 解码得到；
  2. `烫烫烫` / `屯屯屯`：由 `0xCC` / `0xCD` 填充字节被 GBK 解码得到（断言工具判 `NOT_MOJIBAKE`）；
  3. `?` 截断：目标编码无映射字符 → 编码器写入 `?`；
  4. `U+FFFD`：非法字节序列被 decode 替换；
  5. `errors='ignore'` 静默丢失：编码/解码时丢弃不可映射字符。
- **干净语料基线**：M1 使用**自写合成干净短句**（不采集公开文本原文）；如后续接入公开文本，仍**只提取统计**（字符类别分布、编码可解码性），**不把原文或长片段入仓**；基线文件登记"抽样来源类别 + 抽样规模量级 + 期望命中数 0"，不登记原文。
- **不入仓的白名单占位**（文档与 fixture 中可出现，作为明显的假值）：
  - 域名：`example.invalid`、`example.com`（仅文档示例）；
  - 邮箱：`fixture@example.invalid`；
  - 人名/机构：`合成样本`、`synthcorp`；
  - 编码样本里的"原文"一律使用自编短句（如 `乱码尸检`、`日本語のテスト`、`한국어 테스트`）。
- **不得引入真实文号、真实日期事件、真实指标**：fixture 里的任何数值均为构造常量并在 `expect.json` 登记。
- **反例必须有**：干净文本 fixture 必须断言"0 报告 0 改动"，防止工具靠"见非 ASCII 就报"骗过验收。
- **可重建性判据**：同一生成脚本在任意机器（不同路径/时区）重跑，`expect.json` 逐字节一致；`--check` 模式用于 CI。

---

## 四、数值口径（单点定义，全项目唯一权威）

> 本节八项口径**只在此处定义**。`plan/01`、`plan/02`–`06`、代码常量、README 一律引用本节，不得另立第二套。

### 4.1 编码器集合（`ENCODERS`）与解码器集合（`DECODERS`）

首期冻结为：

```
ENCODERS  = ("utf-8", "gb18030", "gbk", "big5", "shift_jis", "euc-jp", "euc-kr",
             "cp1252", "latin-1", "cp437")
DECODERS  = ("utf-8", "gb18030", "big5", "shift_jis", "euc-kr",
             "cp1252", "latin-1")
```

- 说明：`ENCODERS` 中的 `cp1252` / `latin-1` / `cp437` 是**通道**（还原时常用"错的那一步"），`DECODERS` 少 `cp437`（无 UTF-8 标志的 zip 名才用，归 M4）。
- 集合的变更属于**口径变更**：必须同时改本节、`codecs_table.py`、`bench/run.py` 的探针口径，并重跑基准；**不得只改代码**。
- 任一 codec 在当前解释器不可用 → 启动即报 `codec_unavailable` + 退出码 3，**不静默跳过**（静默跳过会让候选集悄悄缩水，正是本工具要审计的毛病）。

### 4.2 链路与链深

- 链路 = `encode` / `decode` 交替的序列，**从 `encode` 开始，以 `decode` 结束**（输入是已解坏的 `str`：要回到字节，必须先在某个编码下 encode）。
- **链深 `depth` = 链中 `decode` 的步数**（探针口径：一次错误的 decode 记深度 1；`encode→decode` 记为 1 步）。
- **首期上限 `MAX_DEPTH = 3`**。超过上限不枚举；若输入在 ≤3 内无任何无损候选，输出 `status="no_candidate"` + `notes=["depth_limit_reached"]`，**退出码 1**，不静默返回空列表当成功。
- 深度 3 的候选规模**已由 M2 的 `attr` 实测**（`bench/golden/attr.json` 的 `depth3` 块：候选中位 125 / 最大 241，真答案入集 57/57）。数字属小样本证据，不作阈值；`--top` 只影响展示，`total_candidates` 始终报完整数。

### 4.3 无损性硬过滤（候选集的唯一入口）

对候选链 `t0 --enc(e1)--> b1 --dec(d1)--> t1 --enc(e2)--> ... --dec(dk)--> tk`：

```
无损 ⇔ tk.encode(dk) == b_k            # 最后一步的编码器必须能把结果还原成该步的字节
且   对每一步 i:  b_i == 前一步产出的字节   # 链路自身是构造出来的，恒成立
```

实现上取**最强判据**：把 `tk` 按链路**逆序**重走一遍（`encode(dk) → decode(e_k) ...`），要求逐步字节与原文完全相等。
**不满足者直接淘汰**，不使用 `errors='replace'` 做"能解就行"的近似——近似正是误报的来源。

**候选集完整性门槛（M2 硬门）**：57 例探针样本中，真答案必须**全部**落在候选集内（目标 100%）。这是**判据正确性**的验证，不是性能指标。

### 4.4 三层打分与排序

```
score = W_READ * readability + W_DEPTH * depth_score + W_LANG * language_score
W_READ  = 1.0
W_DEPTH = 0.5
W_LANG  = 0.3      # 仅当 --freq 提供了词频表时生效；默认 0（关闭）
```

- **`readability`**（逐字符累加，再按长度归一化到 `[-1, 1]`）：

  | 字符类别 | 分值 |
  |---|---|
  | ASCII 可见（`0x20–0x7E`）+ 常规空白 | +0.2 |
  | CJK 统一表意文字（`U+4E00–U+9FFF`）/ 假名 / 谚文 | +1.0 |
  | 拉丁扩展（`U+00A0–U+024F`） | +0.1 |
  | 半角片假名（`U+FF61–U+FF9F`） | −0.5 |
  | 制表控制字符（`U+0009` 之外的控制码 `U+0000–U+001F`、`U+007F`） | −1.0 |
  | PUA（`U+E000–U+F8FF`）、代理项、非字符 | −1.0 |
  | `U+FFFD`（替换符） | −1.5 |
  | 其它 | 0 |

  > 归一化后再 clamp 到 `[-1, 1]`：`U+FFFD` 的 −1.5 是**逐字符权重**，纯替换符串的最终值落在 −1.0。

- **`depth_score`** = `1 / (1 + depth)`（浅层优先）。一次性脚本显示这一项把"真答案排第一"从 79% 提到 93%（M1 可复算复跑见 §1.3.1；固定排序键下实际为 34/57 minimal、30/57 expanded），但**永远不保证第一**。
- **`language_score`**：常用字比例（需 `--freq`）；默认 0。词频表**不入仓**，许可边界见 §二。
- **排序键（写死）**：`(-score_total, depth, path_string)`。`path_string` 为链路序列化成 `"encode:cp1252>decode:utf-8"` 的字符串，保证并列时顺序确定。

### 4.5 置信度口径

**候选之间**的相对置信度，不是概率：

```
confidence_i = score_i / Σ_j score_j        （仅对 status=candidates 的候选计算）
区间          = [confidence_i_lower, confidence_i_upper]
confidence_i_lower = confidence_i / (1 + spread)
confidence_i_upper = min(1.0, confidence_i * (1 + spread))
spread = 0.05 * (n_candidates - 1)           # 候选越多，区间越宽
```

- 若 `n_candidates == 1`：`confidence = 1.0`，但输出仍标明 `note="single_candidate_in_bounded_search"`（**不是"确定"**，只是在给定集合与链深内的唯一候选）。
- 若所有候选 `score_total <= 0`：不归一化，`confidence = null`，`note="no_positive_score"`——**不伪造分布**。实现取等价守卫 `Σ score_j <= 0`（非正分母下归一化无定义，同样返回 `null`，不造数）。
- 归一化分母 = **完整候选集**（`collapse_by_result` 之后、`--top` 截断之前）的总分；截断只影响展示，`confidence` 不随 `--top` 变化。
- `--top` 截断时，被展示候选若无更高优先级 note，则标 `note="truncated_to_top_n"`（提示"后面还有候选"，不是质量判断）。
- **禁止表述**：`confidence=1.0` 之外的任何"已确定 / 正确编码是 / 修复成功"。

### 4.6 误改率为零的判定（M5 门禁）

- **误改（false positive）的定义**：`scan` 在**干净语料基线**覆盖的文件上报告了任何一条 `new` 命中。
- **门槛**：干净语料基线的 `new` 命中数**必须为 0**，且**不得改动任何文件**（`scan` 全程只读，文件 mtime/内容前后一致）。
- 基线命中（`baselined`）与新增（`new`）分开计数：基线内旧账不计失败；**新增任何一条 → 退出码 1**。
- 基线文件里指向已不存在文件的条目 → `stale`，只提示，不参与退出码。
- 基线 JSON 只含：文件相对路径、该文件允许的命中类别（默认空 = 必须 0）、抽样来源类别、抽样规模量级。**不含语料原文。**
- **基线根约定（唯一）**：基线里的 `path`、报告里的命中 `path`、以及 `stale` 的存在性检查，全部相对**基线文件自身所在目录**（下称「基线根」）。`--dir` 只决定这次走哪棵子树，不改变路径基准。
  - 例：`data/fixtures/scan/clean-corpus.json` 的基线根是 `data/fixtures/scan`，因此 `--dir .../clean` 扫出的路径仍是 `clean/en-01.md`，`--dir .../polluted` 仍是 `polluted/ja.md`。
  - 这样一份基线可同时服务同一棵树下的多个子树；`stale` 也不会因为把 `--dir` 收窄而整片变红（旧行会把相对路径算错，见 `expect.json` 的 `stale` 期望）。
  - `scan_directory()` 作为纯函数，`root` 参数缺省为 `--dir`；命令行路径一律传基线根。

### 4.7 退出码（五个子命令共用）

| 码 | 含义 | 适用 |
|---|---|---|
| 0 | 成功，且无"需要人处理"的结论 | `attr` 有候选；`recover` 为 `RECOVERED`；`file` / `explain` 正常；`scan` 无新增 |
| 1 | 成功执行，但结论需要人处理 | `attr` 为 `no_candidate` / `depth_limit_reached`；`recover` 为 `LOST`；`scan` 有新增命中 |
| 2 | 用法 / 输入错误（不可解析的参数、**`--dir` 不存在或不是目录**、**`--baseline` 文件不存在**、基线 JSON 语法错误、`--pick` 越界） | 全部；**不得留下任何输出文件** |
| 3 | 环境不满足（codec 不可用、Python 版本低于下限、必需的标准库模块缺失） | 全部；**不降级猜测** |

- 退出码语义**只在此处定义**；`report.py` 的 `EXIT_*` 常量与 README 的说明均引用本节。
- 退出码 4（`EXIT_NOT_READY`）曾是**骨架期临时码**，M5 起 `file` / `scan` 落地后全面子命令退役，**常量已删除**——退出码只有 0/1/2/3 四组。
- `scan` 的 JSON 输出必须**先写后定退出码**（CI 需要报告），但退出码 2 的路径禁止产出文件（坏输入不留痕）。

### 4.8 `scan` 命中判据（M5 实现，M1 基线依赖）

- **检测单元 = 逐文件、逐非空行**；一次命中定位到「相对路径 + 行号 + 候选集」。空行跳过。
- 命中 ⇔ 同时满足：
  1. `readability(line) < 0.5`；
  2. 存在无损候选（depth ≤ `MAX_DEPTH`，§4.3）满足 `readability(result) ≥ 0.8`；
  3. `readability(result) - readability(line) ≥ 0.3`。
- 只读：`scan` 不修改任何文件；命中不触发 `recover`。
- 干净语料基线（§4.6）按本判据登记 `expected_new = []`；阈值变更必须重跑干净基线并回填本节。
- 已知边界：该判据是**误报防线**，不是"更准的检测器"；`readability` 无法区分"通顺 CJK"与"看起来像 CJK 的深层乱码"，所以只把提升幅度作为必要条件，不承诺命中即真相。

---

## 五、口径变更纪律

- 改 §4.1–§4.8 任一项 → 同一次提交内更新：本文件、`src/mojibake_forensics/` 对应常量、`bench/run.py` 的探针口径、`plan/01` 的摘录、`README.md` 的字段说明。
- 改了权重或集合，**必须重跑 57 例探针并回填 §1.3.1**；数字变化不影响"小样本自测"的定性标注。
- 口径变更必须在 `plan/00` 决策记录表新增一行（日期 + 改了什么 + 为什么）。
