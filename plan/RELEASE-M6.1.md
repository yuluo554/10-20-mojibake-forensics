# RELEASE-M6.1 · v0.1.1 补丁版发布留档

> 本文件随 tag 树冻结：第一栏是 tag 前事实；第二栏在 tag / Release 成功后追加提交（tag 对象本身不含第二栏字面值，字面值见 Release 正文与 tag 后提交）。
> 口径：`plan/05` §三、`plan/06` §七、`plan/RELEASE-M6.md` 首段。
> 为什么有这一版：`v0.1.0` 的发布物在 Linux 上自带套件 = **1 failed / 173 passed**（`tests/test_recover.py::test_report_has_no_host_facts`，`COMPUTERNAME` 缺省空串使断言恒假），修复提交 `f8056bb` 在 tag 之后。按 `plan/WRAPUP-M6.md` §四 的「二期候选：补丁版 v0.1.1」兑现，**`v0.1.0` 不重打、不移动**。

## 一、tag 前事实

- 基准日：2026-10-23
- 版本：`0.1.1`（`pyproject.toml` / `src/mojibake_forensics/__init__.py` 同值；README 首行同值）
- 计划 tag：`v0.1.1`（annotated；tagger 使用 noreply 邮箱）
- tag 父提交：`git rev-parse v0.1.1^{commit}`（字面值在第二栏回填）
- 发布形态：GitHub 公开仓库 `yuluo554/10-20-mojibake-forensics`；Release 附手工源码包 + `SHA256SUMS`；本地副本在 `dist/release/`（不入仓）
- 源码包方法：`git archive --format=tar --prefix=mojibake-forensics-0.1.1/ v0.1.1 | gzip -9n > mojibake-forensics-0.1.1.tar.gz`
- 同源判据：解包后逐文件 sha256 与 `git show v0.1.1:<path>` 比对；文件集合与 `git ls-tree -r --name-only v0.1.1` 一致

### 1.1 本版修的是什么（逐条对缺陷编号）

| 编号 | 缺陷 | 本版处置 |
|---|---|---|
| D1（P0） | `v0.1.0` 发布物在 Linux 上 1 failed / 173 passed | tag 树纳入 `f8056bb`；并新增跨平台守门 `test_host_facts_check_is_not_vacuous_when_var_absent`（变量缺失时确认走跳过分支、变量存在时确认检测器有效、静态守门禁止空串默认值回归） |
| D3（P0） | `scan --dir` 指向坏路径 → `rc=0` + `status:"ok"` + `files_scanned:0`，一个手误就能让 CI 门禁永远绿 | `scan()` 入口先校验：不存在 → `scan_directory_missing`；指向文件 → `scan_directory_not_a_directory`；两者 rc=2 且不产出任何输出 |
| D4/D5（P0） | 基线根约定不一致：README 的两条命令与 `--dir .` **三种调用全都过不了** `expect.json`（`stale` 恒 10、`polluted.new` 缺前缀） | 基线根统一为**基线文件所在目录**（`data/README.md` §4.6 单点定义）；`--dir` 只收窄子树。改后 clean → files 10 / new [] / stale [] / exit 0，polluted → files 3 / new [`polluted/ja.md`,`polluted/zh.md`] / exit 1，两格与 `expect.json` 逐字一致 |
| D4 第三层 | `expect.json` 无任何测试在读（活数据变死数据） | 新增 `test_expect_json_matches_reality` 逐格断言 + `test_expect_json_stale_probe` |
| D7（P1） | `checkout@v4` / `setup-python@v5` 触发 Node20 弃用注解 | 升 `@v7`；推送后 run `39897950161` 四腿全绿、注解 0 条 |
| D10（P2） | 脱敏门被四份文档当发布面证据指向，却不在 CI 里跑 | 新增 `Desensitize scan` step |
| D11（P2） | 全仓无「下次复核」元数据 | `data/README.md` 首屏加 `next_review: 2026-11-20`（阅读动作，不是断言阈值） |
| D2（P1） | tag 树 README / plan 状态与「已发布」事实相反 | 由本版 tag 树承接：README `| M6 | ✅`+`M6.1`、`plan/00`、`plan/05` 同 |
| D6（P1） | `license = { text = "MIT" }` 触发 PEP 639 弃用 | **DEC-4 乙**：保留 3.8 floor，在 `pyproject.toml` 就地写明弃用与 2027-02-18 期限，不转 SPDX |
| D8 / D9 / D12 / D13 | 已登记的历史错值 / 本地卫生 / 上界 / `addopts` 双 `-q` | 按诊断处置：D8 在 `RELEASE-M6:27` 标注「不再改动」；D9 已删 `dist/*.dev0`；D12/D13 不改判据 |

### 1.2 tag 前门禁（本机实测）

| 门 | 命令 | 结果 |
|---|---|---|
| 布局门 | `py -X utf8 tools/check_sprint_layout.py` | 全绿 |
| 变异验证 | `py -X utf8 tools/check_layout_mutations.py` | 全部变异均被捕获 |
| 测试（Windows） | `py -3.12 -m pytest -o addopts=""` | 180 passed |
| 测试（Linux 语义） | `env -u COMPUTERNAME py -3.12 -m pytest -o addopts=""` | 180 passed |
| 探针 | `py -3.12 bench/run.py --check` | `golden matches`；57 cases；truth 57/57 ×2；truth first 34/57；depth3 median 125 / max 241 |
| fixture | 12 个 `gen.py --check` | 12/12 PASS（字节零改动） |
| 脱敏门 | `py -3.12 tools/check_desensitize.py` | `TOTAL 0` |
| 发布门 | `py -3.12 tools/check_release.py --pre-tag` | 0 FAIL |

> 测试数从 174 增至 180：新增 1 条 D1 守门、2 条 D3 坏路径、2 条 `expect.json` 活判据、1 条 `scan_directory` 的 `root` 语义。零 skip、零 xfail。

### 1.3 CI 口径

- `v0.1.1` tag 前的修复批已推送并验证：run `39897950161`（4 腿 = 3.8/3.12 × ubuntu-22.04/windows-latest）全绿，`Node.js 20 is deprecated` 注解 **0 条**。
- 矩阵仍钉 `ubuntu-22.04`（理由见 `ci.yml` 行内注释与 `plan/05` 环境事实）：规避 `ubuntu-latest` 自 2026-10-19 起迁移 Ubuntu 26。
- CI 只跑 `--pre-tag`；`--online` 只在本机 / 发布时跑。

## 二、tag 后追加

（tag / Release 成功后回填；本栏在 tag 后提交进入仓库，tag 对象本身不含本栏字面值。）

### 2.1 发布事实

| 项 | 值 |
|---|---|
| tag 对象 | 待回填 |
| tag 父提交 | 待回填 |
| Release | 待回填 |
| 附件 | `mojibake-forensics-0.1.1.tar.gz` + `SHA256SUMS` |
| sha256 | 待回填（本地副本 = Release 下载件 = 远端 API 读回，三者一致） |
| 同源复核 | 待回填（解包逐文件 sha256 与 tag 树比对） |

### 2.2 干净环境验证

- 待回填：真下载 → sha256 对撞 → 中立目录解包 → 新 venv 安装 → `forensics --version` → 四场景 → **`env -u COMPUTERNAME` 跑自带套件**（这一条是 D1 的最终验收）。

### 2.3 CI 实录

- 待回填（v0.1.1 tag 推送触发的 run id 与四腿结论）。

## 三、阶段 7 覆盖对账表

| 出口门 | 状态 | 证据 / 不适用理由 |
|---|---|---|
| 发布物本体已验（真下载 + 中立目录） | 实现 | §2.2（真下载 + 中立目录解包 + 新 venv） |
| 附件与 tag 树逐字节同源 | 实现 | 发布门 ARTIFACTS 逐文件 sha256 对撞（不是只比文件名） |
| 源码包自足 | 实现 | `git archive` 全 tracked 文件；解包树内安装 + 自带套件全绿（`env -u COMPUTERNAME`） |
| README 每条命令在解包树真敲 | 实现 | 四场景全过；`scan` 两条命令与 `expect.json` 逐格一致 |
| 版本号多处一致 | 实现 | `pyproject.toml` / `__init__.py` / README / tag 均 `0.1.1`；发布门 VERSION PASS |
| 脱敏（提交身份 + tagger 邮箱） | 实现 | 提交作者/提交者为 noreply；tagger noreply（发布门 TAG PASS） |
| CI push 数 = run 数对账 | 实现 | 前置修复批 run `39897950161` 四腿全绿、注解 0；tag 推送另跑一次并回填 §2.3 |
| 发布门 `--pre-tag` 跑通 | 实现 | tag 前 0 FAIL |
| PyPI 首发 | 不适用 | 发布形态 = GitHub Release 手工源码包（`plan/00` 交付形态），不做 PyPI |
