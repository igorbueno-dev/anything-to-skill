"""Autoavaliação da skill gerada: gera perguntas do corpus, responde e pontua.

Geração e resposta precisam de LLM, então são injetadas (`qa_gen_fn`, `answer_fn`).
A pontuação é determinista: a resposta cita uma âncora válida (fundamentada)? cita a
âncora esperada?"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvalReport:
    total: int
    correct: int          # respostas que citam ao menos uma âncora válida
    cited_expected: int   # respostas que citam a âncora esperada
    items: list = field(default_factory=list)


def evaluate_skill(skill_dir, *, qa_gen_fn, answer_fn) -> EvalReport:
    skill_dir = Path(skill_dir)
    anchors_path = skill_dir / ".graph" / "anchors.json"
    valid = set(json.loads(anchors_path.read_text(encoding="utf-8")).keys()) \
        if anchors_path.exists() else set()
    content = {f.stem: f.read_text(encoding="utf-8", errors="replace")
               for f in (skill_dir / "content").glob("*.md")}

    qa = qa_gen_fn(content) or []
    correct = 0
    cited_expected = 0
    items = []
    for item in qa:
        ans = answer_fn(item.get("question", ""), skill_dir) or {}
        cited = set(ans.get("cited_anchors", []))
        grounded = any(c in valid for c in cited)
        hit = item.get("expected_anchor") in cited
        correct += 1 if grounded else 0
        cited_expected += 1 if hit else 0
        items.append({
            "question": item.get("question", ""),
            "expected_anchor": item.get("expected_anchor"),
            "cited_anchors": sorted(cited),
            "grounded": grounded,
            "cited_expected": hit,
        })
    return EvalReport(total=len(qa), correct=correct,
                      cited_expected=cited_expected, items=items)


def write_eval_report(report: EvalReport, out_dir) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# Relatorio de autoavaliacao", ""]
    lines.append(f"- Fundamentadas (citam fonte valida): {report.correct}/{report.total}")
    lines.append(f"- Citam a fonte esperada: {report.cited_expected}/{report.total}")
    lines.append("")
    for it in report.items:
        mark = "ok" if it["grounded"] else "falha"
        lines.append(f"- [{mark}] {it['question']} "
                     f"(esperado {it['expected_anchor']}, citou {it['cited_anchors']})")
    p = out_dir / "eval_report.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
