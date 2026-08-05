from pathlib import Path

from anything_to_skill.build import build_skill


def fake_extractor(detect_result, content_dir):
    nodes = []
    for f in sorted(Path(content_dir).iterdir()):
        nodes.append({
            "id": f"{f.stem}_root", "label": f.stem, "file_type": "concept",
            "source_file": f.name, "source_location": f"{f.stem}#L1",
            "source_url": None, "captured_at": None, "author": None, "contributor": None,
        })
    return {"nodes": nodes, "edges": []}


def test_build_writes_verification_report(tmp_path):
    src = tmp_path / "sample.md"
    src.write_text("# T\n\nBoa prosa completa e legivel aqui dentro.\n", encoding="utf-8")
    out = build_skill([src], tmp_path / "work", tmp_path / "skill", extractor=fake_extractor)
    report = out / ".qa" / "verification_report.md"
    assert report.exists()
    # sem citações órfãs num build limpo → status pass
    assert "pass" in report.read_text(encoding="utf-8").splitlines()[0]
