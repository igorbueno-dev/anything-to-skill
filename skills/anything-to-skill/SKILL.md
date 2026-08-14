---
name: anything-to-skill
description: Use quando o usuário quiser converter um corpus de fontes (livros, artigos, transcrições, links) numa skill de Claude Code consultável e rastreável até a fonte.
---

# anything-to-skill

Constrói uma skill de Claude Code a partir de um corpus de fontes, organizada por
tema, com o texto-fonte completo consultável e cada afirmação rastreável até a fonte.

## Entradas aceitas

Arquivos locais **PDF** (texto + imagens preservadas), **Markdown**, **txt** e **HTML**.
**URLs** (http/https): passe a URL direto; o conteúdo é buscado e limpo de boilerplate.
Texto colado: salve num arquivo `.md` ou `.txt` e passe o caminho.

Em ambiente controlado (sem rede, ou com fetch já mediado por outra ferramenta), injete
`fetch_fn` (uma função `url -> html`) em `normalize()` (passo 1) ou `build_skill()`
(passo 3) em vez de deixar o fetch padrão rodar.

## Ambiente (bootstrap, roda uma vez)

Este plugin traz um pacote Python. Na primeira execução, prepare um venv estável (fora do
cache do plugin, que é recriado a cada update). É idempotente: se já existir, `uv` reaproveita.

```bash
uv venv "$HOME/.anything-to-skill/.venv" --python 3.12
uv pip install --python "$HOME/.anything-to-skill/.venv" "$CLAUDE_PLUGIN_ROOT"
```

Instalar `$CLAUDE_PLUGIN_ROOT` (que tem o `pyproject.toml`) puxa as dependências
(`networkx`, `pymupdf`, `markdownify`) automaticamente.

Depois, rode o Python sempre por esse venv:
- Windows: `"$HOME/.anything-to-skill/.venv/Scripts/python.exe"`
- Linux/macOS: `"$HOME/.anything-to-skill/.venv/bin/python"`

O schema de extração está em `$CLAUDE_PLUGIN_ROOT/anything_to_skill/references/extraction_spec.md`.

## Fluxo de construção

Três passos. A extração semântica (passo 2) é feita por você, o agente; os passos 1 e 3
são deterministas e rodam em Python.

### 1. Normalizar e ler as fontes

```python
from pathlib import Path
from anything_to_skill.intake import register_sources
from anything_to_skill.normalize import normalize

WORK = Path(r"<work_dir>")
inputs = [Path(r"<arquivo1>"), ]
content = WORK / "content"; content.mkdir(parents=True, exist_ok=True)
figures = WORK / "figures"; figures.mkdir(parents=True, exist_ok=True)

sources = register_sources(inputs, WORK)
for src, inp in zip(sources, inputs):
    doc = normalize(Path(inp), kind=src.kind, out_images_dir=figures, source_id=src.id)
    (content / f"{src.id}.md").write_text(doc.markdown, encoding="utf-8")
    print(src.id, "->", src.title, f"({src.kind})")
```

Depois leia cada `WORK/content/{Sn}.md`. Os números de linha desses arquivos são a
referência estável para ancorar as citações no passo 2.

### 2. Extrair o grafo de conhecimento (você, o agente)

Para cada fonte, produza nós e arestas seguindo **exatamente** o schema em
`$CLAUDE_PLUGIN_ROOT/anything_to_skill/references/extraction_spec.md`. Cada nó carrega
`id`, `label`, `file_type` (`concept` ou `rationale`; só esses dois entram no glossário),
`source_file` (`"{Sn}.md"`) e `source_location` (`"{Sn}.md#L<linha>"`). Cada aresta carrega
`source`/`target`, `relation` tipada (`depends-on`, `contradicts`, `defines`,
`exemplifies`, `conceptually_related_to`, `references`) e `confidence`/`confidence_score`.

Corpus grande (muitas fontes ou fontes longas): despache um subagente `general-purpose`
por fonte com o mesmo schema, cada um devolvendo seu bloco de nós/arestas; combine tudo
num único `extraction.json` antes do passo 3. Corpus pequeno: extraia inline você mesmo.

Grave o resultado em `WORK/extraction.json`:

```json
{
  "nodes": [
    {"id": "n1", "label": "Conceito", "file_type": "concept",
     "source_file": "S1.md", "source_location": "S1.md#L3"}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "relation": "depends-on",
     "confidence": "EXTRACTED", "confidence_score": 1.0}
  ]
}
```

### 3. Construir e emitir a skill

```python
import json
from pathlib import Path
from anything_to_skill.build import build_skill

WORK = Path(r"<work_dir>")
OUT  = Path(r"<out_dir>")  # o nome desta pasta vira o `name:` da skill gerada — escolha com cuidado
inputs = [Path(r"<arquivo1>"), ]
ext = json.loads((WORK / "extraction.json").read_text(encoding="utf-8"))

build_skill(inputs, WORK, OUT, extractor=lambda detect_result, content_dir: ext)
print("skill gerada em", OUT)
```

`build_skill` renormaliza de forma determinista, detecta comunidades, nomeia cada tema pelo
conceito central, resolve as âncoras de citação, roda o QA e a verificação final, escreve a
pasta-skill e um `build_report.md` com números autoritativos.

Por padrão as seções trazem só os rótulos dos nós, um por linha, com a citação de âncora
(sem prosa sintetizada) — é a fidelidade byte-a-byte fazendo seu trabalho, não um bug. Para
prosa de verdade, dedup semântico ou autoavaliação (perguntas geradas do corpus e
respondidas com citação), `build_skill` aceita os ganchos opcionais `summarize_fn`,
`similar_fn`, `qa_gen_fn`/`answer_fn` (veja as assinaturas em `anything_to_skill/build.py`).

## Saída

- `SKILL.md` roteador (frontmatter `name`/`description`; contrato de citar-ou-recusar,
  protocolo de recuperação e exemplos de pergunta)
- `study_modes.md` protocolo dos modos de estudo (mapa, currículo, debate, flashcards,
  cobertura cruzada, insights, notas), referenciado pelo roteador
- `sections/<tema>.md` uma por tema; `content/{Sn}.md` fonte preservada byte-a-byte
- `glossary.md`, `sources.md`, `tensions.md` (pares `contradicts`), `coverage.md`,
  `build_report.md`; `cheatsheet.md` só para perfil `technical_book`/`reference`
- `.graph/` grafo + âncoras; `.qa/` relatórios
- `figures/` só existe se alguma fonte tinha imagem (não é criada vazia)

A pasta gerada é uma skill instalável por si só: mova-a para `~/.claude/skills/` e ela
dispara pelos temas do corpus, sem precisar de Python para ser consultada.
