import pytest

from anything_to_skill.chunk import chunk_markdown
from anything_to_skill.resolve import build_anchor_index, resolve_citation, nearest_anchor


def test_resolves_citation_to_block_text():
    blocks = chunk_markdown("a\n\nbeta gamma\n", "S1")
    idx = build_anchor_index({"S1": blocks})
    assert resolve_citation("[S1-b0001]", idx) == "beta gamma"


def test_nearest_anchor_by_line():
    md = "linha0\n\nlinha2\n\nlinha4\n"
    blocks = chunk_markdown(md, "S1")
    assert nearest_anchor(blocks, "S1#L2") in {"S1-b0001", "S1-b0000"}


def test_nearest_anchor_no_line_defaults_first():
    blocks = chunk_markdown("a\n\nb\n", "S1")
    assert nearest_anchor(blocks, None) == "S1-b0000"


def test_resolve_missing_anchor_raises():
    with pytest.raises(KeyError):
        resolve_citation("[S1-b9999]", {"S1-b0000": "x"})
