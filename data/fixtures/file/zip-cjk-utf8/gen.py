#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""file fixture: ZIP with a CJK filename and the UTF-8 flag (0x800) set."""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.dirname(FIXTURE_DIR)
if FILE_DIR not in sys.path:
    sys.path.insert(0, FILE_DIR)

import common  # noqa: E402


def build():
    data = common.build_zip("中文.txt", b"fixture\n")
    facts = common.zip_facts(data)
    if not facts["flag_utf8"]:
        raise RuntimeError("zipfile did not set the UTF-8 flag")
    utf8 = facts["interpretations"]["utf-8"]
    cp437 = facts["interpretations"]["cp437"]
    if not utf8["decodable"] or utf8["name"] != "中文.txt":
        raise RuntimeError("unexpected UTF-8 interpretation: %r" % (utf8,))

    input_block = {
        "path": "zip-cjk-utf8.zip",
        "sha256": facts["archive_sha256"],
        "bytes_hex": common.genlib.hexdump(data),
    }
    expected = {
        "status": "ok",
        "zip_names": [
            {
                "raw_name_hex": facts["raw_name_hex"],
                "flag_bits": facts["flag_bits"],
                "flag_utf8": True,
                "interpretation": "utf-8",
                "name": utf8["name"],
                "alternatives": [
                    {"codec": "cp437", "name": cp437["name"]},
                ],
            }
        ],
        "zipfile_view": facts["zipfile_view"],
        "archive_sha256": facts["archive_sha256"],
        "mutates_input": False,
    }
    return common.payload(input_block, expected, "M5 consumes this fixture; the 0x800 flag selects UTF-8"), {
        "zip-cjk-utf8.zip": data,
    }


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "file/zip-cjk-utf8 fixture generator (M1)",
        )
    )
