from __future__ import annotations

import re
from typing import Callable

_TS = re.compile(r"\b\d{1,2}:\d{2}\b")
_SPEAKER = re.compile(r"(?m)^[A-ZÀ-Ý][\wÀ-ÿ]+:\s")
_CODE = re.compile(r"```")


def classify(text: str, kind: str) -> str:
    """Classifica a fonte num perfil que determina o template de seção."""
    t = text
    if re.search(r"\bAbstract\b", t) and re.search(r"\bReferences\b|doi:|et al\.", t):
        return "paper"
    if len(_TS.findall(t)) >= 2 or len(_SPEAKER.findall(t)) >= 2:
        return "transcript"
    if len(_CODE.findall(t)) >= 4 or len(re.findall(r"(?m)^#{2,3}\s+\d+\.\d+", t)) >= 2:
        return "technical_book"
    defs = len(re.findall(r"(?m)^\s*[-*]\s+\*\*[^*]+\*\*\s*[—:-]", t))
    if defs >= 5:
        return "reference"
    return "article"


def refine_with(text: str, base: str, refiner: Callable[[str], str] | None) -> str:
    """Aplica um refinador (LLM injetado) sobre o palpite heurístico; sem refinador,
    devolve o base."""
    if refiner is None:
        return base
    return refiner(text) or base
