import json

from anything_to_skill.kg import detect, build_graph, cluster, export_graph


def test_detect_categorizes(tmp_path):
    (tmp_path / "a.md").write_text("um dois tres", encoding="utf-8")
    (tmp_path / "b.txt").write_text("quatro cinco", encoding="utf-8")
    r = detect(tmp_path)
    assert r["total_files"] == 2
    assert r["total_words"] == 5
    assert any(p.endswith("a.md") for p in r["files"].get("document", []))


def test_build_graph_preserves_node_attrs():
    ext = {"nodes": [{"id": "n1", "label": "L1", "source_file": "S1.md",
                      "source_location": "S1.md#L3", "file_type": "concept"}],
           "edges": []}
    G = build_graph(ext)
    assert "n1" in G.nodes
    assert G.nodes["n1"]["label"] == "L1"
    assert G.nodes["n1"]["source_location"] == "S1.md#L3"


def test_build_graph_edges():
    ext = {"nodes": [{"id": "a"}, {"id": "b"}],
           "edges": [{"source": "a", "target": "b", "relation": "r"}]}
    G = build_graph(ext)
    assert G.has_edge("a", "b")


def test_cluster_covers_all_nodes():
    G = build_graph({"nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
                     "edges": [{"source": "a", "target": "b"}]})
    comms = cluster(G)
    allnodes = {n for ids in comms.values() for n in ids}
    assert allnodes == {"a", "b", "c"}


def test_cluster_empty_graph():
    assert cluster(build_graph({"nodes": [], "edges": []})) == {}


def test_export_graph_writes_nodes_and_edges(tmp_path):
    G = build_graph({"nodes": [{"id": "a", "label": "A", "source_location": "x"}], "edges": []})
    p = tmp_path / "graph.json"
    export_graph(G, {0: ["a"]}, p)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["nodes"][0]["id"] == "a"
    assert data["nodes"][0]["label"] == "A"
    assert data["nodes"][0]["source_location"] == "x"
    assert data["communities"]["0"] == ["a"]
