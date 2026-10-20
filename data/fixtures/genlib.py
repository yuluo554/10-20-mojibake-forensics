# -*- coding: utf-8 -*-
"""Shared deterministic helpers for fixture generators.

Fixtures are **data**, not the tool: this module uses the standard library only
and never imports ``mojibake_forensics``. Every expected value is recomputable
from a fixed input with ``codecs``.

Run any generator with ``--check`` to regenerate in memory and compare with the
committed ``expect.json`` and artifact bytes.
"""

from __future__ import print_function

import argparse
import hashlib
import json
import os


def canonical_json(payload):
    """Canonical JSON text: sorted keys, UTF-8 literals, LF, trailing newline."""
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def hexdump(data):
    return " ".join("%02X" % byte for byte in data)


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def write_bytes(path, data):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "wb") as handle:
        handle.write(data)


def transform(text, encoder, decoder):
    """Strict ``text --encode--> bytes --decode--> text`` transform."""
    raw = text.encode(encoder)
    return raw, raw.decode(decoder)


def chain_steps(text, encoder, decoder):
    """Steps of a one-step recovery chain: encode with ``encoder``, decode with
    ``decoder``. Returns ``(steps, result)`` with byte-level evidence."""
    raw = text.encode(encoder)
    result = raw.decode(decoder)
    return (
        [
            {
                "index": 1,
                "op": "encode",
                "codec": encoder,
                "input": text,
                "output_hex": hexdump(raw),
            },
            {
                "index": 2,
                "op": "decode",
                "codec": decoder,
                "input_hex": hexdump(raw),
                "output": result,
            },
        ],
        result,
    )


def verify_steps(steps):
    """Independently replay a step list forward and backwards (strict codecs).

    Returns True iff every recorded intermediate matches exactly.
    """
    if not steps:
        return False
    states = [steps[0]["input"]]
    state = states[0]
    try:
        for step in steps:
            if step["op"] == "encode":
                state = state.encode(step["codec"])
            else:
                state = state.decode(step["codec"])
            states.append(state)
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False
    state = states[-1]
    for index in range(len(steps) - 1, -1, -1):
        step = steps[index]
        inverse = "decode" if step["op"] == "encode" else "encode"
        try:
            state = state.encode(step["codec"]) if inverse == "encode" else state.decode(step["codec"])
        except (UnicodeEncodeError, UnicodeDecodeError):
            return False
        if state != states[index]:
            return False
    return True


def _observed_paths(value, prefix=""):
    found = []
    if isinstance(value, dict):
        for key in sorted(value):
            path = prefix + "/" + key if prefix else key
            if key.startswith("observed_"):
                found.append(path)
            found.extend(_observed_paths(value[key], path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_observed_paths(item, "%s[%d]" % (prefix, index)))
    return found


def run(build, fixture_dir, argv=None, description=None):
    """Run a fixture generator.

    ``build()`` returns ``(expect_payload, artifacts)`` where ``artifacts`` maps
    a fixture-relative POSIX path to bytes. Without ``--check`` the generator
    writes ``expect.json`` and every artifact; with ``--check`` it recomputes and
    compares byte-for-byte without writing.
    """
    parser = argparse.ArgumentParser(description=description or "fixture generator")
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and compare with committed files",
    )
    args = parser.parse_args(argv)

    payload, artifacts = build()
    observed = _observed_paths(payload)
    if observed:
        print("FAIL  expect.json contains observed_* fields: %s" % ", ".join(observed))
        return 1

    expect_bytes = canonical_json(payload).encode("utf-8")
    expect_path = os.path.join(fixture_dir, "expect.json")

    if args.check:
        problems = []
        if not os.path.exists(expect_path):
            problems.append("expect.json missing")
        elif read_bytes(expect_path) != expect_bytes:
            problems.append("expect.json differs")
        for rel in sorted(artifacts):
            path = os.path.join(fixture_dir, *rel.split("/"))
            if not os.path.exists(path):
                problems.append("%s missing" % rel)
            elif read_bytes(path) != artifacts[rel]:
                problems.append("%s differs" % rel)
        for problem in problems:
            print("FAIL  %s" % problem)
        if problems:
            return 1
        print("PASS  %s (%d artifact(s))" % (os.path.basename(fixture_dir), len(artifacts)))
        return 0

    write_bytes(expect_path, expect_bytes)
    for rel in sorted(artifacts):
        write_bytes(os.path.join(fixture_dir, *rel.split("/")), artifacts[rel])
    print(
        "wrote %s/expect.json + %d artifact(s)"
        % (os.path.basename(fixture_dir), len(artifacts))
    )
    return 0
