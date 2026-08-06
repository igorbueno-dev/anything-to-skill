from pathlib import Path

from anything_to_skill.intake import Source
from anything_to_skill.emit import emit_skill


def _fixture(name):
    return Path(__file__).parent / "fixtures" / name


def test_emits_router_sections_and_preserves_content(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# Prompt Engineering\n\nfew-shot works.\n", encoding="utf-8")
    sources = [Source(id="S1", title="Prompt Engineering", kind="md",
                      origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"

    result = emit_skill(_fixture("graph.sample.json"), sources, content, out)

    assert result == out
    skill_md = (out / "SKILL.md").read_text(encoding="utf-8")
    assert "Few-shot prompting" in skill_md
    assert "Chain of thought" in skill_md
    assert "[Sn·loc]" in skill_md
    assert (out / "sections" / "few-shot-prompting.md").exists()
    assert (out / "sections" / "chain-of-thought.md").exists()
    assert (out / "content" / "S1.md").read_text(encoding="utf-8") == \
        "# Prompt Engineering\n\nfew-shot works.\n"
    assert (out / ".graph" / "graph.json").exists()
    assert "S1" in (out / "sources.md").read_text(encoding="utf-8")


def test_emitter_uses_profile_and_cross_index(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# PE\n\nAbstract\nEstudo.\nReferences\n[1] x et al.\n",
                                   encoding="utf-8")
    sources = [Source(id="S1", title="PE", kind="md", origin="/abs/S1.md", profile="paper")]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    sec = next((out / "sections").glob("*.md")).read_text(encoding="utf-8")
    assert "## Achados" in sec  # template de paper
    assert (out / "glossary.md").exists()
    smd = (out / "sources.md").read_text(encoding="utf-8")
    assert "Temas" in smd and "S1" in smd


def test_generated_skill_has_frontmatter(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# T\n\ntexto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "minha-skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    skill = (out / "SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\n")
    assert "name: minha-skill" in skill
    assert "description:" in skill
    # os temas viram gatilho na descrição
    assert "Few-shot prompting" in skill


def test_section_cites_block_anchor(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("intro\n\nfew-shot detalhe aqui\n", encoding="utf-8")
    sources = [Source(id="S1", title="PE", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    sec = (out / "sections" / "few-shot-prompting.md").read_text(encoding="utf-8")
    assert "[S1·S1-b" in sec
    assert (out / ".graph" / "anchors.json").exists()
