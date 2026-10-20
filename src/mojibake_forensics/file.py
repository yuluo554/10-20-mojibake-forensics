# -*- coding: utf-8 -*-
"""M5 · file — raw-byte pipeline diagnostics (BOM, UTF-16, zip names, CSV).

Read-only by construction: the module opens the target with mode ``"rb"`` and
never writes back. Every section reports *evidence* (bytes, offsets, the two
possible readings of a name); it never rewrites the file and never chooses a
single truth where two interpretations are valid (``plan/03`` §六).
"""

from __future__ import absolute_import

import hashlib
import io
import os
import struct
import zipfile

from . import report

MILESTONE = "M5"

CSV_CODECS = ("cp1252", "gbk", "shift_jis")
CSV_DELIMITERS = (",", ";", "\t", "|")

# Longest first: UTF-32LE starts with the UTF-16LE BOM.
BOMS = (
    ("utf-32-le", b"\xff\xfe\x00\x00"),
    ("utf-32-be", b"\x00\x00\xfe\xff"),
    ("utf-8", b"\xef\xbb\xbf"),
    ("utf-16-le", b"\xff\xfe"),
    ("utf-16-be", b"\xfe\xff"),
)


class UsageError(ValueError):
    """Input/usage error: rendered as ``status="error"`` with exit code 2."""

    def __init__(self, code, message):
        super(UsageError, self).__init__(message)
        self.code = code
        self.message = message


def _hexdump(data):
    return " ".join("%02X" % byte for byte in bytearray(data))


def _reason(exc):
    """Short, path-free reason for a read failure (K7: no absolute paths)."""
    if isinstance(exc, FileNotFoundError):
        return "file not found"
    if isinstance(exc, IsADirectoryError):
        return "path is a directory"
    if isinstance(exc, PermissionError):
        return "permission denied"
    return exc.__class__.__name__


def _decode_attempt(data, codec):
    try:
        return {"decodable": True, "text": data.decode(codec)}
    except UnicodeDecodeError as exc:
        return {"decodable": False, "byte_offset": exc.start}


def _sniff_bom(data):
    for kind, bom in BOMS:
        if data.startswith(bom):
            return {
                "present": True,
                "kind": kind,
                "bytes_hex": _hexdump(bom),
                "offset": 0,
            }
    return {"present": False}


def _bom_codec(kind):
    return kind


def _bom_section(data, preset):
    """BOM sniff plus the conflict evidence (body decoded as declared / GB18030)."""
    if preset == "zip-names":
        return None
    bom = _sniff_bom(data)
    section = {"bom": bom, "bom_conflict": False}
    if not bom["present"]:
        return section

    # The hex string is space-grouped byte pairs; Python 2/3 compatible length.
    bom_len = len(bom["bytes_hex"].replace(" ", "")) // 2
    body = data[bom_len:]
    declared = _decode_attempt(body, _bom_codec(bom["kind"]))
    section["bom_conflict"] = not declared["decodable"]
    if section["bom_conflict"]:
        # Evidence only: show what the body is, never rewrite the file.
        section["content"] = {
            "body_hex": _hexdump(body),
            "as_utf8": _decode_attempt(body, "utf-8"),
            "as_gb18030": _decode_attempt(body, "gb18030"),
        }
    return section


def _utf16_section(data, bom):
    """Odd byte count + one-byte shift evidence; no automatic correction."""
    if bom.get("present"):
        # A BOM means a declared UTF-* container; misalignment evidence would
        # just be noise on top of an already-reported conflict.
        return None
    if data[:4] == b"PK\x03\x04":
        return None
    if len(data) % 2 == 0 or len(data) < 3:
        return None

    for codec in ("utf-16-le", "utf-16-be"):
        try:
            data.decode(codec)
            continue
        except UnicodeDecodeError as exc:
            unshifted = {"decodable": False, "byte_offset": exc.start}
        try:
            shifted_text = data[1:].decode(codec)
        except UnicodeDecodeError:
            continue
        return {
            "byte_length": len(data),
            "odd_length": True,
            "unshifted": unshifted,
            "shift_offset": 1,
            "shifted_text": shifted_text,
            "reason": "odd_byte_count",
        }
    return None


def _central_entries(data):
    """Yield ``(flags, raw_name)`` from the central directory without extracting."""
    start = data.rfind(b"PK\x05\x06")
    count = None
    offset = data.find(b"PK\x01\x02")
    if start != -1 and len(data) >= start + 20:
        count = struct.unpack("<H", data[start + 10 : start + 12])[0]
        offset = struct.unpack("<I", data[start + 16 : start + 20])[0]

    entries = []
    cursor = offset
    while cursor >= 0 and cursor + 46 <= len(data) and data[cursor : cursor + 4] == b"PK\x01\x02":
        if count is not None and len(entries) >= count:
            break
        flags = struct.unpack("<H", data[cursor + 8 : cursor + 10])[0]
        name_length = struct.unpack("<H", data[cursor + 28 : cursor + 30])[0]
        extra_length = struct.unpack("<H", data[cursor + 30 : cursor + 32])[0]
        comment_length = struct.unpack("<H", data[cursor + 32 : cursor + 34])[0]
        raw_name = data[cursor + 46 : cursor + 46 + name_length]
        entries.append((flags, raw_name))
        cursor += 46 + name_length + extra_length + comment_length
    return entries


def _zip_section(data):
    """Central-directory names only; member contents are never decompressed."""
    if data[:4] != b"PK\x03\x04":
        return None

    names = []
    for flags, raw_name in _central_entries(data):
        flag_utf8 = bool(flags & 0x0800)
        interpretations = {}
        for codec in ("utf-8", "cp437"):
            try:
                interpretations[codec] = raw_name.decode(codec)
            except UnicodeDecodeError:
                interpretations[codec] = None

        interpretation = "utf-8" if flag_utf8 else "cp437"
        other_codec = "cp437" if flag_utf8 else "utf-8"
        entry = {
            "raw_name_hex": _hexdump(raw_name),
            "flag_bits": flags,
            "flag_utf8": flag_utf8,
            "interpretation": interpretation,
            "name": interpretations[interpretation],
            "alternatives": [],
        }
        if interpretations[other_codec] is not None:
            entry["alternatives"].append(
                {"codec": other_codec, "name": interpretations[other_codec]}
            )
            if not flag_utf8:
                entry["note"] = "two interpretations are listed; the tool does not choose"
        names.append(entry)

    section = {
        "zip_names": names,
        "archive_sha256": hashlib.sha256(data).hexdigest(),
    }
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            views = [
                {
                    "filename": info.filename,
                    "flag_bits": info.flag_bits,
                    "compress_type": info.compress_type,
                    "create_system": info.create_system,
                }
                for info in archive.infolist()
            ]
    except (zipfile.BadZipfile, IOError):
        views = []
    if views:
        section["zipfile_view"] = views[0] if len(views) == 1 else views
    return section


def _csv_section(data, preset):
    if preset != "csv-excel-win":
        return None

    candidates = []
    for codec in CSV_CODECS:
        attempt = _decode_attempt(data, codec)
        candidates.append({"codec": codec, "decodable": attempt["decodable"]})

    sample = data[:4096].decode("latin-1")
    split_lines = sample.splitlines()
    first_line = split_lines[0] if split_lines else ""
    counts = dict((delimiter, first_line.count(delimiter)) for delimiter in CSV_DELIMITERS)
    best = None
    best_count = 0
    for delimiter in CSV_DELIMITERS:
        if counts[delimiter] > best_count:
            best, best_count = delimiter, counts[delimiter]

    return {
        "delimiter": best,
        "delimiter_counts": counts,
        "candidates": candidates,
    }


def inspect_bytes(data, preset=None):
    """Pure, read-only inspection; returns the evidence sections."""
    sections = {}
    bom_section = _bom_section(data, preset)
    if bom_section is not None:
        sections.update(bom_section)
        bom = bom_section["bom"]
    else:
        bom = {"present": False}

    if preset in (None, "utf16"):
        utf16 = _utf16_section(data, bom)
        if utf16 is not None:
            sections["utf16_misalignment"] = utf16

    if preset in (None, "zip-names"):
        zip_section = _zip_section(data)
        if zip_section is not None:
            sections.update(zip_section)

    if preset in (None, "csv-excel-win"):
        csv_section = _csv_section(data, preset)
        if csv_section is not None:
            sections["csv_candidates"] = csv_section

    sections["mutates_input"] = False
    return sections


def inspect_path(path, preset=None):
    """Read-only byte inspection; never writes back (M5)."""
    try:
        handle = io.open(path, "rb")
    except IOError as exc:
        raise UsageError(
            "file_unreadable",
            "cannot open --path for reading (%s)" % _reason(exc),
        )
    try:
        with handle:
            data = handle.read()
    except IOError as exc:
        raise UsageError(
            "file_unreadable",
            "cannot read --path (%s)" % _reason(exc),
        )
    return inspect_bytes(data, preset)


def run(args):
    try:
        sections = inspect_path(args.path, preset=getattr(args, "preset", None))
    except UsageError as exc:
        return report.error(exc.code, exc.message, command="file")

    payload = report.base_envelope("ok")
    payload["command"] = "file"
    payload["path"] = os.path.basename(args.path)
    payload.update(sections)
    payload["notes"] = []
    return payload


def _render_section(name, value):
    lines = []
    if name == "bom":
        if value.get("present"):
            lines.append(
                "bom: %s at offset %d (%s)"
                % (value["kind"], value["offset"], value["bytes_hex"])
            )
        else:
            lines.append("bom: none")
    elif name == "bom_conflict":
        lines.append("bom_conflict: %s" % ("true" if value else "false"))
    elif name == "content":
        lines.append("content body: %s" % value["body_hex"])
        for codec in ("as_utf8", "as_gb18030"):
            attempt = value[codec]
            if attempt["decodable"]:
                lines.append("  %s: decodable %r" % (codec, attempt["text"]))
            else:
                lines.append(
                    "  %s: not decodable (byte offset %s)"
                    % (codec, attempt.get("byte_offset"))
                )
    elif name == "utf16_misalignment":
        lines.append(
            "utf16_misalignment: byte_length=%d odd_length=%s reason=%s shift=%d"
            % (
                value["byte_length"],
                "true" if value["odd_length"] else "false",
                value["reason"],
                value["shift_offset"],
            )
        )
        if value.get("shifted_text") is not None:
            lines.append(
                "  shifted text: %r (evidence only, no auto-fix)" % value["shifted_text"]
            )
    elif name == "zip_names":
        for entry in value:
            lines.append(
                "zip name: %r flag_bits=%d flag_utf8=%s interpretation=%s raw=%s"
                % (
                    entry["name"],
                    entry["flag_bits"],
                    "true" if entry["flag_utf8"] else "false",
                    entry["interpretation"],
                    entry["raw_name_hex"],
                )
            )
            for alternative in entry["alternatives"]:
                lines.append(
                    "  alternative %s: %r" % (alternative["codec"], alternative["name"])
                )
            if entry.get("note"):
                lines.append("  note: %s" % entry["note"])
    elif name == "csv_candidates":
        lines.append(
            "csv candidates: %s; delimiter=%r"
            % (
                ", ".join(
                    "%s=%s" % (item["codec"], "yes" if item["decodable"] else "no")
                    for item in value["candidates"]
                ),
                value["delimiter"],
            )
        )
    elif name == "mutates_input":
        lines.append("mutates_input: false")
    return lines


def render(payload):
    """Stable human-readable text (no color, no clock, no host paths)."""
    if payload.get("status") != "ok":
        return None
    lines = ["file: %s (read-only)" % payload.get("path", "?")]
    for name in (
        "bom",
        "bom_conflict",
        "content",
        "utf16_misalignment",
        "zip_names",
        "csv_candidates",
        "mutates_input",
    ):
        if name in payload:
            lines.extend(_render_section(name, payload[name]))
    return "\n".join(lines) + "\n"
