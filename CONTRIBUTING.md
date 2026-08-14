# Contribuindo

## Rodando os testes

```bash
.venv/Scripts/python.exe -m pytest -v
```

A arquitetura separa lógica determinística (coberta por testes) do que precisa de
LLM/visão/rede (injetado por dependência): intake, normalização, QA, fatiamento,
segmentação, dedup, perfis e verificação são testáveis; extração, síntese, autoavaliação,
similaridade e fetch entram por injeção.

## Estrutura do repositório

```
anything_to_skill/
  intake.py        registro de fontes (arquivos e URLs)
  normalize.py     PDF/HTML/MD/TXT/URL para Markdown (preserva imagem)
  structure.py     segmentação por títulos (densidade e temas)
  fencing.py       cerca conteúdo não-confiável (URLs)
  interview.py     entrevista de intake calibrada
  qa.py            portão de QA de extração
  kg.py            motor de grafo (detect/build/cluster/afinidade/export)
  dedup.py         desduplicação de conceitos + peso de evidência
  chunk.py         fatiamento em blocos endereçáveis
  resolve.py       resolução de citações [Sn·bloco]
  profiles.py      classificador de perfil de conteúdo
  templates.py     esquemas de seção por perfil
  emit.py          emissor da pasta-skill
  build.py         orquestrador do pipeline
  eval.py          autoavaliação da skill gerada
  verify.py        traceabilidade + cite-check + nuance + segurança
  references/      schema de extração próprio
.claude-plugin/    manifesto do plugin e catálogo do marketplace
skills/anything-to-skill/SKILL.md   a skill (orquestrador, carregado pelo plugin)
tests/             suíte pytest
```
