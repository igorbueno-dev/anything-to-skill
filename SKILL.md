---
name: anything-to-skill
description: Transforma um corpus de fontes (livros, artigos, transcrições, links) numa skill de Claude Code de alta fidelidade e rastreável. Use quando o usuário quiser converter documentos em uma skill consultável.
---

# anything-to-skill

Constrói uma skill de Claude Code a partir de um corpus de fontes, organizada por
tema, com o texto-fonte completo consultável e cada afirmação rastreável até a fonte.

## Uso

```
/anything-to-skill <arquivo|pasta>
```

## Fluxo (v1 — esqueleto andante)

1. **Resolver inputs.** Por ora: arquivos markdown locais (PDF/URL/texto vêm nos planos 2+).
2. **Extração semântica.** Para cada arquivo de conteúdo, extrair um fragmento de grafo
   de conhecimento seguindo o schema próprio em `references/extraction_spec.md`
   (nós com `id`, `label`, `file_type`, `source_file`, `source_location`).
   Em Claude Code, despachar um subagente `general-purpose` por chunk com aquele prompt,
   OU — para um corpus pequeno — extrair inline você mesmo (o host é o LLM).
3. **Construir e emitir.** Chamar
   `anything_to_skill.build.build_skill(inputs, work_dir, out_dir, extractor=<coletor do passo 2>)`,
   onde `extractor(detect_result, content_dir) -> {"nodes": [...], "edges": [...]}`.
4. **Reportar** a pasta-skill gerada: `SKILL.md` (roteador), `sections/` (por tema),
   `content/` (fonte preservada), `.graph/` (mapa), `sources.md`.

## Estágios seguintes (planos 2–6)

Normalização multi-formato preservando imagem · portão de QA de extração ·
endereçamento por bloco · perfis adaptativos · guardrails de fidelidade e cite-check.
