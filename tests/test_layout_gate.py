# -*- coding: utf-8 -*-
import importlib.util
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GATE = os.path.join(ROOT, "tools", "check_sprint_layout.py")


def _run_gate(root):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, GATE, "--root", root],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding="utf-8",
        env=env,
    )


def test_layout_gate_is_green():
    proc = _run_gate(ROOT)
    assert proc.returncode == 0, proc.stdout
    assert "全绿" in proc.stdout
    assert "这轮扫到" in proc.stdout


def test_layout_gate_reports_scan_counts():
    proc = _run_gate(ROOT)
    assert "状态副本 3" in proc.stdout
    assert "文档点名工具" in proc.stdout


def _load_gate():
    spec = importlib.util.spec_from_file_location("layout_gate_test", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_release(root, text):
    plan = os.path.join(root, "plan")
    os.makedirs(plan, exist_ok=True)
    with open(os.path.join(plan, "RELEASE-M6.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


VALID_RELEASE = """# RELEASE-M6

## 一、tag 前事实

- v0.1.0

## 二、tag 后追加

- 追加提交

### 三、阶段 7 覆盖对账

| 出口门 | 状态 | 证据 |
|---|---|---|
| 本体 | 实现 | 下载件 |
| 源码包 | 不适用 | 单文件形态 |
| CI | 待首推 | 首推后回填 |
"""


def test_release_doc_two_columns_and_coverage(tmp_path):
    module = _load_gate()
    _write_release(str(tmp_path), VALID_RELEASE)
    module.CHECKS[:] = []
    module.check_release_doc(str(tmp_path), [6])
    assert all(item[1] for item in module.CHECKS), module.CHECKS


def test_release_doc_missing_coverage_is_red(tmp_path):
    module = _load_gate()
    _write_release(str(tmp_path), VALID_RELEASE.replace("### 三、阶段 7 覆盖对账", "### 三、其它"))
    module.CHECKS[:] = []
    module.check_release_doc(str(tmp_path), [6])
    assert any(not item[1] for item in module.CHECKS)


def test_release_doc_missing_post_tag_column_is_red(tmp_path):
    module = _load_gate()
    _write_release(str(tmp_path), VALID_RELEASE.replace("## 二、tag 后追加", "## 二、发布后"))
    module.CHECKS[:] = []
    module.check_release_doc(str(tmp_path), [6])
    assert any(not item[1] for item in module.CHECKS)


def test_handoff_m1_has_seven_sections():
    path = os.path.join(ROOT, "plan", "HANDOFF-M1.md")
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    for needle in (
        "证据",
        "当前事实",
        "待办",
        "（K 编号",
        "环境坑",
        "DoD",
        "命令速查",
    ):
        assert needle in text, needle


def test_handoff_m2_has_seven_sections():
    path = os.path.join(ROOT, "plan", "HANDOFF-M2.md")
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    for needle in (
        "证据",
        "当前事实",
        "待办",
        "（K 编号",
        "环境坑",
        "DoD",
        "命令速查",
    ):
        assert needle in text, needle
