# WRAPUP-M6 · 首期收尾

> M6 为首期最后一个里程碑；本文是收尾记录，不是下一棒交接单（无 M7）。
> 布局门 `LAYOUT.RELEASE` 认可 RELEASE/WRAPUP 二选一形态；发布事实的完整留档在 `plan/RELEASE-M6.md`（两栏 + 覆盖对账），本文只登记后续维护入口与已知遗留。

## 一、首期终态

- 仓库：https://github.com/yuluo554/10-20-mojibake-forensics（public）
- 版本：`v0.1.0`（tag 对象 `6a5d7bd`；Release 附手工源码包 + `SHA256SUMS`，sha256 `b98055f…e9279`）
- 五个子命令交付：`attr` / `explain` / `recover` / `file` / `scan`；退出码 0/1/2/3
- 测试 174 条 × 双解释器（3.8 / 3.12）全绿；CI 首绿 run 39452638001（4 矩阵）
- 干净环境验证：Release 真下载 + 中立目录解包 + 新 venv 安装 + README 四场景全过

## 二、后续维护入口（接手新对话从这里开始）

1. `python tools/check_sprint_layout.py` —— 布局门（绿才动手）。
2. 口径单点：`data/README.md` §四（K1–K10 索引见 `plan/HANDOFF-M6.md` §四）；状态副本三处（`plan/00` / `plan/05` / `README.md`）。
3. 发布类操作：`tools/check_release.py`（`--pre-tag` / 离线 / `--online`）；脱敏：`tools/check_desensitize.py`。
4. CI：`.github/workflows/ci.yml`（布局门 + pytest + CLI 冒烟 + bench golden + fixture drift + 发布门 pre-tag + 变异自检）。

## 三、已知遗留（如实登记）

| 项 | 现状 | 处置 |
|---|---|---|
| tag 树 CI run（39450988842）红 | **v0.1.0 的发布物在 Linux 上自带套件 = 1 failed / 173 passed**（`tests/test_recover.py::test_report_has_no_host_facts`；`COMPUTERNAME` 缺省空串使断言恒假）。实测方式：`git clone --no-local` + `checkout v0.1.0` + `env -u COMPUTERNAME pytest` | `main` 上已修（`f8056bb`），**未进 tag**；`v0.1.0` 按既定口径不重打，`v0.1.1` 起不再重现 |
| Shift-JIS / EUC-KR 全量样本 | 首期少量代表样本 | 二期 |
| 词频语言先验 | 默认关闭（`--freq` 报错退出码 2） | 二期可选包；词表不入仓 |
| PyPI | 不适用（发布形态 = GitHub Release 手工源码包） | 如需再启，走 `plan/06` 决策流程 |
| git 443 间歇阻断 | 本机 git HTTPS 通道不稳 | push 走 SSH（`git@github.com`）；gh API 通道正常 |

## 四、二期候选（不承诺）

- 补丁版 `v0.1.1`：把 tag 后的测试修复与 README 状态行纳入新 tag 树。
- Unicode 安全扫描（D-2）、通用 homoglyph：已弃选理由见 `plan/00` 决策记录表，重启需新决策行。
