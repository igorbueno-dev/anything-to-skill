from pathlib import Path

from anything_to_skill.build import build_skill


def fake_extractor(detect_result, content_dir):
    nodes = []
    for f in sorted(Path(content_dir).iterdir()):
        nodes.append({
            "id": f"{f.stem}_root",
            "label": f.stem,
            "file_type": "concept",
            "source_file": f.name,
            "source_location": f"{f.stem}#L1",
            "source_url": None, "captured_at": None, "author": None, "contributor": None,
        })
    return {"nodes": nodes, "edges": []}


def test_build_writes_qa_report(tmp_path):
    src = tmp_path / "sample.md"
    src.write_text("# T\n\nBoa prosa completa e legivel aqui dentro.\n", encoding="utf-8")
    out = build_skill([src], tmp_path / "work", tmp_path / "skill", extractor=fake_extractor)
    report = out / ".qa" / "extraction_report.md"
    assert report.exists()
    assert "S1" in report.read_text(encoding="utf-8")


def test_failed_source_excluded_from_sections(tmp_path):
    good = tmp_path / "good.md"
    good.write_text("# Good\n\nBoa prosa completa e legivel aqui dentro.\n", encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text("he�llo cid:44 w o r l d", encoding="utf-8")
    out = build_skill([good, bad], tmp_path / "work", tmp_path / "skill",
                      extractor=fake_extractor)
    report = (out / ".qa" / "extraction_report.md").read_text(encoding="utf-8")
    assert "⚑" in report  # fonte ruim marcada como failed
    secs = "\n".join(s.read_text(encoding="utf-8") for s in (out / "sections").glob("*.md"))
    assert "S2" not in secs  # citações da fonte ruim ausentes das seções
