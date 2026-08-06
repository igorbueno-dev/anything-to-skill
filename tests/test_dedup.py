from anything_to_skill.dedup import normalize_label, dedup_nodes, remap_edges


def test_normalize_label_strips_accents_and_case():
    assert normalize_label("Hábito Atômico") == normalize_label("habito atomico")


def test_dedup_merges_same_label_across_sources():
    nodes = [
        {"id": "a", "label": "Hábito", "source_file": "S1.md", "source_location": "S1.md#L1"},
        {"id": "b", "label": "habito", "source_file": "S2.md", "source_location": "S2.md#L5"},
        {"id": "c", "label": "Outro", "source_file": "S1.md", "source_location": "S1.md#L9"},
    ]
    reps, id_map = dedup_nodes(nodes)
    assert len(reps) == 2
    hab = next(r for r in reps if normalize_label(r["label"]) == "habito")
    assert hab["evidence_weight"] == 2
    assert id_map["b"] == id_map["a"]


def test_dedup_keeps_empty_labels_distinct():
    nodes = [
        {"id": "a", "label": "", "source_file": "S1.md", "source_location": "S1.md#L1"},
        {"id": "b", "label": "", "source_file": "S1.md", "source_location": "S1.md#L2"},
    ]
    reps, _ = dedup_nodes(nodes)
    assert len(reps) == 2


def test_remap_edges_drops_self_loops():
    id_map = {"a": "a", "b": "a"}
    edges = [{"source": "a", "target": "b", "relation": "x"}]
    assert remap_edges(edges, id_map) == []
