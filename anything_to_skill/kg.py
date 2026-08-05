"""Motor de grafo de conhecimento próprio, sobre networkx.

Faz a fatia que a skill precisa — categorizar arquivos, montar o grafo, detectar
comunidades e serializar — sem depender de nenhum motor externo.
"""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import louvain_communities

_CATEGORIES = {
    ".md": "document", ".markdown": "document", ".txt": "document", ".rst": "document",
    ".html": "document", ".htm": "document",
    ".pdf": "paper", ".epub": "paper", ".docx": "paper",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image",
}


def detect(root: Path) -> dict:
    """Categoriza os arquivos de uma pasta por extensão e conta palavras dos docs."""
    root = Path(root)
    files: dict[str, list[str]] = {}
    total_words = 0
    all_files = [p for p in root.rglob("*") if p.is_file()]
    for p in all_files:
        cat = _CATEGORIES.get(p.suffix.lower(), "other")
        files.setdefault(cat, []).append(str(p))
        if cat == "document":
            try:
                total_words += len(p.read_text(encoding="utf-8", errors="replace").split())
            except OSError:
                pass
    return {"files": files, "total_files": len(all_files),
            "total_words": total_words, "scan_root": str(root)}


def build_graph(extraction: dict, *, directed: bool = False) -> nx.Graph:
    """Monta um grafo networkx a partir de {nodes, edges} no schema de extração."""
    G: nx.Graph = nx.DiGraph() if directed else nx.Graph()
    for n in extraction.get("nodes", []):
        nid = n.get("id")
        if nid is None:
            continue
        G.add_node(nid, **{k: v for k, v in n.items() if k != "id"})
    for e in extraction.get("edges", []):
        s, t = e.get("source"), e.get("target")
        if s is None or t is None:
            continue
        G.add_node(s)
        G.add_node(t)
        G.add_edge(s, t, **{k: v for k, v in e.items() if k not in ("source", "target")})
    return G


def cluster(G: nx.Graph) -> dict[int, list[str]]:
    """Detecção de comunidades (Louvain). Grafo sem arestas → cada nó é sua comunidade."""
    if G.number_of_nodes() == 0:
        return {}
    if G.number_of_edges() == 0:
        return {i: [n] for i, n in enumerate(G.nodes())}
    comms = louvain_communities(G, seed=42)
    return {i: sorted(c) for i, c in enumerate(comms)}


def export_graph(G: nx.Graph, communities: dict[int, list[str]], path: Path) -> None:
    """Serializa o grafo (nós com atributos + arestas + comunidades) num JSON."""
    nodes = [{"id": nid, **attrs} for nid, attrs in G.nodes(data=True)]
    edges = [{"source": s, "target": t, **attrs} for s, t, attrs in G.edges(data=True)]
    data = {
        "nodes": nodes,
        "edges": edges,
        "communities": {str(k): list(v) for k, v in communities.items()},
    }
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
