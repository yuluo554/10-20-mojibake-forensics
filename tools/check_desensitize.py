# -*- coding: utf-8 -*-
"""M6 脱敏扫描：tracked 文本文件里不得出现本机绝对路径 / 主机名。

两层判据：
- 路径形态（``D:\\``、``C:\\Users``、``\\Users\\ASUS`` …）对所有 tracked 文本文件生效；
- 裸主机名 token（``ASUS``）只对文档（README / plan / data / AGENTS）生效——
  ``tests/test_bench.py`` 与 ``tools/check_release.py`` 里把 ``ASUS``
  作为脱敏判据的 needle 使用，属于守门自身，不算泄漏。
"""
import io
import subprocess
import sys

PATH_NEEDLES = [
    "D:" + chr(92) + chr(92),
    "D:" + chr(92),
    "C:" + chr(92) + "Users",
    chr(92) + "Users" + chr(92) + "ASUS",
    "/Users/ASUS",
    "/home/ASUS",
    "ProgramData" + chr(92) + "zcode",
    "AppData" + chr(92) + "Local",
]

DOC_HOST_TOKENS = ["ASUS"]
DOC_PREFIXES = ("README.md", "AGENTS.md", "data/", "plan/")


def _scan(text, needles, where):
    for needle in needles:
        start = 0
        while True:
            idx = text.find(needle, start)
            if idx < 0:
                break
            yield (where, needle, text[max(0, idx - 50):idx + len(needle) + 50].replace("\n", " "))
            start = idx + 1


def main():
    files = subprocess.check_output(
        ["git", "ls-files"], text=True, encoding="utf-8"
    ).splitlines()
    hits = []
    for f in files:
        if f.endswith((".zip", ".bin")):
            continue
        try:
            text = io.open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        hits.extend(_scan(text, PATH_NEEDLES, f))
        if f.replace(chr(92), "/").startswith(DOC_PREFIXES):
            hits.extend(_scan(text, DOC_HOST_TOKENS, f))
    for hit in hits:
        print(hit)
    print("TOTAL", len(hits))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
