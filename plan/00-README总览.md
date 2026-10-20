# 00 · README 总览 — 10-20-mojibake-forensics（乱码尸检）

> 方法论：`ai-tool-project-sprint`（装订 2026-10-20）｜布局门：`python tools/check_sprint_layout.py`｜续接对话第一件事 = 跑它

- **性质**：不参赛项目题 · 发布 GitHub **公开仓库** · 署名 yuluo554
- **定位宣言**："ftfy 官方文档明确把 CJK 编码排除在外；检测器（chardet / uchardet / charset-normalizer）只回答'这是什么编码'，不回答'**已经解坏的 str 是被哪一步转坏的**'。本工具做乱码尸检：输出**有界候选集 + 每一步 encode/decode 的字节证明 + 哪一步不可逆**，**永不假装猜出唯一答案**——这是与所有'自动修乱码'工具的立场差异。"
- **交付形态**：**纯本地 Python CLI**（标准库编码表，零外部数据、零网络、无模型）。唯一形态，不设备选。
- **发布**：GitHub 公开仓库，v0.1.0（**tag + Release 附产物 + 发布留档**三件套）。
- **查证基准日**：2026-10-20。
- **状态**：M0 / M1 / M2 / M3 / M4 / M5 完成（题目定稿 + 方法论装订 + 可运行骨架 + 数据先行 + `attr` 归因 + `explain` 证明 + `recover` 判定 + `file` 管道与 `scan` 门禁）；M6 发布中（tag 前准备）。

## 文档索引表

| 文档 | 内容 | 状态 |
|---|---|---|
| `plan/00-README总览.md` | 本文档：索引 / 决策记录 / 弃选项 / 承诺-证据台账 / 提交材料实物表 / 里程碑 | ✅ v1 |
| `plan/01-题目文档.md` | 十段式题目定稿（定位宣言、需求原话、探针实测、五模块、评分、含金量锚点、边界与非目标、招牌动词表） | ✅ v1 |
| `data/README.md` | 依据查证记录（三态 + 基准日 + 不可达来源如实说明）/ 数据源可获取性 / 合成数据纪律 / 数值口径（唯一权威） | ✅ v1 |
| `.gitignore` | Python 标准模板 + 语料目录 + `bench/out/` | ✅ v1 |
| `plan/02-架构与技术选型.md` | 分层架构、编解码表冻结方式、退出码契约、选型与弃选 | ✅ v1 |
| `plan/03-模块详设.md` | 五子命令接口、数据结构、处理顺序、失败路径、测试点 | ✅ v1 |
| `plan/04-数据计划.md` | fixture 生成器确定性纪律、五类不可逆样例、干净语料基线、bench | ✅ v1 |
| `plan/05-里程碑与发布.md` | 可演示物、出口门、环境事实、风险预案、已知未验证项 | ✅ v1 |
| `plan/06-交付对标与决策.md` | 题面 §二/§三逐条落位、待拍板决策、风险登记、缺口、发布前检查清单 | ✅ v1 |
| `plan/HANDOFF-M1.md` | M0 → M1 交接单（七节，含当前事实·状态不变量） | ✅ v1 |
| `plan/HANDOFF-M2.md` | M1 → M2 交接单（七节，含当前事实·状态不变量） | ✅ v1 |
| `plan/HANDOFF-M3.md` | M2 → M3 交接单（七节，含当前事实·状态不变量） | ✅ v1 |
| `plan/HANDOFF-M4.md` | M3 → M4 交接单（七节，含当前事实·状态不变量） | ✅ v1 |
| `plan/HANDOFF-M5.md` | M4 → M5 交接单（七节，含当前事实·状态不变量） | ✅ v1 |
| `plan/HANDOFF-M6.md` | M5 → M6 交接单（七节，含当前事实·状态不变量） | ✅ v1 |
| `plan/RELEASE-M6.md` | 发布留档（tag 时点事实 / tag 后追加事实分栏） | 🟡 tag 前事实已落盘 |

> 索引状态列随里程碑同步翻转；不得在一处标 ✅ 而在另一处标 ⬜。

## 决策记录表

> 本表同时登记已定案决策与**弃选项**（含弃选理由），后续里程碑不再重复论证。
> **前四条是本题的产品地基，不得在后续文档中被改弱。**

| 日期 | 决策 | 结论与理由 |
|---|---|---|
| 2026-10-20 | **① "唯一解"叙事已被自测数据证伪（0/57）——必须改为"有界候选 + 可验证证明"** | 57 例探针里**没有任何一例存在唯一无损解**（0%，中位候选 4、均值 4.5、最大 11；一次性脚本，M1 复算见本表末行），而真答案落在候选集内 **57/57（100%）**。这不是实现缺陷，是**信息论层面的多解性**：同一个乱码串可以由多条 encode/decode 链无损产生。因此：输出恒为**列表**、置信度恒为**区间**、文档与 CLI 输出中**禁止**"已确定 / 正确编码是 / 修复成功"这类断言。**这是产品立场，不是缺陷**——任何声称唯一解的工具，在 CJK 侧都在骗人。 |
| 2026-10-20 | **② 不可逆类（`锟斤拷` / `烫烫烫` / `?` 截断 / `U+FFFD` / `errors='ignore'` 静默丢失）必须判死，不能猜** | 这五类**字节已经丢了**，任何"修"都是编造字符。工具必须输出 `LOST` + **丢失点定位**（哪一步、哪个偏移、被替换成什么），并断言输出中**不含任何工具自造字符**。猜字的代价远高于"承认丢了"——用户会把 `锟斤拷` 抄进生产数据。另注：`烫烫烫`/`屯屯屯` 是 MSVC Debug 的 `0xCC`/`0xCD` 栈填充值，**根本不是乱码**，必须归到"非编码事故"而不是"修复失败"。 |
| 2026-10-20 | **③ 打分表与误报防线是主要工作量** | 候选集靠无损性硬过滤已能 100% 不漏（探针 57/57），**剩下的全部难度在排序与降噪**：粗打分真答案排第一 79%，加"浅层优先"后 93%（一次性脚本数字；M1 可复算复跑见本表末行：34/57 minimal、30/57 expanded）——即排序永远不完美。因此：①三层打分权重**只在 `data/README.md` §四定义一次**；②排序键 `(-score, depth, path_string)` 写死以保证双跑一致；③`scan` 的误报防线是**干净语料零报告基线**，不是"模型更准"。这两块（score.py + 干净语料基线）是首期工时大头。 |
| 2026-10-20 | **④ 竞品 `luanma` 1★（2026-10-19 创建）已在做 explain——差异必须落在四条上** | 检索 `mojibake explain` 只有 1 个 1★ 项目。**不得宣称首创 explain**。本题差异只能落在：**不承诺唯一解**（候选集 + 置信度区间）、**多解并列**（逐字节对照"为什么不是另一个"）、**不可逆判死**（五类直接判丢失、不猜字）、**证明可复算**（每条路径可被独立脚本重放）。四条之外的任何"更准/更聪明"表述都不得写进 README 或题面。 |
| 2026-10-20 | **探针数字只作方法可行性证据，不作产品指标** | 57 例、0/57、57/57、79%、93% 全部为**小样本自测**，只可出现在 `plan/01` §1.4 与 `data/README.md` §四，**不得进 README 首屏当卖点、不得作代码断言阈值**。探针链深为 2；首期 M1 上限设链深 3，**深度 3 的候选集扩张与排序效果 ⬜ 未实测**（如实登记，不推算）。 |
| 2026-10-20 | **数值口径单点定义在 `data/README.md` §四** | 编码器集合 / 解码器集合 / 链深上限 / 打分权重 / 置信度归一化 / 误改率为零判定 / 退出码 / `scan` 命中判据，八项一处定义；plan 与代码只可引用。理由：本项目的结论对小改动（多加一个解码器、改一个权重）非常敏感，两处口径必然漂移。 |
| 2026-10-20 | **中文侧证据改用 GitHub issue + 中文仓库 README + HN 评论** | 本环境 V2EX / 知乎 / Reddit **不可达**（sov2ex 503、v2ex 超时、reddit 403）。如实记录不可达，**不编造 V2EX 链接**；改用三类可直连来源（ftfy issue #34/#166、`justjavac/unicode-encoding-error-table` 256★、`Grey-Wolf-Optimizer` issue #7、阮一峰周刊 #11560、HN 33053918）。 |
| 2026-10-20 | 弃选："Unicode 安全扫描（bidi / 同形异义 / 不可见字符）作为首期模块" | `anti-trojan-source` 90★ + eslint 插件 80★ + bidichk 42★ + glassworm-hunter 30★ 已覆盖 bidi，且 Aikido / CrowdStrike 已产品化；做它是在红海里重做一遍，还会冲淡"乱码归因"这一窄缝。降级为二期扩展项 D-2。 |
| 2026-10-20 | 弃选："通用 homoglyph / IDN 库" | dnstwist 5761★ / codebox-homoglyph 638★ / decancer 131★ 已商品化；中文形近表需自建，`confusables.txt` 里 CJK 源项仅 410 条，数据工程超一周，且与"归因"主线无关。 |
| 2026-10-20 | 弃选："重做 charset 检测器" | chardet 2680★ / charset-normalizer 803★ / uchardet 658★ / chardetng 130★ 是红海；且检测器回答的是**另一个问题**（`bytes → 编码名`）。本题只在内部需要字节候选时复用标准库编解码器，不发布检测 API。 |
| 2026-10-20 | 弃选："把 zip / CSV 小工具独立成题" | 检索到的 4 个 0★ 同类项目已把这类工具的天花板演示完（`garbled encoding diagnose` 1 个 0★、`mojibake recovery` 头部 3★ 等）；独立成题没有增量。**降级为 M4 的一个模块**（原始字节管道），服务"字符串归因 + 原始字节"两条入口。 |
| 2026-10-20 | 弃选："同构克隆 `luanma`" | 1★ 项目已做 explain；照抄等于把 1★ 的定位复制一遍，且与"永不假装唯一解"的立场冲突（多数 explain 工具的目标是"给出答案"）。本题保留 explain 形态但改目标为**证明 + 对照**。 |
| 2026-10-20 | 弃选："原地修复 / 自动批量重命名文件" | 会破坏原始证据，使复算失去意义；且改名不可撤销。`recover` 只写 stdout / `--out`，`file` / `scan` 全程只读。 |
| 2026-10-20 | 弃选："云分析 / 上传样本 / 遥测" | 隐私红线：纯本地零网络。乱码样本常含真实客户数据（发票、病历、合同），上传即事故。 |
| 2026-10-20 | **方法论装订落地（M0 第零步）** | 装订三件：`AGENTS.md` 锚点 + `tools/check_sprint_layout.py` 布局门 + 本文件顶部装订行；另配 `tools/check_layout_mutations.py` 做逐判据变异验证。判据只落仓库内文件，不读 git 元数据。 |
| 2026-10-20 | **骨架期退出码 4（`EXIT_NOT_READY`）** | M0 只交付可安装骨架，五个子命令返回 `status="not_ready"` + 退出码 4，**不伪造空结果**。M2–M5 对应模块落地时按"常量 → CLI → 测试 → 文档退出码表"四处同步退役。退出码 0/1/2/3 语义不因骨架改变。 |
| 2026-10-20 | 许可证默认 **MIT**（待用户拍板） | 记入 `plan/06` 待拍板决策 P1；用户确认后再写入 `plan/00` 定案行。默认值用于让仓库具备可上传形态，不代表最终法律选择。 |
| 2026-10-20 | 形态定案：纯 CLI，单一形态 | 输出是规范 JSON + 人类可读的证明文本，接 CI 与本地终端；不做 GUI / 桌面 / Web 服务，避免空壳形态与额外分发负担。 |
| 2026-10-20 | 首期范围：CJK 优先，链深 ≤ 3 | 编码器 / 解码器集合见 `data/README.md` §四；深度 3 效果未实测，超限报 `depth_limit` 而不是静默截断。 |
| 2026-10-20 | **M2 `attr` 落地：置信度口径补全 + 链深 3 实测 + attr 退出码 4 退役** | ①置信度归一化分母固定为**完整候选集**（`collapse_by_result` 之后、`--top` 之前），`--top` 不改变 `confidence`；守卫取 `Σ score_j <= 0`（与"全部 ≤ 0"等价且覆盖非正分母），返回 `null` + `note="no_positive_score"`。②`--top` 截断时被展示候选标 `note="truncated_to_top_n"`（提示"后面还有"，不是质量判断）。③**链深 3 首次实测**（`attr` 跑同 57 例）：候选中位 **125** / 最小 **50** / 最大 **241**，链路数中位 **447** / 最大 **1654**，真答案入集 **57/57**、排第一 **30/57**；数字进 `bench/golden/attr.json` 的 `depth3` 块，只作小样本证据，不作阈值。④`--freq` 明确报 `freq_not_implemented`（退出码 2），不伪造语言先验。⑤`attr` 不再返回退出码 4（常量保留给 M3–M5 的其余子命令）。 |
| 2026-10-20 | **M3 `explain` 落地：证明 + 对照 + 退出码 4 退役（explain）** | ①`explain` 不重新枚举：复用 `attr.search` 的已排序候选（`Chain` 仍是唯一中间表示，`plan/02` 口径不破）。②逐步重放每步独立复算：记录的输入/输出与重放状态比对，第一处不一致停在 `failed_step`（1 起），`failure` 带 `reason` + 偏移。③`status="ok"`（verify 全绿）/ `"verify_failed"`（任一步失败，退出码 1）/ `"no_candidate"`（退出码 1，不伪造证明）。④`--vs` 缺省取 top-2 中的另一条（pick 1↔2，其余取 1）；`divergence` 只陈述第一处差异（`kind=step|bytes|text|depth|none`），**不判断优劣**；候选不足两条 → `no_second_candidate`。⑤`--pick`/`--vs` 越界 → 退出码 2（`pick_out_of_range`/`vs_out_of_range`）；`--all` 与 `--vs` 互斥。⑥独立重放脚本 `tests/independent_replay.py`：只用标准库 + 报告自身字段复算，不 import 工具内部状态。⑦`explain` 不再返回退出码 4（常量保留给 `recover`/`file`/`scan`）。 |
| 2026-10-20 | **M4 `recover` 落地：确定性还原 + 不可逆判死 + 退出码 4 退役（recover）** | ①判定顺序固定（`plan/03` §5.2）：先判不可逆五类——`U+FFFD` → `LOST(replacement_char)` + 偏移；`锟斤拷` → `LOST(kun_jin_kao)` + `EF BF BD` 重复位置；`烫烫烫`/`屯屯屯` → `NOT_MOJIBAKE(msvc_fill)`；`?` → `LOST(encode_truncated)` + 偏移；判死后不再重放。②`silent_drop` 只在有出处证据（原文对照）时可判，CLI 面只有已解坏的 str → 不伪造该判定（fixture `requires_provenance` 口径一致）。③`RECOVERED` 必过 verify：按 `--pick` 取 `attr.search` 已排序候选（不重新枚举），复用 explain 的 `replay_chain` 逐步双向比对；失败降级 `LOST(verify_failed)`，绝不输出未经验证的修复。④`--pick` 必填（缺省 → 退出码 2 `missing_pick`）；越界 → 退出码 2 `pick_out_of_range`；`--out` 与 `--file` 输入同路径 → 退出码 2 `out_overwrites_input`；永不覆盖输入。⑤`recover` 不再返回退出码 4（常量保留给 `file`/`scan`，M5 结束前删）。⑥`no_candidate` → `LOST(reason=no_candidate)` + `depth_limit_reached`，不猜字。 |
| 2026-10-20 | **M5 `file` + `scan` 落地：退出码 4 全面退役（常量删除）** | ①`file` 只读二进制诊断：BOM 嗅探（UTF-8/16LE/16BE/32 先后）+ `bom_conflict` 证据分节、UTF-16 奇字节数 + 错位一字节证据（`shifted_text`，不自动改）、zip 中央目录名（`flag_bits & 0x800` 判 UTF-8；无标志列 CP437/UTF-8 双解释，工具不选择；不解压成员）、`--preset csv-excel-win` 报 cp1252/gbk/shift_jis 可解码性 + 分隔符嗅探；文件不存在退出码 2。②`scan` 命中判据 = K9（`readability(line)<0.5` + 候选 `≥0.8` + gain `≥0.3`），候选走 `attr.search` 不重新枚举；分桶 new/baselined/stale；坏基线退出码 2 零产出；全程只读，干净语料 0 报告 0 改动。③**`EXIT_NOT_READY` 常量删除**：常量 / CLI / 测试 / 文档四处同步，退出码只剩 0/1/2/3。④新增 `tests/test_file.py`、`tests/test_scan.py` 各 12 条；双解释器全绿；bench `--check` 逐字节一致。 |
| 2026-10-20 | **M6 发布：默认值执行 + 手工源码包 + 先验后 tag** | 用户未另行表态，按 `plan/06` P1/P2/P7 默认值执行：许可证 MIT（`LICENSE` 已落）、仓库公开、附件为手工源码包（`git archive` + `gzip -9n` + `SHA256SUMS`）。发布顺序固定为「测试绿 → 版本号 0.1.0 → 源码包 → 干净环境验证 → tag → Release → 校验和」；tag 后事实回填 `plan/RELEASE-M6.md` 第二栏并另起提交，tag 对象不追写。CI 无远端期间只写“本地等价校验，未接远端，CI 待首推验证”，首推后据实回填 run id。 |
| 2026-10-20 | **M1 探针落地与数字复核（一次性脚本 → 可复算基准）** | 出题前的一次性脚本未入仓，`bench/run.py` 成为唯一可复算实现并冻结 `bench/golden/attr.json`。复跑：minimal（depth 1，按结果去重）候选中位 **7** / 均值 **6.421053** / 最大 **10**；expanded（depth ≤ 2）中位 **33** / 最大 **57**；唯一解 **0/57**；真答案入集 **57/57**（minimal 与 expanded 均 100%）；真答案排第一 **34/57（minimal）/ 30/57（expanded）**。`data/README.md` §1.3 的 4 / 4.5 / 11 与 79% / 93% 保留为历史记录，不再作为可复算口径。**定性结论不变**：多解是常态、真答案不漏、排序不完美。另更正：出题期描述"6 个解码器"与冻结 `DECODERS`（7 个）不一致，M1 按代码集合复算。 |

## 弃选项汇总（速查）

| 弃选项 | 一句话理由 | 去向 |
|---|---|---|
| Unicode 安全扫描 | 已被 4 个工具 + 2 家商业产品覆盖 | 二期扩展 D-2 |
| 通用 homoglyph / IDN 库 | 已商品化，中文形近表数据工程超一周 | 不做 |
| charset 检测器 | 红海，回答的是另一个问题 | 不做（内部复用标准库） |
| zip/CSV 独立成题 | 4 个 0★ 项目已演示天花板 | 降级为 M4 |
| 克隆 `luanma` | 1★ 已占位，照抄无增量 | 改为"证明 + 对照" |
| 原地修复 / 批量改名 | 破坏证据、不可撤销 | 永不进判定路径 |
| 云 / 上传 / 遥测 | 隐私红线 | 永不 |

## 承诺-证据台账

> 全项目只此一份；其他文档只可引用，不得复制。状态列随里程碑同步翻转。

| 承诺项 | 素材来源 | 交付物内可达性 | 核验方式 | 状态 |
|---|---|---|---|---|
| 有界候选集（不漏真答案） | 无损性硬过滤 `t2.encode(decoder) == bytes`（✅ 探针 57/57） | `forensics attr` 的 `candidates[*]` | `bench/run.py` 57 例：真答案在候选集内 100%（硬门） | ✅ M2 `attr` 复跑 57/57（链深 3 亦 57/57） |
| 候选集有界（不是全枚举倾泻） | 可复算探针：minimal 中位 7 / 最大 10；expanded 最大 57；depth 3 中位 125 / 最大 241（✅ 小样本自测） | `attr` 的 `--top` 与候选计数 | `bench/out/attr.json` 记录规模分布；**不锁具体数字**，只锁"有界 + 双跑一致" | ✅ M2 展示策略落地（`--top` 默认 5，`total_candidates` 报完整数） |
| 置信度区间（非伪概率） | §4.5 归一化口径 | `attr` 的 `candidates[*].confidence` | 区间上下界与分项分可复算；文档/输出/README 三处禁止"已确定"表述 | ✅ M2 落地（`tests/test_attr.py`） |
| 三层打分与浅层优先 | 探针：排序永远不完美（复算 34/57 minimal） | `attr` 的 `score.{readability,depth,language}` | 分项分与排序键 `(-score, depth, path_string)` 的固定性测试 | ✅ M2 完整落地（打分 + 置信度 + CLI） |
| 字节级证明路径 | Python 标准库编解码器（✅ 冻结） | `forensics explain --pick n` | 独立重放脚本对每步 `verify` 全绿；改错 codec 名 → 指向具体 step | ✅ M3 落地（`tests/independent_replay.py` + `tests/test_explain.py`） |
| 多解对照（为什么不是另一个） | 候选集结构（✅） | `explain --vs k` 的分叉点比较 | 分叉点字节逐字节断言 | ✅ M3 落地（`divergence` 五类 kind；只陈述差异） |
| 不可逆五类判死 | 标准库字节语义（✅） | `forensics recover` 的 `LOST` + 丢失点 | 五类各一条单测；断言输出不含工具自造字符 | ✅ M4 落地（`tests/test_recover.py`） |
| `锟斤拷` 归因 | `EF BF BD` 重复被 GBK 读回（✅ 可本地复现） | `recover` 的丢失点定位 | fixture `recover/kun-jin-kao` golden | ✅ M4 落地（`LOST(kun_jin_kao)` + offset/repeat） |
| `烫烫烫/屯屯屯` 非乱码判定 | MSVC `0xCC`/`0xCD` 栈填充（✅ 可本地复现） | `recover` 的 `NOT_MOJIBAKE` | fixture `recover/tang-tang` golden | ✅ M4 落地（`NOT_MOJIBAKE(msvc_fill)`） |
| BOM / UTF-16 奇偶错位诊断 | 标准库 + 合成 fixture（✅） | `forensics file --path` | 三类管道 fixture golden 逐字节一致 | ✅ M5 落地（`tests/test_file.py`） |
| zip 文件名归因（`0x800` + CP437 对照） | zip 规范 `flag_bits & 0x800`（✅） | `file` 的 `zip_names` | 带/不带标志两个 fixture golden | ✅ M5 落地（`zip_names` 双解释，工具不选择） |
| 零误改基线（误报防线） | 合成干净短句**仅提统计、不入仓原文** | `scan --baseline <clean.json>` | 干净语料 0 报告、0 改动；污染语料退非 0 | ✅ M5 落地（`tests/test_scan.py`） |
| 退出码语义稳定 | §四单点定义 | 五个子命令 | 四组退出码测试（干净 / 新增 / 用法错误 / 环境不满足） | ✅ M5 起 `EXIT_NOT_READY` 常量删除，五个子命令只用 0/1/2/3 |
| fixture 可重建 | 生成脚本固定输入 | `data/fixtures/**` | 重生成逐字节一致（`--check`） | ✅ M1 已重建（3.8 / 3.12） |
| bench 可复算 | 57 例程序化生成 | `bench/run.py` → `bench/out/attr.json` + `bench/golden/attr.json` | 干净环境重跑数字一致（同解释器版本） | ✅ M1 已复算；M2 硬门复跑 |
| README 四场景复现 | 场景命令 | `README.md` | 干净 clone 按 README 跑通 | ⬜ 待 M6 |
| 发布三件套 | — | tag / Release 附产物 / `plan/RELEASE-M6.md` | tag 树内含留档；Release 有附件 + 本地副本 + sha256 | ⬜ 待 M6 |

## 提交材料实物表（plan/01 §三 逐项落位）

> 每一项都要能在 M6 指着一个具体文件说"就是它"；指不出的项现在删，不留成无主承诺。

| 承诺项 | 应存在的文件路径 | 由哪个里程碑产出 | 用哪条命令核对 |
|---|---|---|---|
| 可安装 CLI 入口 | `pyproject.toml`（`[project.scripts] forensics`）+ `src/mojibake_forensics/cli.py` | M0 骨架 | `pip install -e . && forensics --help` |
| 五个子命令实现 | `src/mojibake_forensics/{attr,explain,recover,file,scan}.py` + `codecs_table.py` / `paths.py` / `score.py` / `report.py` | M2–M5（全部已交付） | `forensics <sub> --help` × 5 |
| 可复算基准 | `bench/run.py` → `bench/out/attr.json`（不入仓）+ `bench/golden/attr.json`（入仓） | M1 基准 / M2 硬门 | `python bench/run.py --check` |
| fixture 集 | `data/fixtures/{attr,explain,recover,file,scan}/{gen.py,expect.json,README.md}` | M1–M5 | `git ls-files data/fixtures`；`--check` 重生成一致 |
| 测试 | `tests/test_*.py` | M1–M5 | `pytest -q` |
| README.md | `README.md`（四场景 + 字段说明 + 已知边界） | M6 | 干净 clone 按 README 跑通 |
| 发布留档 | `plan/RELEASE-M6.md`（两栏：tag 时点 / tag 后追加） | M6 | `git cat-file -e v0.1.0:plan/RELEASE-M6.md` |

> **招牌动词表**（能力名词 → 交付态命令 → 断言基准）见 `plan/01-题目文档.md` §二，全项目只此一份。

## 里程碑

| 里程碑 | 内容 | 出口门 | 状态 |
|---|---|---|---|
| M0 | 出题定稿 + 方法论装订 + 可运行骨架 | `plan/00`–`06` / `plan/01` / `data/README.md` / `.gitignore` 齐；`AGENTS.md` + 布局门 + `plan/00` 装订行齐；`pyproject.toml` + 五个子命令参数面 + `pytest` 双解释器绿；布局门与变异验证绿 | ✅ 已完成（2026-10-20） |
| **M1** | **数据先行** | `bench/run.py` 可复现 57 例探针口径（链深 2 数字与 `data/README.md` §1.3.1 对齐；链深 3 记为未实测）；**五类不可逆各一例 fixture**；**干净语料误报基线**（只提统计、不入仓原文）落地；fixture 生成器 `--check` 逐字节一致 | ✅ 已完成（2026-10-20） |
| M2 | `attr` 归因 | 候选集恒为列表；真答案在候选集内 100%（57 例，链深 3 实测 57/57）；候选有界；三层打分与置信度分项可复算；双跑逐字节一致；`bench/out/attr.json` 产出 | ✅ 已完成（2026-10-20） |
| M3 | `explain` 证明 | 每条路径可被**独立脚本**重放；`--vs` 对照给出分叉点；改错 codec 名 → 指向具体 step；双跑一致 | ✅ 已完成（2026-10-20） |
| M4 | `recover` 不可逆 | 五类各一条单测；`LOST` 附丢失点定位；输出不含自造字符；`verify` 失败降级为 `LOST` | ✅ 已完成（2026-10-20） |
| M5 | `file` 管道 + `scan` 门禁 | 三类管道 fixture 全对；干净语料**零报告零改动**；退出码四组语义稳定；JSON 机器可读 | ✅ 已完成（2026-10-20） |
| M6 | 发布 | **git tag（`v0.1.0`）+ GitHub Release（附产物：手工源码包，本地留副本 + sha256）+ 发布留档 `plan/RELEASE-M6.md`（tag 前落盘、tag 后分栏追加）**；干净环境按 README 跑通四场景；提交面脱敏（含 tag tagger 邮箱）；发布 GitHub **公开仓库** | ⬜ |

> **M6 DoD 口径 = A）"Release 附产物"**：至少 1 个手工上传附件（`git archive` + `gzip -9n` + `SHA256SUMS`），本地留副本并记录 sha256。里程碑表的 DoD 列**只能加不能减**；要减必须在决策记录留一行理由。

## 台账与里程碑维护纪律

- 台账状态列在对应里程碑完成的**同一次提交**里翻转，不得滞后。
- 任何一条承诺若在开发中被砍，必须在决策记录表新增一行说明理由，并**同步删除题面对应措辞**；不得只改台账不改题面。
- 里程碑出口门只能加强，不得为了让里程碑"看起来完成"而改弱（尤其 M6 的"附产物"三个字）。
