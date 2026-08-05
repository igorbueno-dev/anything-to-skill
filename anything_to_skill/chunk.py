from __future__ import annotations

import re
from dataclasses import dataclass

_SPLIT = re.compile(r"\n\s*\n")


@dataclass
class Block:
    anchor: str
    ordinal: int
    text: str
    start: int
    end: int
    line: int = 1


def chunk_markdown(md: str, source_id: str) -> list[Block]:
    blocks: list[Block] = []
    pos = 0
    ordinal = 0
    for chunk in _SPLIT.split(md):
        text = chunk.strip()
        start = md.find(chunk, pos)
        if start < 0:
            start = pos
        end = start + len(chunk)
        pos = end
        if not text:
            continue
        line = md.count("\n", 0, start) + 1
        blocks.append(Block(anchor=f"{source_id}-b{ordinal:04d}", ordinal=ordinal,
                            text=text, start=start, end=end, line=line))
        ordinal += 1
    return blocks


def annotate(md: str, blocks: list[Block]) -> str:
    parts = [f"<!-- {{#{b.anchor}}} -->\n{b.text}" for b in blocks]
    return "\n\n".join(parts) + "\n"
