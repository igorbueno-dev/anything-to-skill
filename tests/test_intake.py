import json
from pathlib import Path

from anything_to_skill.intake import register_sources, Source


def test_registers_markdown_source_with_stable_id(tmp_path):
    src = tmp_path / "sample.md"
    src.write_text("# Prompt Engineering\n\nfew-shot works.\n", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    sources = register_sources([src], out)

    assert len(sources) == 1
    s = sources[0]
    assert s.id == "S1"
    assert s.title == "Prompt Engineering"
    assert s.kind == "md"
    assert s.origin == str(src.resolve())

    data = json.loads((out / "sources.json").read_text(encoding="utf-8"))
    assert data[0]["id"] == "S1"
    assert data[0]["title"] == "Prompt Engineering"


def test_ids_increment_in_order(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("# A\n", encoding="utf-8")
    b = tmp_path / "b.txt"
    b.write_text("plain\n", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    sources = register_sources([a, b], out)

    assert [s.id for s in sources] == ["S1", "S2"]
    assert sources[1].kind == "txt"
    assert sources[1].title == "b"
