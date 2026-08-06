---
name: anything-to-skill
description: Transforma um corpus de fontes (livros, artigos, transcrições, links) numa skill de Claude Code de alta fidelidade e rastreável. Use quando o usuário quiser converter documentos em uma skill consultável.
---

# anything-to-skill

Constrói uma skill de Claude Code a partir de um corpus de fontes, organizada por
tema, com o texto-fonte completo consultável e cada afirmação rastreável até a fonte.

## Entradas aceitas

Arquivos locais **PDF** (texto + imagens preservadas), **Markdown**, **txt** e **HTML**.
Texto colado: salve num arquivo `.md` ou `.txt` e passe o caminho.

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

Para cada fonte, produza nós e arestas seguindo o schema em
`$CLAUDE_PLUGIN_ROOT/anything_to_skill/references/extraction_spec.md`. Cada nó carrega
`id`, `label`, `file_type` (`concept`, `rationale`, `claim`, `example`, ...),
`source_file` (`"{Sn}.md"`) e `source_location` (`"{Sn}.md#L<linha>"`). As arestas ligam
`source`/`target` por `relation`.

Grave o resultado em `WORK/extraction.json`:

```json
{
  "nodes": [
    {"id": "n1", "label": "Conceito", "file_type": "concept",
     "source_file": "S1.md", "source_location": "S1.md#L3"}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "relation": "relaciona"}
  ]
}
```

### 3. Construir e emitir a skill

```python
import json
from pathlib import Path
from anything_to_skill.build import build_skill

WORK = Path(r"<work_dir>")
OUT  = Path(r"<out_dir>")
inputs = [Path(r"<arquivo1>"), ]
ext = json.loads((WORK / "extraction.json").read_text(encoding="utf-8"))

build_skill(inputs, WORK, OUT, extractor=lambda detect_result, content_dir: ext)
print("skill gerada em", OUT)
```

`build_skill` renormaliza de forma determinista, detecta comunidades, nomeia cada tema pelo
conceito central, resolve as âncoras de citação, roda o QA e a verificação final, escreve a
pasta-skill e um `build_report.md` com números autoritativos.

## Saída

- `SKILL.md` roteador (frontmatter `name`/`description`; contrato de citar-ou-recusar,
  protocolo de recuperação e exemplos de pergunta)
- `sections/<tema>.md` uma por tema; `content/{Sn}.md` fonte preservada byte-a-byte
- `glossary.md`, `sources.md`, `build_report.md`
- `figures/` imagens extraídas; `.graph/` grafo + âncoras; `.qa/` relatórios

A pasta gerada é uma skill instalável por si só: mova-a para `~/.claude/skills/` e ela
dispara pelos temas do corpus, sem precisar de Python para ser consultada.
