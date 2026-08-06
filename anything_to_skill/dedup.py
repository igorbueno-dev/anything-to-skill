"""Desduplicação de conceitos equivalentes entre fontes, com peso de evidência.

A equivalência semântica pode vir de `similar_fn` injetado; o fallback determinista é
o label normalizado (minúsculas, sem acento/pontuação)."""
from __future__ import annotations

import re
import unicodedata


def normalize_label(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def dedup_nodes(nodes, *, similar_fn=None):
    """Colapsa nós equivalentes num representante que carrega `evidence` (todas as
    origens) e `evidence_weight` (nº de fontes distintas). Retorna (reps, id_map)."""
    reps: list[dict] = []
    groups: list[list[dict]] = []
    id_map: dict[str, str] = {}

    for n in nodes:
        match = None
        for i, rep in enumerate(reps):
            if similar_fn:
                same = similar_fn(n, rep)
            else:
                a, b = normalize_label(n.get("label")), normalize_label(rep.get("label"))
                same = bool(a) and a == b
            if same:
                match = i
                break
        if match is None:
            rep = dict(n)
            reps.append(rep)
            groups.append([n])
            id_map[n["id"]] = rep["id"]
        else:
            groups[match].append(n)
            id_map[n["id"]] = reps[match]["id"]

    for rep, members in zip(reps, groups):
        rep["evidence"] = [{"source_file": m.get("source_file"),
                            "source_location": m.get("source_location")} for m in members]
        rep["evidence_weight"] = len({m.get("source_file") for m in members
                                      if m.get("source_file")})
    return reps, id_map


def remap_edges(edges, id_map):
    """Reaponta arestas para os representantes; descarta laços criados pelo merge."""
    out = []
    for e in edges:
        s = id_map.get(e.get("source"), e.get("source"))
        t = id_map.get(e.get("target"), e.get("target"))
        if s == t:
            continue
        out.append({**e, "source": s, "target": t})
    return out
