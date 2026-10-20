#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""file fixture: ZIP with a CJK filename and the UTF-8 flag (0x800) cleared.

Without the flag the filename bytes must be interpreted as CP437, so two
readings exist. The tool must list both; it must not pick one for the user.
"""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.dirname(FIXTURE_DIR)
if FILE_DIR not in sys.path:
    sys.path.insert(0, FILE_DIR)

import common  # noqa: E402


def build():
    raw = common.build_zip("中文.txt", b"fixture\n")
    data = common.clear_utf8_flag(raw)
    facts = common.zip_facts(data)
    if facts["flag_utf8"]:
        raise RuntimeError("UTF-8 flag was not cleared")

    utf8 = facts["interpretations"]["utf-8"]
    cp437 = facts["interpretations"]["cp437"]
    if not utf8["decodable"] or utf8["name"] != "中文.txt":
        raise RuntimeError("unexpected UTF-8 interpretation: %r" % (utf8,))
    if not cp437["decodable"]:
        raise RuntimeError("CP437 interpretation failed")

    input_block = {
        "path": "zip-cjk-cp437.zip",
        "sha256": facts["archive_sha256"],
        "bytes_hex": common.genlib.hexdump(data),
    }
    expected = {
        "status": "ok",
        "zip_names": [
            {
                "raw_name_hex": facts["raw_name_hex"],
                "flag_bits": facts["flag_bits"],
                "flag_utf8": False,
                "interpretation": "cp437",
                "name": cp437["name"],
                "alternatives": [
                    {"codec": "utf-8", "name": utf8["name"]},
                ],
                "note": "two interpretations are listed; the tool does not choose",
            }
        ],
        "zipfile_view": facts["zipfile_view"],
        "archive_sha256": facts["archive_sha256"],
        "mutates_input": False,
    }
    return common.payload(input_block, expected, "M5 consumes this fixture; list both readings"), {
        "zip-cjk-cp437.zip": data,
    }


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "file/zip-cjk-cp437 fixture generator (M1)",
        )
    )
