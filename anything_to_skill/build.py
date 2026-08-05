from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Callable

from .intake import register_sources
from .normalize import normalize
from .emit import emit_skill
from .qa import assess, write_qa_report
from .profiles import classify
from .verify import verify_skill

Extractor = Callable[[dict, Path], dict]


def _source_id_of(source_file: str | None) -> str:
    from pathlib import Path as _P
    return _P(source_file).stem if source_file else ""


def build_skill(inputs: list[Path], work_dir: Path, out_dir: Path,
                *, extractor: Extractor, vision_describe=None) -> Path:
    work_dir = Path(work_dir)
    out_dir = Path(out_dir)
    content = work_dir / "content"
    content.mkdir(parents=True, exist_ok=True)
    figures = work_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    # registro a partir dos ORIGINAIS (preserva kind/title), conteúdo normalizado
    sources = register_sources([Path(p) for p in inputs], work_dir)
    reports = []
    all_images = []  # (source_id, ImageRef)
    for src, inp in zip(sources, inputs):
        doc = normalize(Path(inp), kind=src.kind, out_images_dir=figures, source_id=src.id)
        (content / f"{src.id}.md").write_text(doc.markdown, encoding="utf-8")
        src.profile = classify(doc.markdown, src.kind)
        reports.append(assess(src.id, doc.markdown,
                              images_extracted=len(doc.images)))
        for img in doc.images:
            all_images.append((src.id, img))

    from graphify.detect import detect
    from graphify.build import build_from_json
    from graphify.cluster import cluster
    from graphify.export import to_json

    detect_result = detect(content)
    extraction = extractor(detect_result, content)

    # fontes 'failed' não alimentam as seções (conteúdo fica pra auditoria no .qa)
    failed = {r.source_id for r in reports if r.status == "failed"}
    if failed:
        kept = [n for n in extraction.get("nodes", [])
                if _source_id_of(n.get("source_file")) not in failed]
        kept_ids = {n["id"] for n in kept}
        extraction["nodes"] = kept
        extraction["edges"] = [e for e in extraction.get("edges", [])
                               if e.get("source") in kept_ids and e.get("target") in kept_ids]

    G = build_from_json(extraction, root=str(content), directed=False)
    communities = cluster(G)

    graph_path = work_dir / "graph.json"
    to_json(G, communities, str(graph_path))

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["communities"] = {str(k): list(v) for k, v in communities.items()}
    graph.setdefault("labels", {str(k): f"Tema {k}" for k in communities})
    graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    result = emit_skill(graph_path, sources, content, out_dir)

    # trilha de auditoria do QA (sempre presente)
    write_qa_report(reports, out_dir / ".qa")

    # copia figuras extraídas pra pasta-skill final
    figure_files = [f for f in figures.iterdir() if f.is_file()]
    if figure_files:
        (out_dir / "figures").mkdir(parents=True, exist_ok=True)
        for f in figure_files:
            shutil.copy2(f, out_dir / "figures" / f.name)
        flines = ["# Figuras", ""]
        for sid, img in all_images:
            desc = vision_describe(figures / img.filename) if vision_describe else "(descrição pendente)"
            flines.append(f"- **{img.filename}** (fonte {sid}, pág {img.page}) — {desc}")
        (out_dir / "figures" / "figures.md").write_text("\n".join(flines) + "\n", encoding="utf-8")

    # verificação final: traceabilidade, cite-check, nuance, segurança
    anchors_path = out_dir / ".graph" / "anchors.json"
    anchor_index = json.loads(anchors_path.read_text(encoding="utf-8")) if anchors_path.exists() else {}
    source_texts = {
        f.stem: f.read_text(encoding="utf-8", errors="replace")
        for f in (out_dir / "content").glob("*.md")
    }
    verify_skill(out_dir, anchor_index, source_texts=source_texts)

    return result
