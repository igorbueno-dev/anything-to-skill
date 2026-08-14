from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from collections import Counter

from .intake import Source
from .chunk import chunk_markdown
from .resolve import build_anchor_index, nearest_anchor
from .templates import render_section

# nome parecido com o módulo templates.py importado acima: não crie __init__.py em templates/, risco de sombreamento.
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "tema"


def _build_description(themes: list[str], subject: str | None, n_sources: int,
                       *, budget: int = 160, max_themes: int = 6) -> str:
    """Descrição enxuta para o frontmatter: gatilhos = nomes de tema, sem
    repetição, cortados por orçamento de caracteres e resumindo o excedente."""
    shown: list[str] = []
    used = 0
    for t in themes:
        if shown and (used + len(t) + 2 > budget or len(shown) >= max_themes):
            break
        shown.append(t)
        used += len(t) + 2
    extra = len(themes) - len(shown)
    phrase = ", ".join(shown) if shown else "o corpus"
    if extra > 0:
        phrase += f" e mais {extra} tema" + ("s" if extra != 1 else "")
    fonte = f"{n_sources} fonte" + ("s" if n_sources != 1 else "")
    if subject and shown:
        lead = f"sobre {subject}: {phrase}"
    elif subject:
        lead = f"sobre {subject}"
    else:
        lead = f"sobre {phrase}"
    desc = (f"Referência consultável {lead}. Construída de {fonte}, "
            f"com cada afirmação rastreável até o texto original.")
    return desc.replace('"', "'").replace("\n", " ")


def _usage_blocks() -> str:
    """Blocos estáticos na SKILL.md gerada: contrato de fidelidade, protocolo de
    recuperação por intenção, modos de estudo e exemplos de pergunta. Sem LLM."""
    return (
        "## Idioma\n"
        "Responda no idioma do usuário, nunca no idioma das fontes ou desta skill por "
        "padrão. Identifique o idioma pelo histórico da conversa, não só pela última "
        "mensagem: se a entrada não trouxer idioma (por exemplo, apenas um link ou "
        "arquivo), mantenha o idioma que o usuário vem usando. Preserve como estão os "
        "nomes próprios e os trechos de código das fontes.\n\n"
        "## Como usar este acervo\n"
        "Responda somente a partir deste acervo. Se o acervo não cobrir a pergunta, "
        "diga que não está nas fontes, em vez de completar com conhecimento geral.\n\n"
        "## Como citar\n"
        "Cada trecho tem uma âncora interna `[Sn-bNNNN]` (fonte Sn, bloco NNNN). Não "
        "repita essa âncora a cada frase, para não poluir o texto:\n"
        "- Cite por afirmação ou parágrafo, não por frase; agrupe quando a mesma fonte "
        "sustenta ideias seguidas.\n"
        "- No corpo da resposta, use números sequenciais: `[1]`, `[2]`, ...\n"
        "- Ao final, feche com uma seção `Referências` que mapeia cada número à sua "
        "âncora, com o título da fonte e o arquivo, por exemplo: "
        "`[1] <fonte> · content/Sn.md · bloco bNNNN`.\n\n"
        "## Como recuperar\n"
        "- Pergunta ampla (\"me ensina\", \"visão geral\"): varra todas as seções do tema "
        "e o `glossary.md`.\n"
        "- Pergunta específica (\"revisa X\", \"o que é X\"): abra a seção do tema e a "
        "âncora citada; se precisar, faça `grep` sobre `content/`.\n\n"
        "## Modos de estudo\n"
        "Além de responder, esta skill sabe conduzir mapa de dependência, currículo, "
        "debate, flashcards, cobertura cruzada, insights, notas Zettelkasten, quiz, "
        "modo socrático, desafio de ideias e comparação entre perfis de fonte. Também "
        "acompanha progresso de estudo por tema: retomar leitura de onde parou, revisão "
        "espaçada e percentual coberto. O protocolo de cada um está em "
        "`study_modes.md`; leia antes de executar qualquer um deles.\n\n"
        "## Exemplos de pergunta\n"
        "- \"me ensina <tema>\"\n"
        "- \"revisa <tema>\"\n"
        "- \"em que ordem estudo <tema>\"\n"
        "- \"me testa sobre <tema>\"\n"
        "- \"me mostra o mapa de <tema>\"\n"
        "- \"debate comigo sobre <tema>\"\n"
        "- \"registra uma nota sobre <tema>\"\n"
        "- \"quiz sobre <tema>\"\n"
        "- \"me guia por <tema>\"\n"
        "- \"desafia isso: <ideia>\"\n"
        "- \"compara os perfis sobre <tema>\"\n"
        "- \"continua de onde eu parei\"\n"
        "- \"o que eu ainda não revisei\"\n"
        "- \"meu progresso\"\n"
    )


_CITE_ANCHOR = re.compile(r"\[(S\d+-b\d+)\]")


def _summary_ok(summary: str, valid_anchors: set[str]) -> bool:
    """Guarda de fidelidade do resumo: toda citação com âncora deve apontar para
    uma âncora real. Resumo sem âncora inválida passa; com âncora inexistente, cai."""
    return all(a in valid_anchors for a in _CITE_ANCHOR.findall(summary))


def _load_graph(graph_path: Path) -> dict:
    return json.loads(Path(graph_path).read_text(encoding="utf-8"))


def _node_index(graph: dict) -> dict[str, dict]:
    return {n["id"]: n for n in graph.get("nodes", [])}


def _source_id_for(source_file: str | None, sources: list[Source]) -> str:
    """Resolve o ID da fonte (S1..Sn) a partir do source_file de um nó.
    Conteúdo normalizado se chama `{Sn}.md`, então o stem já é o ID; caso
    contrário, casa pelo nome do arquivo original."""
    if not source_file:
        return "S?"
    stem = Path(source_file).stem
    if re.fullmatch(r"S\d+", stem):
        return stem
    return next((s.id for s in sources
                 if Path(s.origin).name == source_file), "S?")


def emit_skill(graph_path: Path, sources: list[Source],
               content_dir: Path, out_dir: Path, *, summarize_fn=None) -> Path:
    graph = _load_graph(graph_path)
    nodes = _node_index(graph)
    communities: dict = graph.get("communities", {})
    labels: dict = graph.get("labels", {})

    out_dir = Path(out_dir)
    (out_dir / "sections").mkdir(parents=True, exist_ok=True)
    (out_dir / "content").mkdir(parents=True, exist_ok=True)
    (out_dir / ".graph").mkdir(parents=True, exist_ok=True)

    # 1. content/ verbatim (fidelidade byte-a-byte) + fatiar em blocos endereçáveis
    blocks_by_source: dict[str, list] = {}
    for f in sorted(Path(content_dir).iterdir()):
        if f.is_file():
            shutil.copy2(f, out_dir / "content" / f.name)
            text = f.read_text(encoding="utf-8", errors="replace")
            blocks_by_source[f.stem] = chunk_markdown(text, f.stem)

    # 2. .graph/graph.json + índice de âncoras (endereçamento)
    shutil.copy2(graph_path, out_dir / ".graph" / "graph.json")
    anchor_index = build_anchor_index(blocks_by_source)
    valid_anchors = set(anchor_index.keys())
    (out_dir / ".graph" / "anchors.json").write_text(
        json.dumps(anchor_index, indent=2, ensure_ascii=False),
        encoding="utf-8")

    # 2b. study_modes.md: protocolo dos modos de estudo, copia verbatim
    shutil.copy2(_TEMPLATES_DIR / "study_modes.md", out_dir / "study_modes.md")

    # 2c. .study/progress.json: estado de progresso do usuario, preservado em rebuilds
    study_dir = out_dir / ".study"
    study_dir.mkdir(parents=True, exist_ok=True)
    progress_path = study_dir / "progress.json"
    if not progress_path.exists():
        progress_path.write_text(
            json.dumps({"temas": {}}, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. sections/: uma por comunidade, template do perfil dominante
    profile_by_sid = {s.id: (s.profile or "article") for s in sources}
    theme_rows = []
    theme_by_sid: dict[str, set[str]] = {}
    for cid, node_ids in communities.items():
        theme = labels.get(str(cid), f"Tema {cid}")
        slug = _slug(theme)
        theme_rows.append((theme, slug))
        items = []
        theme_profiles = []
        for nid in node_ids:
            n = nodes.get(nid, {})
            loc = n.get("source_location")
            sid = _source_id_for(n.get("source_file"), sources)
            anchor = nearest_anchor(blocks_by_source.get(sid, []), loc)
            cite = f"[{anchor}]" if anchor else f"[{sid}]"
            items.append({"label": n.get("label", nid), "citation": cite})
            if sid in profile_by_sid:
                theme_profiles.append(profile_by_sid[sid])
                theme_by_sid.setdefault(sid, set()).add(theme)
        profile = Counter(theme_profiles).most_common(1)[0][0] if theme_profiles else "article"
        body = render_section(profile, theme, items)
        if summarize_fn:
            summary = (summarize_fn(theme, items) or "").strip()
            if summary and _summary_ok(summary, valid_anchors):
                prefix = f"# {theme}\n\n"
                if body.startswith(prefix):
                    body = prefix + summary + "\n\n" + body[len(prefix):]
                else:
                    body = summary + "\n\n" + body
        (out_dir / "sections" / f"{slug}.md").write_text(body, encoding="utf-8")

    # 3a2. tensions.md: contradicoes entre fontes (arestas `contradicts`)
    def _cite_of(n: dict) -> str:
        sid = _source_id_for(n.get("source_file"), sources)
        anchor = nearest_anchor(blocks_by_source.get(sid, []), n.get("source_location"))
        return f"[{anchor}]" if anchor else f"[{sid}]"

    tension_lines = ["# Tensões", ""]
    found_tension = False
    for e in graph.get("edges", []):
        if (e.get("relation") or "").lower() not in {"contradicts", "contradiz"}:
            continue
        a = nodes.get(e.get("source"), {})
        b = nodes.get(e.get("target"), {})
        tension_lines.append(
            f"- **{a.get('label', '?')}** {_cite_of(a)} contradiz "
            f"**{b.get('label', '?')}** {_cite_of(b)}")
        found_tension = True
    if not found_tension:
        tension_lines.append("_(nenhuma contradição detectada)_")
    (out_dir / "tensions.md").write_text("\n".join(tension_lines) + "\n", encoding="utf-8")

    # 3b. glossary.md: conceitos alfabetizados, ancorados
    gloss = sorted(
        (n for n in graph.get("nodes", []) if n.get("file_type") in {"concept", "rationale"}),
        key=lambda n: (n.get("label") or "").lower())
    glines = ["# Glossário", ""]
    for n in gloss:
        sid = _source_id_for(n.get("source_file"), sources)
        anchor = nearest_anchor(blocks_by_source.get(sid, []), n.get("source_location"))
        cite = f"[{anchor}]" if anchor else f"[{sid}]"
        weight = n.get("evidence_weight")
        extra = f" (apoiado por {weight} fontes)" if weight and weight > 1 else ""
        glines.append(f"- **{n.get('label')}** {cite}{extra}")
    (out_dir / "glossary.md").write_text("\n".join(glines) + "\n", encoding="utf-8")

    # 3c. cheatsheet.md: so quando algum perfil pede referencia rapida
    if any((s.profile in {"technical_book", "reference"}) for s in sources):
        (out_dir / "cheatsheet.md").write_text(
            "# Cheatsheet\n\n_(regras de decisão: a preencher a partir de content/)_\n",
            encoding="utf-8")

    # 4. SKILL.md roteador (roteia, nao resume) com frontmatter para o Claude Code
    idx = "\n".join(f"| {t} | `sections/{s}.md` |" for t, s in theme_rows)
    skill_name = _slug(out_dir.name)
    # gatilhos = nomes de tema (curtos), deduplicados e sem os placeholders "Tema N"
    seen_t: set[str] = set()
    themes: list[str] = []
    for t, _ in theme_rows:
        if re.fullmatch(r"Tema \d+", t) or t in seen_t:
            continue
        seen_t.add(t)
        themes.append(t)
    subject = sources[0].title if len(sources) == 1 else None
    description = _build_description(themes, subject, len(sources))
    frontmatter = f'---\nname: {skill_name}\ndescription: "{description}"\n---\n\n'
    skill_md = (
        frontmatter +
        f"# {skill_name}\n\n"
        "Roteador. Abra a secao do tema conforme a pergunta.\n\n"
        "| Tema | Arquivo |\n|---|---|\n" + idx + "\n\n"
        "## Legenda de citacoes\n"
        "`[Sn-bNNNN]` -> fonte Sn, bloco NNNN (ver `sources.md` e `content/`).\n\n"
        + _usage_blocks()
    )
    (out_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # 5. sources.md: registro + indice cruzado tema<->fonte
    src_lines = ["# Fontes", ""]
    for s in sources:
        prof = f" · perfil: {s.profile}" if s.profile else ""
        src_lines.append(f"- **{s.id}** · {s.title} ({s.kind}){prof} · `{s.origin}`")
        temas = sorted(theme_by_sid.get(s.id, set()))
        if temas:
            src_lines.append(f"  - Temas: {', '.join(temas)}")
    (out_dir / "sources.md").write_text("\n".join(src_lines) + "\n", encoding="utf-8")

    # 6. COMO_USAR.md: guia humano de uso, gerado deterministicamente
    guide_lines = [
        f"# Como usar: {skill_name}",
        "",
        description,
        "",
        "## Instalar",
        "",
        f"Mova esta pasta para `~/.claude/skills/{skill_name}/`. Depois disso, a skill "
        f"dispara sozinha quando sua pergunta bate com um dos temas, ou você chama "
        f"direto digitando `/{skill_name}`.",
        "",
        "## Temas cobertos",
        "",
    ]
    guide_lines += [f"- {t}" for t in themes]
    guide_lines += [
        "",
        "## Como perguntar",
        "",
        "**Pra aprender**",
        "- \"me ensina <tema>\"",
        "- \"revisa <tema>\"",
        "- \"em que ordem estudo <tema>\"",
        "- \"me mostra o mapa de <tema>\"",
        "",
        "**Pra praticar**",
        "- \"me testa sobre <tema>\"",
        "- \"quiz sobre <tema>\"",
        "- \"me guia por <tema>\"",
        "",
        "**Pra ir mais fundo**",
        "- \"debate comigo sobre <tema>\"",
        "- \"desafia isso: <ideia>\"",
        "- \"compara os perfis sobre <tema>\"",
        "- \"registra uma nota sobre <tema>\"",
        "",
        "**Pra acompanhar progresso**",
        "- \"continua de onde eu parei\"",
        "- \"o que eu ainda não revisei\"",
        "- \"meu progresso\"",
        "",
        "Protocolo completo de cada modo em `study_modes.md`.",
    ]
    (out_dir / "COMO_USAR.md").write_text(
        "\n".join(guide_lines) + "\n", encoding="utf-8")

    return out_dir
