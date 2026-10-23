# RELEASE-M6 · v0.1.0 发布留档

> 本文件随 tag 树冻结：第一栏是 tag 前事实；第二栏在 tag / Release 成功后追加提交（tag 对象本身不含第二栏字面值，字面值见 Release 正文与 tag 后提交）。
> 口径：`plan/05` §三、`plan/06` §七、`plan/HANDOFF-M6.md` §六。

## 一、tag 前事实

- 基准日：2026-10-20
- 版本：`0.1.0`（`pyproject.toml` / `src/mojibake_forensics/__init__.py` 同值；README 首行同值）
- 计划 tag：`v0.1.0`（annotated；tagger 使用 noreply 邮箱）
- tag 父提交：`git rev-parse v0.1.0^{commit}`（字面值在第二栏回填）
- 发布形态：GitHub 公开仓库 `yuluo554/10-20-mojibake-forensics`；Release 附手工源码包 + `SHA256SUMS`；本地副本在 `dist/release/`（不入仓）
- 源码包方法：`git archive --format=tar --prefix=mojibake-forensics-0.1.0/ v0.1.0 | gzip -9n > mojibake-forensics-0.1.0.tar.gz`
- 同源判据：解包后逐文件 sha256 与 `git show v0.1.0:<path>` 比对；文件集合与 `git ls-tree -r --name-only v0.1.0` 一致

### 1.1 tag 前门禁（本机实测）

| 门 | 命令 | 结果 |
|---|---|---|
| 布局门 | `py -X utf8 tools/check_sprint_layout.py` | 全绿（8 项 PASS） |
| 测试 3.8 | `py -3.8 -m pytest -q` | 174 passed |
| 测试 3.12 | `py -3.12 -m pytest -q` | 174 passed |
| 探针 | `py -3.12 bench/run.py --check` | `golden matches`；57 cases；minimal median 7 / max 10；expanded median 33 / max 57；truth 57/57；depth3 median 125 / max 241 |
| fixture | 12 个 `gen.py --check` | 12/12 PASS |
| 发布门 | `py -3.12 tools/check_release.py --pre-tag` | VERSION PASS / RELEASE_DOC PASS / TAG SKIP / ARTIFACTS SKIP |

> 交接单写“175 条”，M6 复核实测为 174 条（3.8 / 3.12 同）；以实测为准。
> **本句为 M6 当时的更正记录，不再改动**（`plan/HANDOFF-M6.md:14` 的「175」是有意保留的历史错值；下一轮不要再"修"它，否则会制造新的不一致）。

### 1.2 脱敏四步

| 步骤 | 做法 | 结果 |
|---|---|---|
| 代码 | 报告只输出 basename / 相对路径；无时间 / 主机名 / 用户名 / 绝对路径 | 扫描 + 测试断言 |
| 文档 | README / plan / data 无本机盘符绝对路径、无本机用户名 / 主机名（`tools/check_desensitize.py` 扫描） | 扫描 |
| 提交元数据 | 作者 / 提交者均为 `yuluo554 <282769740+yuluo554@users.noreply.github.com>` | `git log` 复核 |
| tag tagger | tag 时设置 `GIT_COMMITTER_NAME/EMAIL` 为同一 noreply 身份 | tag 后 `git for-each-ref` 复核 |

### 1.3 CI 口径

- 本地等价校验，未接远端，CI 待首推验证。
- 首推后回填：workflow run id / 矩阵结果。CI 只跑 `--pre-tag`；发布门联网检查（`--online`）只在本机 / 发布时跑。

## 二、tag 后追加

（2026-10-20 回填；本栏在 tag 后提交进入仓库，tag 对象本身不含本栏字面值。）

### 2.1 发布事实

| 项 | 值 |
|---|---|
| tag 对象 | `6a5d7bdb5fa8fb9161b9f5e1336481a18cb4a96c`（annotated；tagger `yuluo554 <282769740+yuluo554@users.noreply.github.com>`） |
| tag 父提交 | `fbb7b2c1230d4d5267885cc020f5b0b37a3dab6a` |
| 远端对账 | tag 对象与 main 头提交远端 sha 与本地逐字节一致（`gh api .../git/ref/tags/v0.1.0` 与 `.../commits/main`） |
| 仓库 | https://github.com/yuluo554/10-20-mojibake-forensics（public；git 443 间歇阻断，push 走 SSH 通道） |
| Release | https://github.com/yuluo554/10-20-mojibake-forensics/releases/tag/v0.1.0（非 draft / 非 prerelease） |
| 附件 | `mojibake-forensics-0.1.0.tar.gz` + `SHA256SUMS` |
| sha256 | `b98055ff9b61ff71fc9fe3883ada8007a3ea7589db956cb95f100fc7296e9279`（本地副本 = Release 下载件 = 远端 API 读回，三者一致） |
| 同源复核 | `tools/check_release.py` 离线项：解包 118 个文件与 `git show v0.1.0:<path>` 逐文件 sha256 一致，文件集合与 `git ls-tree -r v0.1.0` 一致，含 `plan/RELEASE-M6.md` |

### 2.2 干净环境验证（真下载 + 中立目录 + 新 venv）

- `gh release download` → sha256 与本地一致；`tar xzf`；`py -3.12 -m venv` 新环境 `pip install ./mojibake-forensics-0.1.0.tar.gz` → `forensics 0.1.0`。
- 四场景（解包树内，README 命令路径）：
  1. `attr --text "é›…é›…"` → 351 候选 / top 5 / criteria 行，退出码 0；
  2. `explain --pick 1 --vs 2` → 2 步重放 `recompute: PASS` + 分叉点 `step 2 codec differs`，退出码 0；
  3. `recover --text "锟斤拷" --pick 1` → `LOST(kun_jin_kao)` + 丢失点 + `no_invented_characters`，退出码 1；
  4. `scan`（fixture 干净语料）→ `ok` / 0 new，退出码 0；（污染语料）→ `attention` / 2 new（ja.md:1、zh.md:1），退出码 1。
- 解包树内跑打包自带测试套件：174 passed（venv 内装 pytest 后复跑两轮一致）。

### 2.3 CI 首跑实录（如实登记）

| run | 触发 | 结果 | 说明 |
|---|---|---|---|
| 39450988842 | push `v0.1.0` | failure（仅 ubuntu ×2） | tag 树内 `tests/test_recover.py` 已知测试缺陷：`COMPUTERNAME` 在 Linux 缺省空串使 host-facts 断言恒真；windows ×2 全绿 |
| 39450975557 / 39451948486 | push main | failure（ubuntu 3.12） | 同一缺陷（已修 `f8056bb`）+ 变异验证"M3 待办"假设过期（已修 `2f67bb2`） |
| **39452638001** | push main（`2f67bb2`） | **success** | 4 矩阵（3.8/3.12 × ubuntu/windows）全绿 |

- 缺陷修复提交（`f8056bb` / `2f67bb2`）在 tag 之后，**不回填进 tag 树**；tag 忠实记录发布物，已知问题在 Release 正文"已知边界"下登记。
- push 数 5 = run 数 5（含 tag 推送触发的一次），对账一致。

### 2.4 发布门终态

`py -3.12 -X utf8 tools/check_release.py --online` → 5 PASS / 0 FAIL / 0 SKIP（VERSION / RELEASE_DOC / TAG / ARTIFACTS / ONLINE）。

## 三、阶段 7 覆盖对账表

| 出口门 | 状态 | 证据 / 不适用理由 |
|---|---|---|
| 发布物本体已验（真下载 + 中立目录） | 实现 | Release 真下载（sha256 一致）+ 中立目录解包 + 新 venv 安装；§2.2 |
| 附件与 tag 树逐字节同源 | 实现 | 发布门 ARTIFACTS：118 文件逐文件 sha256 与 tag 树一致；§2.1 |
| 源码包自足（`MANIFEST.in` 白名单） | 实现 | `git archive` 全 tracked 文件；解包树内安装 + 174 测试全绿；§2.2 |
| README 每条命令在解包树真敲 | 实现 | 四场景全过（§2.2），命令路径与 README 一致 |
| 版本号多处一致 | 实现 | `pyproject.toml` / `__init__.py` / README 均 `0.1.0`；发布门 VERSION PASS |
| 脱敏（提交身份 + tagger 邮箱） | 实现 | 5 个提交作者/提交者均 noreply；tagger noreply（发布门 TAG PASS） |
| CI push 数 = run 数对账 | 实现 | push 5 = run 5；tag 树 run 红（已知测试缺陷）如实登记，main 首绿 run 39452638001 |
| 发布门 `--pre-tag` 跑通 | 实现 | tag 前 2 PASS / 0 FAIL / 3 SKIP；tag 后 `--online` 5 PASS |
| PyPI 首发 | 不适用 | 本项目发布形态为 GitHub Release 手工源码包（`plan/00` 交付形态），不做 PyPI |
