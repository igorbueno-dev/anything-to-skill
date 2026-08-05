from pathlib import Path

from anything_to_skill.build import build_skill


def fake_extractor(detect_result, content_dir):
    nodes = []
    for f in sorted(Path(content_dir).iterdir()):
        nodes.append({
            "id": f"{f.stem}_root",
            "label": f.stem.replace('-', ' ').title(),
            "file_type": "concept",
            "source_file": f.name,
            "source_location": f"{f.stem}#L1",
            "source_url": None,
            "captured_at": None,
            "author": None,
            "contributor": None,
        })
    return {"nodes": nodes, "edges": []}


def test_build_produces_valid_skill_folder(tmp_path):
    src = tmp_path / "sample.md"
    src.write_text("# Prompt Engineering\n\nfew-shot.\n", encoding="utf-8")
    out = build_skill([src], tmp_path / "work", tmp_path / "skill",
                      extractor=fake_extractor)
    assert (out / "SKILL.md").exists()
    assert (out / "content" / "sample.md").exists()
    assert (out / ".graph" / "graph.json").exists()
    assert any((out / "sections").glob("*.md"))
