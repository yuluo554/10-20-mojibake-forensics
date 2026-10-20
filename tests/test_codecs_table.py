# -*- coding: utf-8 -*-
from mojibake_forensics import codecs_table


EXPECTED_ENCODERS = (
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
)

EXPECTED_DECODERS = (
    "utf-8",
    "gb18030",
    "big5",
    "shift_jis",
    "euc-kr",
    "cp1252",
    "latin-1",
)


def test_encoder_set_is_frozen():
    assert codecs_table.ENCODERS == EXPECTED_ENCODERS


def test_decoder_set_is_frozen():
    assert codecs_table.DECODERS == EXPECTED_DECODERS


def test_max_depth_is_three():
    assert codecs_table.MAX_DEPTH == 3


def test_declared_codecs_are_available():
    assert codecs_table.missing_codecs() == ()


def test_criteria_block_is_stable():
    criteria = codecs_table.criteria()
    assert criteria["encoders"] == list(EXPECTED_ENCODERS)
    assert criteria["decoders"] == list(EXPECTED_DECODERS)
    assert criteria["max_depth"] == 3


def test_missing_codecs_reports_unknown_names():
    assert codecs_table.missing_codecs(encoders=("no-such-codec",)) == ("no-such-codec",)
