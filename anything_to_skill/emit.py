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
    recuperação por intenção e exemplos de pergunta. Sem LLM."""
    return (
        "## Como usar este acervo\n"
        "Responda somente a partir deste acervo. Cite cada afirmação com `[Sn·âncora]`. "
        "Se o acervo não cobrir a pergunta, diga que não está nas fontes, em vez de "
        "completar com conhecimento geral.\n\n"
        "## Como recuperar\n"
        "- Pergunta ampla (\"me ensina\", \"visão geral\"): varra todas as seções do tema "
        "e o `glossary.md`.\n"
        "- Pergunta específica (\"revisa X\", \"o que é X\"): abra a seção do tema e a "
        "âncora citada; se precisar, faça `grep` sobre `content/`.\n\n"
        "## Exemplos de pergunta\n"
        "- \"me ensina <tema>\"\n"
        "- \"revisa <tema>\"\n"
        "- \"em que ordem estudo <tema>\"\n"
        "- \"me testa sobre <tema>\"\n"
    )


_CITE_ANCHOR = re.compile(r"\[S\d+·([^\]]+)\]")


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

    # 3. sections/ — uma por comunidade, template do perfil dominante
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
            cite = f"[{sid}·{anchor}]" if anchor else f"[{sid}]"
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

    # 3b. glossary.md — conceitos alfabetizados, ancorados
    gloss = sorted(
        (n for n in graph.get("nodes", []) if n.get("file_type") in {"concept", "rationale"}),
        key=lambda n: (n.get("label") or "").lower())
    glines = ["# Glossário", ""]
    for n in gloss:
        sid = _source_id_for(n.get("source_file"), sources)
        anchor = nearest_anchor(blocks_by_source.get(sid, []), n.get("source_location"))
        cite = f"[{sid}·{anchor}]" if anchor else f"[{sid}]"
        glines.append(f"- **{n.get('label')}** {cite}")
    (out_dir / "glossary.md").write_text("\n".join(glines) + "\n", encoding="utf-8")

    # 3c. cheatsheet.md — só quando algum perfil pede referência rápida
    if any((s.profile in {"technical_book", "reference"}) for s in sources):
        (out_dir / "cheatsheet.md").write_text(
            "# Cheatsheet\n\n_(regras de decisão — a preencher a partir de content/)_\n",
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
        "`[Sn·loc]` -> fonte Sn no local `loc` (ver `sources.md` e `content/`).\n\n"
        + _usage_blocks()
    )
    (out_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # 5. sources.md — registro + índice cruzado tema↔fonte
    src_lines = ["# Fontes", ""]
    for s in sources:
        prof = f" · perfil: {s.profile}" if s.profile else ""
        src_lines.append(f"- **{s.id}** — {s.title} ({s.kind}){prof} — `{s.origin}`")
        temas = sorted(theme_by_sid.get(s.id, set()))
        if temas:
            src_lines.append(f"  - Temas: {', '.join(temas)}")
    (out_dir / "sources.md").write_text("\n".join(src_lines) + "\n", encoding="utf-8")

    return out_dir
