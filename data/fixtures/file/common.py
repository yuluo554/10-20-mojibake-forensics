# -*- coding: utf-8 -*-
"""Shared helpers for the raw-byte file fixtures (M1).

Deterministic ZIP construction: ``ZIP_STORED``, ``create_system=0``, fixed
timestamp ``(1980, 1, 1, 0, 0, 0)`` and zeroed attrs. Standard library only.
"""

from __future__ import print_function

import io
import os
import struct
import sys
import zipfile

FIXTURES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if FIXTURES_DIR not in sys.path:
    sys.path.insert(0, FIXTURES_DIR)

import genlib  # noqa: E402


CRITERIA = {
    "encoders": [
        "utf-8",
        "gb18030",
        "gbk",
        "big5",
        "shift_jis",
        "euc-jp",
        "euc-kr",
        "cp1252",
        "latin-1",
        "cp437",
    ],
    "decoders": [
        "utf-8",
        "gb18030",
        "big5",
        "shift_jis",
        "euc-kr",
        "cp1252",
        "latin-1",
    ],
    "max_depth": 3,
}


def payload(input_block, expected_block, note):
    return {
        "input": input_block,
        "expected": expected_block,
        "criteria": CRITERIA,
        "note": note,
    }


def build_zip(name, content):
    """Build a single-entry deterministic ZIP (UTF-8 flag set by zipfile)."""
    buffer = io.BytesIO()
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 0
    info.external_attr = 0
    info.internal_attr = 0
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(info, content)
    return buffer.getvalue()


def clear_utf8_flag(data):
    """Clear general-purpose bit 0x800 in both the local and central headers."""
    out = bytearray(data)
    local = data.index(b"PK\x03\x04")
    central = data.index(b"PK\x01\x02")
    for offset in (local + 6, central + 8):
        flags = struct.unpack("<H", bytes(out[offset : offset + 2]))[0]
        struct.pack_into("<H", out, offset, flags & ~0x0800)
    return bytes(out)


def zip_facts(data):
    """Read the single central-directory entry without extracting members."""
    central = data.index(b"PK\x01\x02")
    flags = struct.unpack("<H", data[central + 8 : central + 10])[0]
    name_length = struct.unpack("<H", data[central + 28 : central + 30])[0]
    extra_length = struct.unpack("<H", data[central + 30 : central + 32])[0]
    comment_length = struct.unpack("<H", data[central + 32 : central + 34])[0]
    raw_name = data[central + 46 : central + 46 + name_length]

    interpretations = {}
    for codec in ("utf-8", "cp437"):
        try:
            interpretations[codec] = {
                "decodable": True,
                "name": raw_name.decode(codec),
            }
        except UnicodeDecodeError:
            interpretations[codec] = {"decodable": False, "name": None}

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.infolist()[0]
        zipfile_view = {
            "filename": info.filename,
            "flag_bits": info.flag_bits,
            "compress_type": info.compress_type,
            "create_system": info.create_system,
        }

    return {
        "flag_bits": flags,
        "flag_utf8": bool(flags & 0x0800),
        "raw_name_hex": genlib.hexdump(raw_name),
        "name_length": name_length,
        "extra_length": extra_length,
        "comment_length": comment_length,
        "interpretations": interpretations,
        "zipfile_view": zipfile_view,
        "archive_sha256": genlib.sha256_hex(data),
    }


def run(build, fixture_dir, description):
    return genlib.run(build, fixture_dir, description=description)
