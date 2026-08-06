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
    # conteúdo normalizado é renomeado por fonte
    assert (out / "content" / "S1.md").exists()
    assert (out / ".graph" / "graph.json").exists()
    assert any((out / "sections").glob("*.md"))


def test_build_from_url(tmp_path):
    html = "<html><body><article><h1>Guia</h1><p>conteudo do guia</p></article></body></html>"
    out = build_skill(["https://exemplo.com/guia"], tmp_path / "work", tmp_path / "skill",
                      extractor=fake_extractor, fetch_fn=lambda u: html)
    assert (out / "content" / "S1.md").exists()
    assert "conteudo do guia" in (out / "content" / "S1.md").read_text(encoding="utf-8")


def test_build_normalizes_pdf(tmp_path):
    pdf = Path(__file__).parent / "fixtures" / "two_col.pdf"
    out = build_skill([pdf], tmp_path / "work", tmp_path / "skill",
                      extractor=fake_extractor)
    assert (out / "content" / "S1.md").exists()
    assert any((out / "figures").glob("*.png"))
