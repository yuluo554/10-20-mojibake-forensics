#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""布局门变异验证：逐条判据制造故障，门必须变红；还原后必须全绿。

在临时目录里复制仓库快照再变异，**不触碰工作树**。
用法：python tools/check_layout_mutations.py
退出码：0 全部变异均被捕获 / 1 有变异未红（假门）/ 2 无法建立基线。
"""

from __future__ import print_function

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
GATE = os.path.join(HERE, "check_sprint_layout.py")

IGNORE = shutil.ignore_patterns(
    ".git", "__pycache__", "*.pyc", ".venv", "venv", "build", "dist", "bench/out", ".pytest_cache"
)
STATUS_LINE = re.compile(r"^\|\s*\*{0,2}M(\d+)\b")
PENDING_MARKERS = ["⬜", "🟡", "未开始", "未执行", "待执行", "待确认"]


def copy_repo(destination):
    shutil.copytree(ROOT, destination, ignore=IGNORE)


def run_gate(root):
    proc = subprocess.run(
        [sys.executable, GATE, "--root", root],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return proc.returncode, proc.stdout


def replace_text(path, old, new):
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    if old not in text:
        raise AssertionError("变异 marker 不存在: %s in %s" % (old, path))
    changed = text.replace(old, new, 1)
    if changed == text:
        raise AssertionError("变异未改变字节: %s" % path)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(changed)


def set_milestone_done(root, milestone):
    """把某里程碑在三处状态副本上翻成 done（用于构造 HANDOFF 缺件态）。"""
    for rel in ("plan/00-README总览.md", "plan/05-里程碑与发布.md", "README.md"):
        path = os.path.join(root, rel)
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        changed = False
        for index, line in enumerate(lines):
            match = STATUS_LINE.match(line)
            if not match or int(match.group(1)) != milestone:
                continue
            newline = line
            for marker in PENDING_MARKERS:
                newline = newline.replace(marker, "✅")
            if "✅" not in newline:
                newline = newline.rstrip() + " ✅"
            if newline != line:
                lines[index] = newline
                changed = True
        if not changed:
            raise AssertionError("未找到 M%d 状态行: %s" % (milestone, rel))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines) + "\n")


def load_gate_module():
    spec = importlib.util.spec_from_file_location("layout_gate_under_test", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── 变异体 ────────────────────────────────────────────────────────────────


def mutation_files(root):
    os.remove(os.path.join(root, "plan/02-架构与技术选型.md"))


def mutation_binding_head(root):
    path = os.path.join(root, "plan/00-README总览.md")
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    kept = [line for line in lines if not line.startswith("> 方法论：")]
    if len(kept) == len(lines):
        raise AssertionError("未找到装订行")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept) + "\n")


def mutation_sections(root):
    replace_text(
        os.path.join(root, "plan/06-交付对标与决策.md"),
        "## 四、风险登记",
        "## 四、风险",
    )


def mutation_doc_tools(root):
    os.remove(os.path.join(root, "tools/check_release.py"))


def mutation_status(root):
    replace_text(
        os.path.join(root, "plan/05-里程碑与发布.md"),
        "| M0 | ✅ 已完成（2026-10-20） |",
        "| M0 | ⬜ 未开始 |",
    )


def mutation_handoffs(root):
    set_milestone_done(root, 1)
    os.remove(os.path.join(root, "plan/HANDOFF-M1.md"))


def mutation_gaps(root):
    replace_text(
        os.path.join(root, "plan/06-交付对标与决策.md"),
        "| 核心枚举与无损过滤尚未实现（M2） |",
        "| 核心枚举未实现，见 M0 收尾记录 |",
    )


MUTATIONS = [
    ("LAYOUT.FILES", mutation_files),
    ("LAYOUT.BINDING_HEAD", mutation_binding_head),
    ("LAYOUT.SECTIONS", mutation_sections),
    ("LAYOUT.DOC_TOOLS", mutation_doc_tools),
    ("LAYOUT.STATUS", mutation_status),
    ("LAYOUT.HANDOFFS", mutation_handoffs),
    ("LAYOUT.GAPS", mutation_gaps),
]


def check_release_mutations(tmp):
    """RELEASE 判据有两条独立子判据：两栏齐全 + 覆盖对账小节。逐条变异。"""
    module = load_gate_module()
    release_root = os.path.join(tmp, "release-case")
    release_dir = os.path.join(release_root, "plan")
    os.makedirs(release_dir)
    release_path = os.path.join(release_dir, "RELEASE-M6.md")
    valid = """# RELEASE-M6

## 一、tag 前事实

- 版本 v0.1.0。

## 二、tag 后追加

- 追加提交。

### 三、阶段 7 覆盖对账

| 出口门 | 状态 | 证据 |
|---|---|---|
| 发布物本体 | 实现 | 下载件 sha256 |
| 源码包自足 | 不适用 | 手工源码包形态 |
| CI 对账 | 待首推 | 首推后回填 |
"""
    failures = []

    def run_case(name, text, expect_fail):
        module.CHECKS[:] = []
        with open(release_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        module.check_release_doc(release_root, [6])
        failed = [item for item in module.CHECKS if not item[1]]
        got_fail = bool(failed)
        if got_fail != expect_fail:
            failures.append(
                "%s: 期望 %s，实际 %s" % (name, "红" if expect_fail else "绿", "红" if got_fail else "绿")
            )

    run_case("RELEASE 基线", valid, False)
    run_case("RELEASE 缺覆盖对账", valid.replace("### 三、阶段 7 覆盖对账", "### 三、其它"), True)
    run_case("RELEASE 缺 tag 后栏", valid.replace("## 二、tag 后追加", "## 二、发布后"), True)
    return failures


def main():
    baseline_tmp = tempfile.mkdtemp(prefix="layout-baseline-")
    try:
        copy_repo(os.path.join(baseline_tmp, "repo"))
        code, output = run_gate(os.path.join(baseline_tmp, "repo"))
        if code != 0:
            print("基线未绿，无法做变异验证：")
            print(output)
            return 2
        print("PASS  基线                                          全绿")
    finally:
        shutil.rmtree(baseline_tmp, ignore_errors=True)

    failures = []
    for expected_id, mutate in MUTATIONS:
        tmp = tempfile.mkdtemp(prefix="layout-mutation-")
        try:
            repo = os.path.join(tmp, "repo")
            copy_repo(repo)
            mutate(repo)
            code, output = run_gate(repo)
            caught = code == 1 and expected_id in output and "FAIL" in output
            print(
                "%s  %-18s  %s"
                % (
                    "PASS" if caught else "FAIL",
                    expected_id,
                    "门已变红" if caught else "门未红（假门）",
                )
            )
            if not caught:
                failures.append(expected_id)
                print(output)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    tmp = tempfile.mkdtemp(prefix="layout-release-")
    try:
        copy_repo(os.path.join(tmp, "repo"))
        release_failures = check_release_mutations(os.path.join(tmp, "repo"))
        for failure in release_failures:
            print("FAIL  LAYOUT.RELEASE      %s" % failure)
        if release_failures:
            failures.append("LAYOUT.RELEASE")
        else:
            print("PASS  LAYOUT.RELEASE      两栏与覆盖对账子判据均已证伪")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 56)
    if failures:
        print("结论: %d 项变异未被捕获" % len(failures))
        return 1
    print("结论: 全部变异均被捕获（门不是假门）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
