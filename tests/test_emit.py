import json
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


def test_frontmatter_description_is_tight_and_not_duplicated(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# Livro\n\ntexto\n", encoding="utf-8")
    # grafo com muitos temas de rótulos longos, para forçar o corte
    labels = {str(i): f"Conceito bastante longo numero {i} que ocupa muito espaco"
              for i in range(12)}
    nodes = [{"id": f"n{i}", "label": labels[str(i)], "file_type": "concept",
              "source_file": "S1.md", "source_location": "S1.md#L3"} for i in range(12)]
    graph = {"nodes": nodes, "edges": [],
             "communities": {str(i): [f"n{i}"] for i in range(12)},
             "labels": labels}
    gp = tmp_path / "graph.json"
    gp.write_text(json.dumps(graph), encoding="utf-8")
    sources = [Source(id="S1", title="Meu Livro", kind="pdf", origin="/abs/S1.pdf", profile=None)]
    out = tmp_path / "skill"
    emit_skill(gp, sources, content, out)

    skill = (out / "SKILL.md").read_text(encoding="utf-8")
    desc_line = next(l for l in skill.splitlines() if l.startswith("description:"))
    # 1. não repete o gatilho duas vezes (bug antigo)
    assert "Use para responder perguntas" not in skill
    # 2. não despeja todos os temas
    assert desc_line.count("Conceito bastante longo") <= 6
    # 3. resume o excedente
    assert "e mais" in desc_line and "tema" in desc_line
    # 4. tamanho controlado
    assert len(desc_line) <= 400


def test_generated_skill_has_usage_contract(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# T\n\ntexto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    skill = (out / "SKILL.md").read_text(encoding="utf-8")
    # contrato citar-ou-recusar
    assert "Como usar este acervo" in skill
    assert "Cite cada afirmação" in skill
    assert "não está nas fontes" in skill
    # protocolo de recuperação por intenção
    assert "Como recuperar" in skill
    assert "me ensina" in skill.lower()
    assert "revis" in skill.lower()
    # onboarding
    assert "Exemplos de pergunta" in skill


def test_section_summary_with_valid_citation(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("intro\n\nfew-shot detalhe aqui\n", encoding="utf-8")
    sources = [Source(id="S1", title="PE", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"

    def summ(theme, items):
        return f"Resumo do tema {items[0]['citation']}."

    emit_skill(_fixture("graph.sample.json"), sources, content, out, summarize_fn=summ)
    sec = next((out / "sections").glob("*.md")).read_text(encoding="utf-8")
    assert "Resumo do tema" in sec


def test_section_summary_dropped_when_citation_invalid(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("intro\n\nfew-shot detalhe\n", encoding="utf-8")
    sources = [Source(id="S1", title="PE", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"

    def summ(theme, items):
        return "Resumo inventado [S9·nao-existe]."

    emit_skill(_fixture("graph.sample.json"), sources, content, out, summarize_fn=summ)
    secs = "".join(f.read_text(encoding="utf-8") for f in (out / "sections").glob("*.md"))
    assert "Resumo inventado" not in secs


def test_tensions_lists_contradictions(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("alpha afirmacao\n\nbeta afirmacao\n", encoding="utf-8")
    graph = {
        "nodes": [
            {"id": "a", "label": "Alpha", "file_type": "claim",
             "source_file": "S1.md", "source_location": "S1.md#L1"},
            {"id": "b", "label": "Beta", "file_type": "claim",
             "source_file": "S1.md", "source_location": "S1.md#L3"},
        ],
        "edges": [{"source": "a", "target": "b", "relation": "contradicts"}],
        "communities": {"0": ["a", "b"]},
        "labels": {"0": "Alpha"},
    }
    gp = tmp_path / "graph.json"
    gp.write_text(json.dumps(graph), encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(gp, sources, content, out)
    tens = (out / "tensions.md").read_text(encoding="utf-8")
    assert "Alpha" in tens and "Beta" in tens
    assert "contrad" in tens.lower()


def test_tensions_empty_when_none(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("texto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    tens = (out / "tensions.md").read_text(encoding="utf-8")
    assert "nenhuma" in tens.lower()


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
