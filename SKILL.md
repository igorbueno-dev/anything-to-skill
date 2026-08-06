---
name: anything-to-skill
description: Transforma um corpus de fontes (livros, artigos, transcrições, links) numa skill de Claude Code de alta fidelidade e rastreável. Use quando o usuário quiser converter documentos em uma skill consultável.
---

# anything-to-skill

Constrói uma skill de Claude Code a partir de um corpus de fontes, organizada por
tema, com o texto-fonte completo consultável e cada afirmação rastreável até a fonte.

## Entradas aceitas

Arquivos locais **PDF** (texto + imagens preservadas), **Markdown**, **txt** e **HTML**.
**URLs** (http/https): passe a URL direto; o conteúdo é buscado e limpo de boilerplate
(use `build_skill(..., fetch_fn=...)` para injetar o fetch em ambiente controlado).
Texto colado: salve num arquivo `.md` ou `.txt` e passe o caminho.

## Ambiente

Os passos 1 e 3 rodam em Python. Use um ambiente com o pacote e suas dependências
instalados (veja o README para preparar o venv) e rode o Python desse ambiente.

## Fluxo de construção

Três passos. A extração semântica (passo 2) é feita por você, o agente; os passos 1 e 3
são deterministas e rodam em Python.

### 1. Normalizar e ler as fontes

Rode este script (ajuste `WORK` e `inputs`). Ele registra as fontes como `S1..Sn`,
normaliza cada uma para `content/{Sn}.md` e extrai imagens para `figures/`.

```python
from pathlib import Path
from anything_to_skill.intake import register_sources
from anything_to_skill.normalize import normalize

WORK = Path(r"<work_dir>")          # pasta de trabalho temporária
inputs = [Path(r"<arquivo1>"), ]    # os arquivos do corpus
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
`references/extraction_spec.md`. Cada nó carrega `id`, `label`, `file_type`
(`concept`, `rationale`, `claim`, `example`, ...), `source_file` (`"{Sn}.md"`) e
`source_location` (`"{Sn}.md#L<linha>"`, apontando para a linha real no `content/`).
As arestas ligam `source`/`target` por `relation`.

Num corpus grande, despache um subagente `general-purpose` por trecho com esse mesmo
prompt; num corpus pequeno, extraia inline você mesmo.

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
OUT  = Path(r"<out_dir>")            # pasta da skill gerada
inputs = [Path(r"<arquivo1>"), ]     # os mesmos do passo 1, na mesma ordem
ext = json.loads((WORK / "extraction.json").read_text(encoding="utf-8"))

build_skill(inputs, WORK, OUT, extractor=lambda detect_result, content_dir: ext)
print("skill gerada em", OUT)
```

`build_skill` renormaliza de forma determinista (mesma ordem `S1..Sn`, mesmas linhas),
detecta comunidades, nomeia cada tema pelo conceito central, resolve as âncoras de
citação, roda o QA e a verificação final, e escreve a pasta-skill.

## Saída

- `SKILL.md` roteador (com frontmatter `name`/`description`, roteia por tema)
- `sections/<tema>.md` uma por tema, no template do perfil dominante
- `content/{Sn}.md` fonte preservada byte-a-byte
- `glossary.md`, `sources.md` (índice cruzado tema-fonte), `cheatsheet.md` quando cabe
- `figures/` imagens extraídas (com `figures.md`)
- `.graph/` grafo + índice de âncoras; `.qa/` relatórios de extração e verificação

A pasta gerada é uma skill instalável por si só: mova-a para `~/.claude/skills/` e ela
dispara pelos temas do corpus, sem precisar de Python para ser consultada.
