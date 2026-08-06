"""Segmentação de markdown por títulos, para orientar densidade e temas."""
from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass
class Segment:
    heading: str
    level: int
    start_line: int  # 1-based
    end_line: int    # 1-based, inclusivo
    word_count: int


def segment_by_headings(md: str) -> list[Segment]:
    """Fatia o texto em segmentos por título. Conteúdo antes do 1o título vira
    '(preambulo)'. Sem título nenhum, o documento inteiro é um segmento."""
    lines = md.splitlines()
    heads: list[tuple[int, int, str]] = []  # (idx0, level, texto)
    for i, ln in enumerate(lines):
        m = _HEADING.match(ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))

    segments: list[Segment] = []
    first = heads[0][0] if heads else len(lines)
    if first > 0:
        wc = sum(len(l.split()) for l in lines[0:first])
        segments.append(Segment("(preambulo)", 0, 1, first, wc))
    for idx, (li, level, text) in enumerate(heads):
        nxt = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        wc = sum(len(l.split()) for l in lines[li:nxt])
        segments.append(Segment(text, level, li + 1, nxt, wc))
    return segments


def segment_index_for_line(segments: list[Segment], line: int) -> int:
    """Índice do segmento que contém a linha 1-based, ou -1."""
    for i, s in enumerate(segments):
        if s.start_line <= line <= s.end_line:
            return i
    return -1
