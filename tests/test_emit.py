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
    assert "[Sn-bNNNN]" in skill_md
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
    assert "Como citar" in skill
    assert "não está nas fontes" in skill
    # protocolo de recuperação por intenção
    assert "Como recuperar" in skill
    assert "me ensina" in skill.lower()
    assert "revis" in skill.lower()
    # onboarding
    assert "Exemplos de pergunta" in skill


def test_generated_skill_cites_by_number_with_references(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# T\n\ntexto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    skill = (out / "SKILL.md").read_text(encoding="utf-8")
    # convenção numérica + referências, com anti-poluição (por afirmação, não por frase)
    assert "Como citar" in skill
    assert "[1]" in skill and "[2]" in skill
    assert "Referências" in skill
    assert "não por frase" in skill


def test_generated_skill_has_language_directive(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# T\n\ntexto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    skill = (out / "SKILL.md").read_text(encoding="utf-8")
    # a skill gerada deve interagir no idioma do usuário, inferido pela conversa
    assert "## Idioma" in skill
    assert "idioma do usuário" in skill
    assert "histórico da conversa" in skill


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
        return "Resumo inventado [S9-b9999]."

    emit_skill(_fixture("graph.sample.json"), sources, content, out, summarize_fn=summ)
    secs = "".join(f.read_text(encoding="utf-8") for f in (out / "sections").glob("*.md"))
    assert "Resumo inventado" not in secs


def test_glossary_shows_evidence_weight(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("conceito x\n", encoding="utf-8")
    graph = {
        "nodes": [{"id": "a", "label": "Conceito X", "file_type": "concept",
                   "source_file": "S1.md", "source_location": "S1.md#L1",
                   "evidence_weight": 3}],
        "edges": [], "communities": {"0": ["a"]}, "labels": {"0": "Conceito X"},
    }
    gp = tmp_path / "graph.json"
    gp.write_text(json.dumps(graph), encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(gp, sources, content, out)
    gloss = (out / "glossary.md").read_text(encoding="utf-8")
    assert "3 fontes" in gloss


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
    assert "[S1-b" in sec
    assert (out / ".graph" / "anchors.json").exists()


def test_emitted_skill_ships_study_modes_and_router_points_to_it(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# T\n\ntexto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)

    study_modes = (out / "study_modes.md").read_text(encoding="utf-8")
    assert "Mapa de dependência" in study_modes

    asset_path = Path(__file__).parent.parent / "anything_to_skill" / "templates" / "study_modes.md"
    assert (out / "study_modes.md").read_bytes() == asset_path.read_bytes()

    skill = (out / "SKILL.md").read_text(encoding="utf-8")
    assert "## Modos de estudo" in skill
    assert "study_modes.md" in skill
    assert "mapa de <tema>" in skill.lower()
    assert "debate comigo" in skill.lower()
    assert "registra uma nota" in skill.lower()


def test_study_modes_asset_exists_and_covers_all_modes():
    asset = (Path(__file__).parent.parent / "anything_to_skill"
             / "templates" / "study_modes.md")
    assert asset.exists()
    text = asset.read_text(encoding="utf-8")
    for heading in ["Mapa de dependência", "Currículo", "Debate", "Flashcards",
                     "Cobertura cruzada", "Insights", "Notas"]:
        assert heading in text
    assert "depends-on" in text
    assert "tensions.md" in text
    assert "glossary.md" in text


def test_study_modes_asset_covers_fase2_modes():
    asset = (Path(__file__).parent.parent / "anything_to_skill"
             / "templates" / "study_modes.md")
    text = asset.read_text(encoding="utf-8")
    for heading in ["Quiz", "Modo socrático", "Desafia minha ideia",
                     "Comparação entre perfis"]:
        assert heading in text
    assert "perfil" in text.lower()
    # o gatilho "desafia minha ideia" deve pertencer so ao modo novo, nao ao Debate
    debate_section = text.split("## Debate")[1].split("## Flashcards")[0]
    assert "desafia minha ideia" not in debate_section.lower()


def test_router_mentions_fase2_study_modes(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# T\n\ntexto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    skill = (out / "SKILL.md").read_text(encoding="utf-8")
    assert "quiz sobre <tema>" in skill.lower()
    assert "me guia por <tema>" in skill.lower()
    assert "desafia isso" in skill.lower()
    assert "compara os perfis" in skill.lower()


def test_study_modes_triggers_are_not_duplicated_across_sections():
    import re
    asset = (Path(__file__).parent.parent / "anything_to_skill"
             / "templates" / "study_modes.md")
    text = asset.read_text(encoding="utf-8")
    sections = re.split(r"^## ", text, flags=re.MULTILINE)[1:]
    seen: dict[str, str] = {}
    dupes = []
    for section in sections:
        heading = section.splitlines()[0].strip()
        # O gatilho pode se estender por mais de uma linha; captura tudo entre
        # "Gatilho:" e o primeiro fechamento de citacao ou parenteses seguido
        # de ponto final, que marca o fim da lista de gatilhos da secao.
        m = re.search(r'Gatilho:\s*(.*?)(?:"\.|\)\.)', section, re.DOTALL)
        gatilho_text = m.group(1) if m else ""
        phrases = re.findall(r'"([^"]+)"', gatilho_text)
        for phrase in phrases:
            if phrase in seen and seen[phrase] != heading:
                dupes.append((phrase, seen[phrase], heading))
            seen[phrase] = heading
    assert not dupes, f"Gatilhos duplicados entre secoes: {dupes}"


def test_emit_creates_empty_progress_json(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# T\n\ntexto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)
    progress = json.loads((out / ".study" / "progress.json").read_text(encoding="utf-8"))
    assert progress == {"temas": {}}


def test_emit_preserves_existing_progress_json_on_rebuild(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    (content / "S1.md").write_text("# T\n\ntexto\n", encoding="utf-8")
    sources = [Source(id="S1", title="T", kind="md", origin="/abs/S1.md", profile=None)]
    out = tmp_path / "skill"
    emit_skill(_fixture("graph.sample.json"), sources, content, out)

    custom = {"temas": {"Few-shot prompting": {"status": "revisado",
                                                "modos_usados": ["quiz"],
                                                "nota": "usuario ja dominou isso"}}}
    (out / ".study" / "progress.json").write_text(
        json.dumps(custom, ensure_ascii=False), encoding="utf-8")

    emit_skill(_fixture("graph.sample.json"), sources, content, out)

    progress = json.loads((out / ".study" / "progress.json").read_text(encoding="utf-8"))
    assert progress == custom


def test_study_modes_asset_covers_fase3_4_behaviors():
    asset = (Path(__file__).parent.parent / "anything_to_skill"
             / "templates" / "study_modes.md")
    text = asset.read_text(encoding="utf-8")
    for heading in ["Estado de progresso", "Leitura incremental",
                     "Revisão espaçada", "Percentual coberto", "Marco"]:
        assert heading in text
    assert ".study/progress.json" in text
    assert "nao_iniciado" in text or "não_iniciado" in text
    assert "em_andamento" in text
    assert "revisado" in text
