#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布终态自检门（M6）。

设计口径（ai-tool-project-sprint 阶段 7 E 节）：
- ``--pre-tag``：tag 相关项报 SKIP 不报 FAIL——发布留档与发布门要能随预备提交进 tag 树；
- 离线（默认）：检查 tag 对象 / tag 树内留档 / 本地源码包 + SHA256SUMS / 附件与 tag 树逐字节同源；
- ``--online``：在离线项之外，用 gh 检查公开仓库、Release 与远端附件 sha256；
  环境缺失（gh / 登录 / 远端）退出码 3，不与"发布未达成"（退出码 1）混用。

退出码：0 全绿 / 1 有 FAIL / 3 环境缺失。
**不要把它写进 CI 的必需步骤之外**；CI 只跑 ``--pre-tag``。
"""

from __future__ import print_function

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAG = "v0.1.0"
ARTIFACT_DIR = os.path.join("dist", "release")
ARTIFACT_NAME = "mojibake-forensics-0.1.0.tar.gz"
SUMS_NAME = "SHA256SUMS"

CHECKS = []


class EnvironmentMissing(Exception):
    """gh / 登录 / 远端缺失：退出码 3。"""


def add(check_id, status, detail):
    CHECKS.append((check_id, status, detail))


def path(*parts):
    return os.path.join(ROOT, *parts)


def read_text(rel):
    full = path(rel)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def run(cmd, binary=False):
    """Run a command in ROOT; return (code, stdout, stderr)."""
    proc = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = proc.communicate()
    if not binary:
        out = out.decode("utf-8", "replace")
        err = err.decode("utf-8", "replace")
    return proc.returncode, out, err


def git(*args, **kwargs):
    return run(["git"] + list(args), binary=kwargs.get("binary", False))


def sha256_file(full):
    digest = hashlib.sha256()
    with open(full, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_version_consistency():
    init_text = read_text("src/mojibake_forensics/__init__.py")
    pyproject_text = read_text("pyproject.toml")
    init_version = None
    project_version = None
    if init_text:
        match = re.search(r"^__version__\s*=\s*[\"']([^\"']+)[\"']", init_text, re.MULTILINE)
        if match:
            init_version = match.group(1)
    if pyproject_text:
        match = re.search(r"^version\s*=\s*[\"']([^\"']+)[\"']", pyproject_text, re.MULTILINE)
        if match:
            project_version = match.group(1)
    if not init_version or not project_version:
        add("VERSION", "FAIL", "版本号未找到（__init__ 或 pyproject）")
        return
    if init_version != project_version:
        add("VERSION", "FAIL", "__init__=%s pyproject=%s" % (init_version, project_version))
        return
    add("VERSION", "PASS", "__init__=%s pyproject=%s" % (init_version, project_version))


def check_release_doc(pre_tag):
    rel = "plan/RELEASE-M6.md"
    text = read_text(rel)
    if text is None:
        add("RELEASE_DOC", "FAIL", "缺 %s（发布未达成）" % rel)
        return
    columns = bool(
        re.search(r"^##\s*一、tag 前事实", text, re.MULTILINE)
        and re.search(r"^##\s*二、tag 后追加", text, re.MULTILINE)
    )
    coverage = bool(re.search(r"^#{2,3}.*覆盖对账", text, re.MULTILINE))
    rows = len(re.findall(r"^\|.*(?:实现|不适用|待首推).*\|$", text, re.MULTILINE))
    details = ["两栏:%s" % columns, "覆盖对账:%s" % coverage, "三态行数:%d" % rows]

    placeholder = "<!-- POST_TAG_PLACEHOLDER -->" in text
    if not pre_tag:
        details.append("tag 后栏:%s" % ("待回填" if placeholder else "已填"))
        if placeholder:
            add("RELEASE_DOC", "FAIL", "；".join(details))
            return

    ok = columns and coverage and rows >= 3
    add("RELEASE_DOC", "PASS" if ok else "FAIL", "；".join(details))


def check_tag(pre_tag):
    if pre_tag:
        add("TAG", "SKIP", "tag 前模式：tag 检查留到 tag 后")
        return

    code, out, _err = git("rev-parse", "--verify", "refs/tags/%s^{commit}" % TAG)
    if code != 0:
        add("TAG", "FAIL", "tag %s 不存在" % TAG)
        return

    code, kind, _err = git("cat-file", "-t", TAG)
    annotated = code == 0 and kind.strip() == "tag"
    if not annotated:
        add("TAG", "FAIL", "%s 不是 annotated tag（cat-file=%s）" % (TAG, kind.strip()))
        return

    pyproject_text = read_text("pyproject.toml") or ""
    match = re.search(r"^version\s*=\s*[\"']([^\"']+)[\"']", pyproject_text, re.MULTILINE)
    if match and TAG != "v" + match.group(1):
        add("TAG", "FAIL", "tag=%s 与 pyproject version=%s 不一致" % (TAG, match.group(1)))
        return

    code, ref_line, _err = git(
        "for-each-ref", "--format=%(taggername)|%(taggeremail)", "refs/tags/%s" % TAG
    )
    tagger_name, _, tagger_email = ref_line.strip().partition("|")
    email_ok = bool(
        re.match(r"^[0-9]+\+[^@]+@users\.noreply\.github\.com$", tagger_email)
        or tagger_email.endswith("@users.noreply.github.com")
    )
    name_ok = "ASUS" not in tagger_name and "\\" not in tagger_name and "/" not in tagger_name
    if not email_ok or not name_ok:
        add(
            "TAG",
            "FAIL",
            "tagger 未脱敏：%s <%s>" % (tagger_name, tagger_email),
        )
        return

    code, _out, _err = git("cat-file", "-e", "%s:plan/RELEASE-M6.md" % TAG)
    if code != 0:
        add("TAG", "FAIL", "tag 树缺 plan/RELEASE-M6.md")
        return

    add("TAG", "PASS", "%s annotated；tagger=%s <%s>；tag 树含发布留档" % (
        TAG, tagger_name, tagger_email
    ))


def _tag_tree_hashes():
    """Return {path: sha256(blob)} for every file in the tag tree."""
    code, out, err = git("ls-tree", "-r", "--name-only", TAG)
    if code != 0:
        raise RuntimeError("git ls-tree 失败: %s" % err.strip())
    hashes = {}
    for rel in out.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        code, blob, err = git("show", "%s:%s" % (TAG, rel), binary=True)
        if code != 0:
            raise RuntimeError("git show %s:%s 失败: %s" % (TAG, rel, err.decode("utf-8", "replace")))
        hashes[rel] = hashlib.sha256(blob).hexdigest()
    return hashes


def check_artifacts(pre_tag):
    if pre_tag:
        add("ARTIFACTS", "SKIP", "tag 前模式：本地源码包检查留到 tag 后")
        return

    tarball = path(ARTIFACT_DIR, ARTIFACT_NAME)
    sums = path(ARTIFACT_DIR, SUMS_NAME)
    if not os.path.exists(tarball):
        add("ARTIFACTS", "FAIL", "缺本地副本 %s" % tarball)
        return
    if not os.path.exists(sums):
        add("ARTIFACTS", "FAIL", "缺 %s" % sums)
        return

    digest = sha256_file(tarball)
    recorded = None
    for line in read_text(os.path.join(ARTIFACT_DIR, SUMS_NAME)).splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == ARTIFACT_NAME:
            recorded = parts[0].lower()
            break
    if recorded != digest:
        add("ARTIFACTS", "FAIL", "SHA256SUMS 不匹配：recorded=%s actual=%s" % (recorded, digest))
        return

    try:
        tree = _tag_tree_hashes()
    except Exception as exc:
        add("ARTIFACTS", "FAIL", str(exc))
        return

    try:
        with tarfile.open(tarball, "r:gz") as archive:
            members = [member for member in archive.getmembers() if member.isfile()]
            names = []
            mismatches = []
            for member in members:
                name = member.name
                if not name.startswith("mojibake-forensics-0.1.0/"):
                    mismatches.append("根前缀异常: %s" % name)
                    continue
                rel = name.split("/", 1)[1]
                names.append(rel)
                data = archive.extractfile(member).read()
                actual = hashlib.sha256(data).hexdigest()
                expected = tree.get(rel)
                if expected is None:
                    mismatches.append("附件多出文件: %s" % rel)
                elif actual != expected:
                    mismatches.append("字节不一致: %s" % rel)
            missing = sorted(set(tree) - set(names))
            if missing:
                mismatches.append("附件缺文件: %s" % ",".join(missing[:5]))
            if "plan/RELEASE-M6.md" not in names:
                mismatches.append("附件缺 plan/RELEASE-M6.md")
    except Exception as exc:
        add("ARTIFACTS", "FAIL", "解包失败: %s" % exc)
        return

    if mismatches:
        add("ARTIFACTS", "FAIL", "；".join(mismatches[:5]))
        return
    add(
        "ARTIFACTS",
        "PASS",
        "sha256=%s；%d 个文件与 tag 树逐字节一致" % (digest, len(names)),
    )


def _repo_slug():
    code, out, _err = git("remote", "get-url", "origin")
    if code != 0 or not out.strip():
        raise EnvironmentMissing("没有 origin 远端")
    url = out.strip()
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not match:
        raise EnvironmentMissing("origin 不是 GitHub 仓库: %s" % url)
    return match.group(1), match.group(2)


def _gh(*args):
    if shutil.which("gh") is None:
        raise EnvironmentMissing("gh 不在 PATH")
    code, out, err = run(["gh"] + list(args))
    return code, out, err


def check_online(online):
    if not online:
        add("ONLINE", "SKIP", "未使用 --online")
        return

    code, _out, err = _gh("auth", "status")
    if code != 0:
        raise EnvironmentMissing("gh 未登录: %s" % err.strip().splitlines()[-1] if err.strip() else "gh 未登录")

    owner, repo = _repo_slug()
    full = "%s/%s" % (owner, repo)

    code, out, err = _gh("api", "repos/%s" % full, "--jq", ".visibility + \"|\" + (.private|tostring)")
    if code != 0:
        add("ONLINE", "FAIL", "仓库不可达: %s" % (err.strip() or out.strip()))
        return
    visibility, _, private = out.strip().partition("|")
    if private == "true" or visibility != "public":
        add("ONLINE", "FAIL", "仓库不是公开状态: %s private=%s" % (visibility, private))
        return

    code, out, err = _gh(
        "release", "view", TAG, "--repo", full,
        "--json", "tagName,isDraft,isPrerelease,url,assets",
    )
    if code != 0:
        add("ONLINE", "FAIL", "Release %s 不存在: %s" % (TAG, err.strip()))
        return
    try:
        release = json.loads(out)
    except ValueError as exc:
        add("ONLINE", "FAIL", "Release JSON 解析失败: %s" % exc)
        return
    if release.get("tagName") != TAG:
        add("ONLINE", "FAIL", "Release tagName=%s" % release.get("tagName"))
        return
    if release.get("isDraft") or release.get("isPrerelease"):
        add("ONLINE", "FAIL", "Release 仍是 draft/prerelease")
        return

    assets = {asset.get("name"): asset for asset in release.get("assets", [])}
    required = [ARTIFACT_NAME, SUMS_NAME]
    missing = [name for name in required if name not in assets]
    if missing:
        add("ONLINE", "FAIL", "Release 缺附件: %s" % ",".join(missing))
        return

    temp_dir = tempfile.mkdtemp(prefix="release-online-")
    try:
        for name in required:
            code, _out, err = _gh(
                "release", "download", TAG, "--repo", full,
                "--pattern", name, "--dir", temp_dir, "--clobber",
            )
            if code != 0:
                add("ONLINE", "FAIL", "下载 %s 失败: %s" % (name, err.strip()))
                return
        remote_tar = os.path.join(temp_dir, ARTIFACT_NAME)
        remote_sums = os.path.join(temp_dir, SUMS_NAME)
        remote_digest = sha256_file(remote_tar)
        local_tar = path(ARTIFACT_DIR, ARTIFACT_NAME)
        if not os.path.exists(local_tar):
            add("ONLINE", "FAIL", "远端可下载但本地副本缺失")
            return
        local_digest = sha256_file(local_tar)
        if remote_digest != local_digest:
            add("ONLINE", "FAIL", "远端附件与本地副本 sha256 不一致")
            return
        recorded = None
        with open(remote_sums, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) >= 2 and parts[-1].lstrip("*") == ARTIFACT_NAME:
                    recorded = parts[0].lower()
                    break
        if recorded != remote_digest:
            add("ONLINE", "FAIL", "远端 SHA256SUMS 不匹配")
            return
        add(
            "ONLINE",
            "PASS",
            "仓库 public；Release %s 非 draft；远端附件 sha256=%s 与本地一致" % (
                release.get("url"), remote_digest
            ),
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Release terminal gate (M6)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pre-tag", action="store_true", help="tag 前模式：tag / 附件项 SKIP")
    mode.add_argument("--online", action="store_true", help="联网模式：额外检查公开仓库与 Release")
    parser.add_argument("--root", default=None, help="repository root")
    args = parser.parse_args(argv)

    global ROOT
    if args.root:
        ROOT = os.path.abspath(args.root)

    try:
        check_version_consistency()
        check_release_doc(args.pre_tag)
        check_tag(args.pre_tag)
        check_artifacts(args.pre_tag)
        check_online(args.online)
    except EnvironmentMissing as exc:
        print("发布门: 环境缺失（退出码 3）: %s" % exc)
        return 3
    except Exception as exc:  # 永不崩：被检查对象不存在也要报 FAIL 并继续
        add("UNEXPECTED", "FAIL", "异常: %s" % exc)

    failed = [item for item in CHECKS if item[1] == "FAIL"]
    print("发布终态自检门 · 模式: %s" % (
        "pre-tag" if args.pre_tag else ("online" if args.online else "offline")
    ))
    print("=" * 64)
    for check_id, status, detail in CHECKS:
        print("%-5s  %-12s  %s" % (status, check_id, detail))
    print("=" * 64)
    print("结论: %d PASS / %d FAIL / %d SKIP" % (
        sum(1 for item in CHECKS if item[1] == "PASS"),
        len(failed),
        sum(1 for item in CHECKS if item[1] == "SKIP"),
    ))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
