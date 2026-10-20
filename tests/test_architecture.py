# -*- coding: utf-8 -*-
import ast
import os
import re

from mojibake_forensics import __version__

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src", "mojibake_forensics")


def test_src_has_no_network_imports():
    forbidden = {"requests", "socket", "http", "urllib", "ftplib", "telnetlib", "smtplib"}
    hits = []
    for name in sorted(os.listdir(SRC)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(SRC, name)
        with open(path, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in forbidden:
                        hits.append((name, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in forbidden:
                    hits.append((name, node.module))
    assert hits == []


def test_src_never_uses_lossy_codec_error_handlers():
    hits = []
    for name in sorted(os.listdir(SRC)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(SRC, name)
        with open(path, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if (
                    keyword.arg == "errors"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value in ("replace", "ignore")
                ):
                    hits.append((name, "errors=%r" % keyword.value.value))
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in ("encode", "decode")
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in ("replace", "ignore")
            ):
                hits.append((name, "%s(..., %r)" % (node.func.attr, node.args[1].value)))
    assert hits == []


def test_src_does_not_read_system_locale():
    hits = []
    for name in sorted(os.listdir(SRC)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(SRC, name), "r", encoding="utf-8") as handle:
            if "getpreferredencoding" in handle.read():
                hits.append(name)
    assert hits == []


def test_version_is_single_source():
    with open(os.path.join(ROOT, "pyproject.toml"), "r", encoding="utf-8") as handle:
        pyproject = handle.read()
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert match is not None
    assert match.group(1) == __version__


def test_readme_mentions_current_version():
    with open(os.path.join(ROOT, "README.md"), "r", encoding="utf-8") as handle:
        readme = handle.read()
    assert __version__ in readme


def test_fixture_directories_exist():
    for module in ("attr", "explain", "recover", "file", "scan"):
        path = os.path.join(ROOT, "data", "fixtures", module, "README.md")
        assert os.path.exists(path), path


def test_fixture_skeleton_subdirs_exist():
    expected = [
        "recover/kun-jin-kao",
        "recover/tang-tang",
        "recover/question-mark",
        "recover/replacement-char",
        "recover/silent-drop",
        "file/bom-conflict",
        "file/utf16-misalignment",
        "file/zip-cjk-utf8",
        "file/zip-cjk-cp437",
        "scan/polluted",
    ]
    for rel in expected:
        path = os.path.join(ROOT, "data", "fixtures", rel, "README.md")
        assert os.path.exists(path), path
