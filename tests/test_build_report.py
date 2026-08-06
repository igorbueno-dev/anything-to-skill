import json
from pathlib import Path

from anything_to_skill.build import build_skill


def _extractor(detect_result, content_dir):
    nodes = []
    for f in sorted(Path(content_dir).iterdir()):
        nodes.append({
            "id": f"{f.stem}_root",
            "label": f.stem.title(),
            "file_type": "concept",
            "source_file": f.name,
            "source_location": f"{f.stem}#L1",
        })
    return {"nodes": nodes, "edges": []}


def test_build_writes_report(tmp_path):
    src = tmp_path / "sample.md"
    src.write_text("# Titulo\n\ncorpo do texto\n", encoding="utf-8")
    out = build_skill([src], tmp_path / "work", tmp_path / "skill", extractor=_extractor)

    assert (out / "build_report.md").exists()
    data = json.loads((out / ".qa" / "build_report.json").read_text(encoding="utf-8"))
    assert data["total_concepts"] == 1
    assert data["total_themes"] >= 1
    s1 = data["sources"][0]
    assert s1["id"] == "S1"
    assert s1["chars"] == len((out / "content" / "S1.md").read_text(encoding="utf-8"))
    assert s1["concepts"] == 1
