# anything-to-skill — spec de extração

Prompt/esquema que o orquestrador passa ao extrator (subagente ou inline) para
transformar um arquivo de conteúdo num fragmento de grafo de conhecimento.

## Instrução

Leia o(s) arquivo(s) de conteúdo indicado(s) e produza **apenas** JSON válido no
schema abaixo, sem explicação, sem cercas markdown, sem preâmbulo. Extraia
conceitos, entidades e relações nomeadas; não invente relações (na dúvida, marque
`AMBIGUOUS`).

## Schema

```json
{
  "nodes": [
    {
      "id": "snake_case_unico",
      "label": "Nome legível",
      "file_type": "concept | rationale",
      "source_file": "<nome do arquivo de conteúdo, ex.: S1.md>",
      "source_location": "<S1.md#L{linha} onde o conceito aparece>"
    }
  ],
  "edges": [
    {
      "source": "id_no_origem",
      "target": "id_no_destino",
      "relation": "depends-on | contradicts | defines | exemplifies | conceptually_related_to | references",
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
- `source_location`: `Sn.md#L{linha}` apontando onde o conceito é discutido; é o que
  ancora a proveniência de cada afirmação na skill gerada.
- `relation` tipada: use `depends-on` quando um conceito é pré-requisito de outro (a skill
  usa isso para sugerir ordem de estudo) e `contradicts` quando duas afirmações se opõem
  (a skill lista esses pares em `tensions.md`). `defines` e `exemplifies` para definição e
  exemplo. Só marque `contradicts` com oposição real entre as fontes. Um `rationale` que
  qualifica um `concept` (ressalva, condição, limite) usa `exemplifies` se ilustra o
  conceito num caso concreto, ou `conceptually_related_to` se só o nuança sem exemplificar.
- `confidence_score`: `1.0` para `EXTRACTED`; `0.55–0.95` para `INFERRED`; `0.1–0.3`
  para `AMBIGUOUS`.
- Densidade: extraia um nó por conceito ou justificativa distinta, não um nó por frase.
  Um trecho curto (poucos parágrafos) pode gerar só 2-4 nós — não fragmente para parecer
  mais completo; um corpus grande deve ter mais nós que um pequeno, mas a proporção não é
  fixa.
