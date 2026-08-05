from __future__ import annotations

import inspect
import re
from dataclasses import dataclass, field
from pathlib import Path

_WORD = re.compile(r"[A-Za-zÀ-ÿ]+")


def broken_word_ratio(text: str) -> float:
    """1 = palavras com comprimento saudável; baixo = fragmentação de coluna/scan.
    Usa comprimento médio de token (merge de coluna produz muitos fragmentos curtos)."""
    words = _WORD.findall(text)
    if not words:
        return 1.0
    avg = sum(len(w) for w in words) / len(words)
    return min(avg / 5.0, 1.0)


def encoding_artifact_ratio(text: str) -> float:
    if not text:
        return 1.0
    hits = text.count("�") + len(re.findall(r"cid:\d+|/CIDFont", text))
    density = hits / max(len(text) / 100, 1)
    return max(0.0, 1.0 - min(density, 1.0))


def layout_score(text: str) -> float:
    return 1.0 if "\n\n" in text.strip() else 0.6


def text_yield(text: str, *, pages: int | None) -> float:
    """Detecta extração quase-vazia. ~50 chars/página já conta como 'tem texto'."""
    if not pages:
        return 1.0
    per_page = len(text) / pages
    return min(per_page / 50.0, 1.0)


def image_fidelity(extracted: int, embedded_hint: int | None) -> float:
    if embedded_hint is None or embedded_hint == 0:
        return 1.0
    return 1.0 if extracted >= embedded_hint else extracted / embedded_hint


@dataclass
class QAReport:
    source_id: str
    status: str
    scores: dict[str, float] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)


def assess(source_id: str, text: str, *, pages: int | None = None,
           images_extracted: int = 0, images_hint: int | None = None) -> QAReport:
    scores = {
        "broken_word": broken_word_ratio(text),
        "encoding": encoding_artifact_ratio(text),
        "layout": layout_score(text),
        "text_yield": text_yield(text, pages=pages),
        "image_fidelity": image_fidelity(images_extracted, images_hint),
    }
    flags = [k for k, v in scores.items() if v < 0.7]
    if any(v < 0.4 for v in scores.values()):
        status = "failed"
    elif flags:
        status = "partial"
    else:
        status = "clean"
    return QAReport(source_id=source_id, status=status, scores=scores, flags=flags)


def write_qa_report(reports: list[QAReport], out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# Relatório de QA de extração", ""]
    for r in reports:
        mark = {"clean": "✓", "partial": "⚠", "failed": "⚑"}[r.status]
        lines.append(f"## {mark} {r.source_id} — {r.status}")
        for k, v in r.scores.items():
            lines.append(f"- {k}: {v:.2f}")
        if r.flags:
            lines.append(f"- flags: {', '.join(r.flags)}")
        lines.append("")
    p = out_dir / "extraction_report.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


_RANK = {"clean": 2, "partial": 1, "failed": 0}


def _accepts_kwargs(fn) -> bool:
    try:
        return "kind" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def retry_extraction(path, kind, converters, out_images_dir, source_id):
    """Tenta cada conversor na ordem, pontua com assess, retorna o de melhor status;
    para no primeiro 'clean'."""
    best = None
    for conv in converters:
        if _accepts_kwargs(conv):
            doc = conv(path, kind=kind, out_images_dir=out_images_dir, source_id=source_id)
        else:
            doc = conv(path)
        report = assess(source_id, doc.markdown,
                        images_extracted=len(getattr(doc, "images", []) or []))
        if best is None or _RANK[report.status] > _RANK[best[1].status]:
            best = (doc, report)
        if report.status == "clean":
            break
    return best
