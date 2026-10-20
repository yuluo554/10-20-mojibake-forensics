# -*- coding: utf-8 -*-
import json

import pytest

from mojibake_forensics import report


def test_dumps_is_deterministic():
    payload = {"b": 2, "a": 1, "中文": "乱码"}
    assert report.dumps(payload) == report.dumps(payload)


def test_dumps_sorts_keys_and_keeps_unicode():
    text = report.dumps({"b": 1, "a": "雅"})
    assert text.index('"a"') < text.index('"b"')
    assert "雅" in text
    assert "\\u96c5" not in text


def test_dumps_ends_with_single_newline():
    text = report.dumps({"a": 1})
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_not_ready_envelope_fields():
    payload = report.not_ready("explain", "M3")
    assert payload["status"] == "not_ready"
    assert payload["schema"] == "mojibake-forensics/1"
    assert payload["notes"] == ["not_implemented_in_skeleton"]
    assert payload["criteria"]["max_depth"] == 3
    json.dumps(payload)  # must be JSON-serializable


def test_exit_code_values_are_frozen():
    assert report.EXIT_OK == 0
    assert report.EXIT_ATTENTION == 1
    assert report.EXIT_USAGE == 2
    assert report.EXIT_ENV == 3


def test_exit_code_4_is_retired():
    """M5: the skeleton-only code 4 is gone — the constant must not exist."""
    assert not hasattr(report, "EXIT_NOT_READY")


def test_error_envelope_fields():
    payload = report.error("bad_thing", "it went wrong", command="file")
    assert payload["status"] == "error"
    assert payload["code"] == "bad_thing"
    assert payload["message"] == "it went wrong"
    assert payload["command"] == "file"
    assert payload["schema"] == "mojibake-forensics/1"
    json.dumps(payload)  # must be JSON-serializable
