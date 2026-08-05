from __future__ import annotations

import re

from .chunk import Block

_CITE = re.compile(r"\[(?P<sid>S\d+)·(?P<anchor>[^\]]+)\]")


def build_anchor_index(blocks_by_source: dict[str, list[Block]]) -> dict[str, str]:
    idx: dict[str, str] = {}
    for blocks in blocks_by_source.values():
        for b in blocks:
            idx[b.anchor] = b.text
    return idx


def nearest_anchor(blocks: list[Block], raw_location: str | None) -> str:
    """Casa um source_location cru (`Sn#L{n}`) ao bloco cuja linha inicial é a
    maior que não passa da linha alvo; fallback: primeiro bloco."""
    if not blocks:
        return ""
    m = re.search(r"#L(\d+)", raw_location or "")
    if not m:
        return blocks[0].anchor
    line = int(m.group(1))
    chosen = blocks[0]
    for b in blocks:
        if b.line <= line:
            chosen = b
        else:
            break
    return chosen.anchor


def resolve_citation(citation: str, index: dict[str, str]) -> str:
    m = _CITE.search(citation)
    if not m:
        raise ValueError(f"citação malformada: {citation!r}")
    anchor = m.group("anchor")
    if anchor not in index:
        raise KeyError(f"âncora inexistente: {anchor}")
    return index[anchor]
