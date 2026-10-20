#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布终态自检门（M6 实现；当前为骨架，不接入 CI）。

设计口径（ai-tool-project-sprint 阶段 7 E 节）：
- `--pre-tag`：tag 相关项报 SKIP 不报 FAIL——发布留档与发布门要能随预备提交进 tag 树；
- 离线（默认）：报 SKIP 不报 PASS，发布未发生则 FAIL；
- `--online`：需要远端与 gh 的检查；环境缺失时退出码 3，不与"发布未达成"（退出码 1）混用。

当前骨架只做模式与退出码占位，M6 补齐检查项；**不要把它写进 CI**。
"""

from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CHECKS = []


def add(check_id, status, detail):
    CHECKS.append((check_id, status, detail))


def check_version_consistency():
    init_path = os.path.join(ROOT, "src/mojibake_forensics/__init__.py")
    pyproject_path = os.path.join(ROOT, "pyproject.toml")
    init_version = None
    project_version = None
    if os.path.exists(init_path):
        with open(init_path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("__version__"):
                    init_version = line.split("=", 1)[1].strip().strip("\"'")
                    break
    if os.path.exists(pyproject_path):
        with open(pyproject_path, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("version") and "=" in stripped:
                    project_version = stripped.split("=", 1)[1].strip().strip("\"'")
                    break
    if init_version and project_version:
        add(
            "VERSION",
            "PASS" if init_version == project_version else "FAIL",
            "__init__=%s pyproject=%s" % (init_version, project_version),
        )
    else:
        add("VERSION", "FAIL", "版本号未找到（__init__ 或 pyproject）")


def check_release_doc():
    path = os.path.join(ROOT, "plan/RELEASE-M6.md")
    if not os.path.exists(path):
        add("RELEASE_DOC", "FAIL", "缺 plan/RELEASE-M6.md（发布未达成）")
        return
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    columns = "## 一、tag 前事实" in text and "## 二、tag 后追加" in text
    coverage = "覆盖对账" in text
    add("RELEASE_DOC", "PASS" if columns and coverage else "FAIL", "两栏:%s 覆盖对账:%s" % (columns, coverage))


def check_tag():
    add("TAG", "SKIP", "tag 检查在 M6 实装（annotated tag / 远端对象哈希）")


def check_artifacts():
    add("ARTIFACTS", "SKIP", "附件与 sha256 检查在 M6 实装")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Release terminal gate (skeleton)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pre-tag", action="store_true", help="tag 前模式：tag 相关项 SKIP")
    mode.add_argument("--online", action="store_true", help="联网模式（gh api）；本骨架未实装")
    parser.add_argument("--root", default=None, help="repository root")
    args = parser.parse_args(argv)

    global ROOT
    if args.root:
        ROOT = os.path.abspath(args.root)

    if args.online:
        print("发布门: --online 尚未实装（M6）")
        return 3

    check_version_consistency()
    check_release_doc()
    check_tag()
    check_artifacts()

    failed = [item for item in CHECKS if item[1] == "FAIL"]
    print("发布终态自检门 · 模式: %s" % ("pre-tag" if args.pre_tag else "offline"))
    print("=" * 56)
    for check_id, status, detail in CHECKS:
        print("%-5s  %-12s  %s" % (status, check_id, detail))
    print("=" * 56)
    print("结论: %d PASS / %d FAIL / %d SKIP" % (
        sum(1 for item in CHECKS if item[1] == "PASS"),
        len(failed),
        sum(1 for item in CHECKS if item[1] == "SKIP"),
    ))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
