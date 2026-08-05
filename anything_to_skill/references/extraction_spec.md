# anything-to-skill — spec de extração

Prompt/esquema que o orquestrador passa ao extrator (subagente ou inline) para
transformar um arquivo de conteúdo num fragmento de grafo de conhecimento.

## Instrução

Leia o(s) arquivo(s) de conteúdo indicado(s) e produza **apenas** JSON válido no
schema abaixo — sem explicação, sem cercas markdown, sem preâmbulo. Extraia
conceitos, entidades e relações nomeadas; não invente relações (na dúvida, marque
`AMBIGUOUS`).

## Schema

```json
{
  "nodes": [
    {
      "id": "snake_case_unico",
      "label": "Nome legível",
      "file_type": "concept | rationale | document | paper | image",
      "source_file": "<nome do arquivo de conteúdo, ex.: S1.md>",
      "source_location": "<S1.md#L{linha} onde o conceito aparece>"
    }
  ],
  "edges": [
    {
      "source": "id_no_origem",
      "target": "id_no_destino",
      "relation": "conceptually_related_to | references | supports | contrasts_with",
      "confidence": "EXTRACTED | INFERRED | AMBIGUOUS",
      "confidence_score": 1.0
    }
  ]
}
```

## Regras

- `id`: minúsculas, apenas `[a-z0-9_]`, determinístico a partir do label (o mesmo
  conceito deve gerar sempre o mesmo id). Nunca acrescente sufixos de chunk.
- `file_type`: use `concept` para ideias/princípios/mecanismos e `rationale` para
  justificativas de decisão; esses dois entram no glossário da skill.
- `source_file`: exatamente o nome do arquivo lido (ex.: `S1.md`).
- `source_location`: `Sn.md#L{linha}` apontando onde o conceito é discutido — é o que
  ancora a proveniência de cada afirmação na skill gerada.
- `confidence_score`: `1.0` para `EXTRACTED`; `0.55–0.95` para `INFERRED`; `0.1–0.3`
  para `AMBIGUOUS`.
