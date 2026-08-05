from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Callable

from .intake import register_sources
from .emit import emit_skill

Extractor = Callable[[dict, Path], dict]


def build_skill(inputs: list[Path], work_dir: Path, out_dir: Path,
                *, extractor: Extractor) -> Path:
    work_dir = Path(work_dir)
    out_dir = Path(out_dir)
    content = work_dir / "content"
    content.mkdir(parents=True, exist_ok=True)
    for p in inputs:
        shutil.copy2(p, content / Path(p).name)

    sources = register_sources(sorted(content.iterdir()), work_dir)

    from graphify.detect import detect
    from graphify.build import build_from_json
    from graphify.cluster import cluster
    from graphify.export import to_json

    detect_result = detect(content)
    extraction = extractor(detect_result, content)
    G = build_from_json(extraction, root=str(content), directed=False)
    communities = cluster(G)

    graph_path = work_dir / "graph.json"
    to_json(G, communities, str(graph_path))

    # anexa communities+labels legiveis (emit os consome)
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["communities"] = {str(k): list(v) for k, v in communities.items()}
    graph.setdefault("labels", {str(k): f"Tema {k}" for k in communities})
    graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    return emit_skill(graph_path, sources, content, out_dir)
