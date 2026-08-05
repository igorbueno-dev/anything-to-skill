from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .intake import Source


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "tema"


def _load_graph(graph_path: Path) -> dict:
    return json.loads(Path(graph_path).read_text(encoding="utf-8"))


def _node_index(graph: dict) -> dict[str, dict]:
    return {n["id"]: n for n in graph.get("nodes", [])}


def _source_id_for(source_file: str | None, sources: list[Source]) -> str:
    """Resolve o ID da fonte (S1..Sn) a partir do source_file de um nó.
    Conteúdo normalizado se chama `{Sn}.md`, então o stem já é o ID; caso
    contrário, casa pelo nome do arquivo original."""
    if not source_file:
        return "S?"
    stem = Path(source_file).stem
    if re.fullmatch(r"S\d+", stem):
        return stem
    return next((s.id for s in sources
                 if Path(s.origin).name == source_file), "S?")


def emit_skill(graph_path: Path, sources: list[Source],
               content_dir: Path, out_dir: Path) -> Path:
    graph = _load_graph(graph_path)
    nodes = _node_index(graph)
    communities: dict = graph.get("communities", {})
    labels: dict = graph.get("labels", {})

    out_dir = Path(out_dir)
    (out_dir / "sections").mkdir(parents=True, exist_ok=True)
    (out_dir / "content").mkdir(parents=True, exist_ok=True)
    (out_dir / ".graph").mkdir(parents=True, exist_ok=True)

    # 1. content/ verbatim
    for f in sorted(Path(content_dir).iterdir()):
        if f.is_file():
            shutil.copy2(f, out_dir / "content" / f.name)

    # 2. .graph/graph.json
    shutil.copy2(graph_path, out_dir / ".graph" / "graph.json")

    # 3. sections/ — uma por comunidade
    theme_rows = []
    for cid, node_ids in communities.items():
        theme = labels.get(str(cid), f"Tema {cid}")
        slug = _slug(theme)
        theme_rows.append((theme, slug))
        lines = [f"# {theme}", ""]
        for nid in node_ids:
            n = nodes.get(nid, {})
            loc = n.get("source_location")
            sid = _source_id_for(n.get("source_file"), sources)
            cite = f"[{sid}·{loc}]" if loc else f"[{sid}]"
            lines.append(f"- {n.get('label', nid)} {cite}")
        (out_dir / "sections" / f"{slug}.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8")

    # 4. SKILL.md roteador (roteia, nao resume)
    idx = "\n".join(f"| {t} | `sections/{s}.md` |" for t, s in theme_rows)
    skill_md = (
        "# anything-to-skill (gerada)\n\n"
        "Roteador. Abra a secao do tema conforme a pergunta.\n\n"
        "| Tema | Arquivo |\n|---|---|\n" + idx + "\n\n"
        "## Legenda de citacoes\n"
        "`[Sn·loc]` -> fonte Sn no local `loc` (ver `sources.md` e `content/`).\n"
    )
    (out_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # 5. sources.md
    src_lines = ["# Fontes", ""]
    for s in sources:
        src_lines.append(f"- **{s.id}** — {s.title} ({s.kind}) — `{s.origin}`")
    (out_dir / "sources.md").write_text("\n".join(src_lines) + "\n", encoding="utf-8")

    return out_dir
