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

<!-- POST_TAG_PLACEHOLDER -->
> tag 后回填：tag 对象哈希、tag 父提交、Release URL、附件名 + sha256、干净环境四场景结果、CI run id、附件与 tag 树同源复核输出。

## 三、阶段 7 覆盖对账表

| 出口门 | 状态 | 证据 / 不适用理由 |
|---|---|---|
| 发布物本体已验（真下载 + 中立目录） | 待首推 | tag 后从 Release 真下载，解包到仓库外中立目录 |
| 附件与 tag 树逐字节同源 | 待首推 | `tools/check_release.py` 离线项逐文件比对 |
| 源码包自足（`MANIFEST.in` 白名单） | 待首推 | `git archive` 含全部 tracked 文件；解包后按 README 安装 |
| README 每条命令在解包树真敲 | 待首推 | 四场景：attr / explain / recover / scan |
| 版本号多处一致 | 实现 | `pyproject.toml` / `__init__.py` / README 均为 `0.1.0`；发布门 VERSION PASS |
| 脱敏（提交身份 + tagger 邮箱） | 实现 | 提交身份 noreply；tagger 在 tag 时固定 noreply（tag 后复核） |
| CI push 数 = run 数对账 | 待首推 | 首推后回填 |
| 发布门 `--pre-tag` 跑通 | 实现 | `tools/check_release.py --pre-tag` 退出码 0 |
| PyPI 首发 | 不适用 | 本项目发布形态为 GitHub Release 手工源码包（`plan/00` 交付形态），不做 PyPI |
