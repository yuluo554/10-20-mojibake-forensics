#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""布局门（ai-tool-project-sprint 方法论装订第②件）。

把"项目还长在方法论上"变成可跑红的断言。判据只落仓库内文件，不读 git 元数据
（浅克隆下 tag / 历史深度会翻转）。

用法：
    python tools/check_sprint_layout.py [--root <repo>]
退出码：0 全绿 / 1 有 FAIL / 2 用法错误。
"""

from __future__ import print_function

import argparse
import os
import re
import sys

CHECKS = []
SCANNED = {"docs": 0, "handoffs": 0, "copies": 0, "doc_tools": 0}


def add(check_id, ok, detail):
    CHECKS.append((check_id, ok, detail))


REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "data/README.md",
    "plan/00-README总览.md",
    "plan/01-题目文档.md",
    "plan/02-架构与技术选型.md",
    "plan/03-模块详设.md",
    "plan/04-数据计划.md",
    "plan/05-里程碑与发布.md",
    "plan/06-交付对标与决策.md",
]

# 装订行：三个锚点必须同现于一行（顺序无关，使用前瞻）。
BINDING_LINE = re.compile(
    r"^>(?=.*ai-tool-project-sprint)(?=.*check_sprint_layout)(?=.*20\d{2}-\d{2}-\d{2}).*$",
    re.MULTILINE,
)

REQUIRED_SECTIONS = {
    "plan/00-README总览.md": ["文档索引", "决策记录", "承诺-证据台账", "里程碑"],
    "plan/01-题目文档.md": ["任务要求", "评分标准", "边界与非目标"],
    "plan/02-架构与技术选型.md": ["分层", "构建"],
    "plan/03-模块详设.md": ["公共契约", "失败路径", "接口稳定性"],
    "plan/04-数据计划.md": ["数据清单", "真值纪律", "数值口径"],
    "plan/05-里程碑与发布.md": ["DoD", "已知未验证项"],
    "plan/06-交付对标与决策.md": ["评分对标", "风险登记", "缺口"],
    "data/README.md": ["依据查证记录", "数值口径"],
}

# 七节：证据 / 当前事实·状态不变量 / 待办 / K 口径 / 环境坑 / DoD / 命令速查
HANDOFF_SECTIONS = [
    "证据",
    "当前事实",
    "待办",
    "（K 编号",
    "环境坑",
    "DoD",
    "命令速查",
]

# 项目已声明的豁免：M0 的收尾记录就是计划套件本身，不要求 HANDOFF-M0。
EXEMPT_MILESTONES = [0]
HANDOFF_FORMAT_FROM = 1
RELEASE_MILESTONE = 6

STATUS_COPIES = [
    ("plan/00-README总览.md", "里程碑表"),
    ("plan/05-里程碑与发布.md", "状态表"),
    ("README.md", "状态表"),
]

STATUS_LINE = re.compile(r"^\|\s*\*{0,2}M(\d+)\b")
PENDING_MARKERS = ["⬜", "🟡", "未开始", "未执行", "待执行", "待确认"]


def read(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def check_required_files(root):
    missing = [rel for rel in REQUIRED_FILES if not os.path.exists(os.path.join(root, rel))]
    SCANNED["docs"] = len(REQUIRED_FILES) - len(missing)
    detail = "缺: " + ",".join(missing) if missing else "%d 份齐备" % SCANNED["docs"]
    add("LAYOUT.FILES", not missing, detail)


def check_binding_head(root):
    text = read(os.path.join(root, "plan/00-README总览.md")) or ""
    ok = bool(BINDING_LINE.search(text))
    add(
        "LAYOUT.BINDING_HEAD",
        ok,
        "plan/00 顶部有装订行（三锚点齐）"
        if ok
        else "plan/00 顶部缺装订行（需同现：方法论名 + 布局门命令 + 装订日期）",
    )


def check_sections(root):
    bad = []
    for rel, needles in REQUIRED_SECTIONS.items():
        text = read(os.path.join(root, rel))
        if text is None:
            continue
        missing = [needle for needle in needles if needle not in text]
        if missing:
            bad.append("%s: %s" % (rel, "/".join(missing)))
    add(
        "LAYOUT.SECTIONS",
        not bad,
        "；".join(bad) if bad else "%d 份小节齐备" % len(REQUIRED_SECTIONS),
    )


def check_documented_tools(root):
    """文档点名的 tools/* 脚本必须有实物（防"文档有门、仓库无门"）。"""
    docs = ["AGENTS.md"]
    plan_dir = os.path.join(root, "plan")
    if os.path.isdir(plan_dir):
        docs.extend(
            "plan/" + name
            for name in sorted(os.listdir(plan_dir))
            if name.endswith(".md")
        )
    referenced = set()
    pattern = re.compile(r"tools/[\w.-]+\.(?:py|mjs|js|cjs|sh|ps1)")
    for rel in docs:
        text = read(os.path.join(root, rel))
        if text is None:
            continue
        referenced.update(pattern.findall(text))
    if not referenced:
        add(
            "LAYOUT.DOC_TOOLS",
            False,
            "扫了 %d 份文档，0 处 tools/ 引用——判据是空的（阳性对照失败）" % len(docs),
        )
        return
    SCANNED["doc_tools"] = len(referenced)
    missing = sorted(rel for rel in referenced if not os.path.exists(os.path.join(root, rel)))
    add(
        "LAYOUT.DOC_TOOLS",
        not missing,
        "文档点名但不存在的工具: " + ",".join(missing)
        if missing
        else "%d 个文档点名的 tools/ 脚本全部在位" % len(referenced),
    )


def collect_states(root):
    states = {}
    for rel, _kind in STATUS_COPIES:
        text = read(os.path.join(root, rel))
        if text is None:
            continue
        SCANNED["copies"] += 1
        for line in text.splitlines():
            match = STATUS_LINE.match(line)
            if not match:
                continue
            milestone = int(match.group(1))
            pending = any(marker in line for marker in PENDING_MARKERS)
            states.setdefault(milestone, set()).add("pending" if pending else "done")
    return states


def check_status_agreement(states):
    conflicts = []
    for milestone in sorted(states):
        values = states[milestone]
        if len(values) > 1:
            conflicts.append(
                "M%d 在副本间状态不一致（%s）" % (milestone, " vs ".join(sorted(values)))
            )
    add(
        "LAYOUT.STATUS",
        not conflicts,
        "；".join(conflicts)
        if conflicts
        else "%d 处副本 × %d 个里程碑 状态全一致"
        % (SCANNED["copies"], len(states)),
    )


def check_handoffs(root, done):
    problems = []
    for milestone in done:
        if milestone in EXEMPT_MILESTONES:
            continue
        rel = "plan/HANDOFF-M%d.md" % milestone
        text = read(os.path.join(root, rel))
        if text is None:
            problems.append("%s(缺)" % rel)
            continue
        SCANNED["handoffs"] += 1
        if milestone < HANDOFF_FORMAT_FROM:
            continue
        missing = [needle for needle in HANDOFF_SECTIONS if needle not in text]
        if missing:
            problems.append("%s(缺节: %s)" % (rel, "/".join(missing)))
    add(
        "LAYOUT.HANDOFFS",
        not problems,
        "；".join(problems)
        if problems
        else "%d 份交接单齐（M0 已声明豁免）" % SCANNED["handoffs"],
    )


def check_stale_gaps(root, done):
    """plan/06 的「缺口」列是状态的隐蔽副本：按表头定位列号，再取单元格。

    扫描面 = 该表头之后连续的表格行（遇到第一行非表格即停），不扫文件后面的其它表。
    """
    text = read(os.path.join(root, "plan/06-交付对标与决策.md"))
    if text is None:
        add("LAYOUT.GAPS", False, "plan/06 不存在")
        return
    lines = text.splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("|") and "缺口" in line:
            header_idx = idx
            break
    if header_idx is None:
        add("LAYOUT.GAPS", False, "plan/06 找不到含『缺口』表头的表（判据表搬走了？）")
        return
    header_cells = [cell.strip() for cell in lines[header_idx].strip().strip("|").split("|")]
    try:
        gap_col = header_cells.index("缺口")
    except ValueError:
        gap_col = 0
    stale = []
    for line in lines[header_idx + 2 :]:
        if not line.lstrip().startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        cell = cells[gap_col] if gap_col < len(cells) else ""
        # 先剥掉行内代码与路径形态，避免文件名里的里程碑号被误判为状态引用。
        scrubbed = re.sub(r"`[^`]*`", "", cell)
        scrubbed = re.sub(r"[\w./-]+\.md", "", scrubbed)
        for milestone in done:
            if re.search(r"(^|[^0-9A-Za-z])M%d([^0-9]|$)" % milestone, scrubbed):
                stale.append("plan/06 缺口列仍提 M%d: %s" % (milestone, cell))
    add(
        "LAYOUT.GAPS",
        not stale,
        "；".join(stale) if stale else "plan/06 缺口列无已完成里程碑",
    )


def check_release_doc(root, done):
    if RELEASE_MILESTONE not in done:
        add(
            "LAYOUT.RELEASE",
            True,
            "M%d 未完成，发布留档尚未要求（当前 done=%s）"
            % (RELEASE_MILESTONE, sorted(done)),
        )
        return
    release = read(os.path.join(root, "plan/RELEASE-M6.md"))
    wrapup = read(os.path.join(root, "plan/WRAPUP-M6.md"))
    if release is None and wrapup is None:
        add("LAYOUT.RELEASE", False, "缺 plan/RELEASE-M6.md 或 plan/WRAPUP-M6.md")
        return
    if release is not None:
        columns = bool(
            re.search(r"^##\s*一、tag 前事实", release, re.MULTILINE)
            and re.search(r"^##\s*二、tag 后追加", release, re.MULTILINE)
        )
        coverage = bool(re.search(r"^#{2,3}.*覆盖对账", release, re.MULTILINE))
        rows = len(
            re.findall(r"^\|.*(?:实现|不适用|待首推).*\|$", release, re.MULTILINE)
        )
        add(
            "LAYOUT.RELEASE",
            columns and coverage and rows >= 3,
            "两栏:%s 覆盖对账小节:%s 三态行数:%d" % (columns, coverage, rows),
        )
        return
    add("LAYOUT.RELEASE", True, "WRAPUP 形态")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sprint layout gate")
    parser.add_argument("--root", default=None, help="repository root (default: script/..)")
    args = parser.parse_args(argv)
    root = args.root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if not os.path.isdir(root):
        print("布局门: root 不存在: %s" % root)
        return 2

    checks = [
        check_required_files,
        check_binding_head,
        check_sections,
        check_documented_tools,
    ]
    for check in checks:
        try:
            check(root)
        except Exception as exc:  # 永不崩：被检查对象不存在也要报 FAIL 并继续
            add(check.__name__, False, "异常: %s" % exc)

    states = collect_states(root)
    done = [milestone for milestone, values in states.items() if "done" in values]
    followups = [
        lambda: check_status_agreement(states),
        lambda: check_handoffs(root, done),
        lambda: check_stale_gaps(root, done),
        lambda: check_release_doc(root, done),
    ]
    for check in followups:
        try:
            check()
        except Exception as exc:
            add("followup", False, "异常: %s" % exc)

    failed = [item for item in CHECKS if not item[1]]
    print("布局门（方法论装订） · 判据只落仓库内文件")
    print("=" * 56)
    for check_id, ok, detail in CHECKS:
        print("%s  %s  %s" % ("PASS" if ok else "FAIL", check_id, detail))
    print("=" * 56)
    print(
        "这轮扫到：文档 %d / 交接单 %d / 状态副本 %d / 文档点名工具 %d"
        % (
            SCANNED["docs"],
            SCANNED["handoffs"],
            SCANNED["copies"],
            SCANNED["doc_tools"],
        )
    )
    print("结论: %s" % ("全绿" if not failed else "%d 项 FAIL" % len(failed)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
