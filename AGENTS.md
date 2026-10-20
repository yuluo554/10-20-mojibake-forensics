# AGENTS.md

本仓库遵循 **`ai-tool-project-sprint`** 方法论（装订日期：2026-10-20）。

## 任何新对话的第一件事

```bash
python tools/check_sprint_layout.py
```

- 布局门必须绿；红了先修布局再干活。
- 续接对话：先读 `plan/HANDOFF-M<k>.md`，**先跑上面这条门**。
- 接手对话（无 HANDOFF）：先读 `plan/00`、`plan/05`、`plan/06`，重建"当前状态 + K 口径清单"再动手。
- **门不存在 = 本项目没装订** → 先补第零步三件（本文件 + 布局门 + `plan/00` 顶部装订行），再做别的。

## 强制布局（布局门逐条断言）

| 项 | 位置 | 判据 |
|---|---|---|
| 计划套件 | `plan/00`–`06` + `data/README.md` | 存在且各含必需小节 |
| 数据台账 | `data/README.md` | 来源 + 三态 + 数值口径 |
| 交接单 | `plan/HANDOFF-M<k>.md` | 每个 ✅ 里程碑一份（M0 已声明豁免），七节齐 |
| 里程碑状态副本 | `plan/00` 里程碑表 + `plan/05` 状态表 + `README.md` 状态表 | **三处逐项一致**（枚举式断言） |
| 发布留档 | `plan/RELEASE-M6.md` | 两栏（tag 前 / tag 后）+ 阶段 7 覆盖对账表；M6 前不要求 |
| 文档点名工具 | `tools/*.py` | 文档里出现的工具路径必须有实物 |
| 发布门 | `tools/check_release.py` | M6 前为骨架；不接入 CI |

## 常用命令

```bash
python tools/check_sprint_layout.py       # 布局门
python tools/check_layout_mutations.py    # 布局门变异验证（临时目录）
py -3.8 -m pytest -q                      # 底线解释器测试
py -3.12 -m pytest -q                     # 新解释器测试
python tools/check_release.py --pre-tag   # 发布门（M6 前骨架）
```

## 环境事实与禁忌（实测 2026-10-20）

- 本机 `python` 是商店占位符 → 用 `py` / `py -3.8` / `py -3.12`；中文输出用 `py -X utf8`。
- 本机 Python：3.8.8-64、3.12-64；Node 24.15.0；git 2.54.0.windows.1。
- Git Bash 打印 UTF-8 中文可能显示乱码——验收文件用解析器或 `py -3.12` 读，不靠控制台肉眼。
- 禁止：把"未执行"写成已完成；在 tag 之后改交付面；在文档里点名不存在的工具。
- 无远端期间，CI 类 DoD 一律写"本地等价校验，未接远端，CI 待首推验证"。

## 既定口径（动了会打挂测试）

详见 `plan/HANDOFF-M1.md` §四 K1–K8：schema / 编码集合 / 退出码 / JSON 序列化 / 无损性判据 / 排序键 / 报告脱敏 / 状态副本一致。
数值口径唯一来源：`data/README.md` §四。
