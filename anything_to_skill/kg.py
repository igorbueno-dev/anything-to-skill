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


def label_communities(G: nx.Graph, communities: dict[int, list[str]]) -> dict[int, str]:
    """Nomeia cada comunidade pelo seu conceito mais central (nó de maior grau).
    Determinístico; fallback para 'Tema N' quando o nó não tem label."""
    labels: dict[int, str] = {}
    for cid, node_ids in communities.items():
        if not node_ids:
            labels[cid] = f"Tema {cid}"
            continue
        central = max(node_ids, key=lambda n: G.degree(n) if n in G else 0)
        lbl = G.nodes[central].get("label") if central in G.nodes else None
        labels[cid] = lbl or f"Tema {cid}"
    return labels


def add_structure_affinity(G: nx.Graph, node_segments: dict[str, str],
                           weight: float = 2.0) -> nx.Graph:
    """Reforça a coesão de unidades estruturais: liga em cadeia os nós de um mesmo
    segmento (mesmo capítulo/título), para o Louvain não dissolver a unidade num tema
    maior. Nunca cria aresta entre segmentos diferentes. Cadeia evita clique O(n^2)."""
    by_seg: dict[str, list[str]] = {}
    for nid, seg in node_segments.items():
        if nid in G:
            by_seg.setdefault(seg, []).append(nid)
    for nodes in by_seg.values():
        for u, v in zip(nodes, nodes[1:]):
            if G.has_edge(u, v):
                G[u][v]["weight"] = G[u][v].get("weight", 1.0) + weight
            else:
                G.add_edge(u, v, weight=weight, relation="mesmo-segmento")
    return G


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
