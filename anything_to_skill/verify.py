from __future__ import annotations

import re
from pathlib import Path

_CITE = re.compile(r"\[(S\d+·[^\]]+)\]")
_QUOTE = re.compile(r'>\s*"([^"]+)"\s*\[(S\d+·[^\]]+)\]')
_CATEGORICAL = re.compile(r"\b(sempre|nunca|garante|garantido|impossível|todos?)\b", re.I)
_HEDGE = re.compile(r"\b(pode|talvez|na maioria|geralmente|evidência fraca|sugere)\b", re.I)


def find_citations(md: str) -> list[str]:
    return _CITE.findall(md)


def check_traceability(sections_dir: Path, anchor_index: dict[str, str]) -> list[str]:
    orphans: list[str] = []
    for f in Path(sections_dir).glob("*.md"):
        for cite in find_citations(f.read_text(encoding="utf-8")):
            anchor = cite.split("·", 1)[1]
            if anchor not in anchor_index:
                orphans.append(cite)
    return orphans


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def extract_quotes(md: str) -> list[tuple[str, str]]:
    return [(q.strip(), c) for q, c in _QUOTE.findall(md)]


def cite_check(quotes: list[tuple[str, str]], anchor_index: dict[str, str]) -> list[str]:
    bad: list[str] = []
    for quote, citation in quotes:
        anchor = citation.split("·", 1)[1]
        block = anchor_index.get(anchor, "")
        if _norm(quote) not in _norm(block):
            bad.append(citation)
    return bad


def nuance_flags(section_md: str, source_text: str) -> list[str]:
    flags: list[str] = []
    if _CATEGORICAL.search(section_md) and _HEDGE.search(source_text):
        flags.append("afirmação categórica sobre fonte que hesita")
    return flags


def security_scan(out_dir: Path) -> list[str]:
    try:
        from graphify import security  # reuso se disponível
        if hasattr(security, "scan_path"):
            return list(security.scan_path(str(out_dir)) or [])
    except Exception:
        pass
    findings: list[str] = []
    pat = re.compile(r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]+PRIVATE KEY-----|ghp_[A-Za-z0-9]{36}")
    for f in Path(out_dir).rglob("*.md"):
        if pat.search(f.read_text(encoding="utf-8", errors="replace")):
            findings.append(str(f))
    return findings


def verify_skill(out_dir: Path, anchor_index: dict[str, str], *,
                 source_texts: dict[str, str]) -> Path:
    out_dir = Path(out_dir)
    sections = out_dir / "sections"
    orphans = check_traceability(sections, anchor_index)
    quotes: list[tuple[str, str]] = []
    nuance: list[str] = []
    for f in sections.glob("*.md"):
        md = f.read_text(encoding="utf-8")
        quotes += extract_quotes(md)
        for sid, txt in source_texts.items():
            if sid in md:
                nuance += nuance_flags(md, txt)
    hallucinated = cite_check(quotes, anchor_index)
    secrets = security_scan(out_dir)
    status = "blocked" if (orphans or hallucinated or secrets) else "pass"
    lines = [f"# Relatório de verificação — {status}", ""]
    lines.append(f"- citações órfãs: {orphans or 'nenhuma'}")
    lines.append(f"- citações alucinadas: {hallucinated or 'nenhuma'}")
    lines.append(f"- alertas de nuance: {nuance or 'nenhum'}")
    lines.append(f"- segredos detectados: {secrets or 'nenhum'}")
    (out_dir / ".qa").mkdir(parents=True, exist_ok=True)
    p = out_dir / ".qa" / "verification_report.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
