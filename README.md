<div align="center">

# anything-to-skill

**Transforme livros, artigos, transcrições, links e texto colado em _uma única skill de Claude Code_, com alta fidelidade, organizada por tema e cada afirmação rastreável até a fonte.**

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Formatos](https://img.shields.io/badge/formatos-PDF%20%C2%B7%20MD%20%C2%B7%20TXT%20%C2%B7%20HTML-informational)
![Testes](https://img.shields.io/badge/testes-61%20passing-brightgreen)
![Licença](https://img.shields.io/badge/licen%C3%A7a-todos%20os%20direitos%20reservados-red)

</div>

---

## Quickstart

1. **Aponte** para um arquivo, uma pasta ou uma mistura de fontes.
2. A skill **normaliza, extrai e sintetiza**, com um portão de QA que sinaliza extração ruim em vez de mascarar.
3. O agente **carrega o tema sob demanda** enquanto você trabalha, citando o trecho exato da fonte.

```
/anything-to-skill <arquivo|pasta>
```

---

## Por que

Skills que convertem um documento numa referência costumam ter três fraquezas, e o anything-to-skill ataca as três:

- **Template engessado.** Forçar todo conteúdo no mesmo molde achata paper, transcrição e ensaio. → **Perfis adaptativos**: cada tipo de fonte gera um formato de seção diferente.
- **Perda de nuance.** Resumos descartam a ressalva do autor. → **Fidelidade primeiro**: o texto-fonte completo fica guardado e endereçável; o resumo é navegação, a palavra final é o trecho real, a um passo.
- **Extração frágil.** PDF de coluna/scan vira lixo silenciosamente. → **Portão de QA**: detecta corrupção e **sinaliza**, nunca resume sobre lixo.

Além disso é **multi-fonte** (vários documentos viram uma skill por tema) e **preserva imagens** dos PDFs.

## O que gera

Uma pasta-skill navegável, com carga em camadas (roteador mínimo → seções por tema → fonte completa):

| Arquivo/pasta | Papel |
|---|---|
| `SKILL.md` | roteador mínimo: índice de temas, gatilhos e legenda de citações (sempre carregado) |
| `sections/` | síntese por tema, no template do perfil (sob demanda) |
| `content/` | texto-fonte completo, **byte-idêntico**: a fonte-verdade |
| `sources.md` | registro de fontes + índice cruzado tema↔fonte + perfil |
| `glossary.md` | conceitos alfabetizados e ancorados |
| `cheatsheet.md` | regras de decisão (quando o perfil pede) |
| `figures/` | imagens preservadas + `figures.md` |
| `.graph/` | grafo consultável + índice de âncoras |
| `.qa/` | relatórios de extração e verificação (trilha de auditoria) |

## Recursos

| Recurso | O que faz |
|---|---|
| **Multi-fonte por tema** | Várias fontes viram uma skill por conceito; a síntese entre fontes emerge da detecção de comunidades |
| **Normalização multi-formato** | PDF, Markdown, texto e HTML → Markdown, **preservando imagens** embutidas do PDF |
| **Portão de QA** | Sinais determinísticos marcam fontes `clean / partial / failed`; fontes ruins não alimentam as seções |
| **Endereçamento por bloco** | Conteúdo fatiado em âncoras estáveis; a recuperação puxa o trecho certo, nunca o arquivo inteiro |
| **Perfis adaptativos** | `paper`, `article`, `technical_book`, `transcript`, `reference`, cada um com seu esquema |
| **Cite-check** | Verifica que cada citação verbatim existe literalmente na fonte; bloqueia alucinação |
| **Guardrails de nuance** | Sinaliza afirmação categórica sobre fonte que hesita |
| **Fencing anti-injeção** | Conteúdo de URL é cercado para instruções injetadas não sequestrarem o build |

## Como funciona

Motor **próprio** de grafo de conhecimento sobre [`networkx`](https://networkx.org/):

```
entrada (arquivos / URLs / texto)
   │
   ├─ [0] intake & registro de fontes ....... IDs estáveis + fencing de URL
   ├─ [1] normalização → Markdown ........... preserva imagens do PDF
   ├─ [2] classificação de perfil ........... paper / artigo / livro / transcrição / referência
   ├─ [3] extração com proveniência ......... nós com source_location (subagente/inline)
   ├─ [4] portão de QA ...................... detecta lixo; marca/exclui fontes failed
   ├─ [5] cluster & síntese ................. temas emergem entre fontes (networkx)
   ├─ [6] emissão ........................... roteador + seções + content + âncoras
   └─ [7] verificação ....................... traceabilidade + cite-check + nuance + segurança
   │
   ▼
skill gerada
```

O `SKILL.md` **roteia**, nunca despeja conteúdo: o custo de entrada é mínimo e a profundidade fica sob demanda.

## Uso

Como skill de Claude Code:

```
/anything-to-skill <arquivo|pasta>
```

O fluxo resolve as entradas, extrai o grafo de conhecimento (via subagente ou inline), constrói e emite a pasta-skill, e reporta os artefatos gerados.

Programaticamente:

```python
from pathlib import Path
from anything_to_skill.build import build_skill

def extractor(detect_result, content_dir):
    # devolve {"nodes": [...], "edges": [...]}, ver references/extraction_spec.md
    ...

build_skill([Path("meu_livro.pdf")], Path("work"), Path("minha-skill"),
            extractor=extractor)
```

## Instalação

### Como plugin (recomendado)

Registre o marketplace no Claude Code:

```
/plugin marketplace add igorbueno-dev/anything-to-skill
```

E instale o plugin:

```
/plugin install anything-to-skill@igor-skills
```

Na primeira execução, a skill prepara sozinha um ambiente Python em
`~/.anything-to-skill` com as dependências. Depois disso, `/anything-to-skill` fica
disponível.

### A partir do código (para desenvolver)

```bash
git clone https://github.com/igorbueno-dev/anything-to-skill.git
```

```bash
cd anything-to-skill && python -m venv .venv && .venv/Scripts/activate && pip install -e ".[dev]"
```

No macOS/Linux, ative com `source .venv/bin/activate`.

<details>
<summary><b>Requisitos</b></summary>

- **Python 3.11+**
- [`networkx`](https://pypi.org/project/networkx/): grafo e detecção de comunidades (Louvain)
- [`pymupdf`](https://pypi.org/project/pymupdf/): extração de PDF preservando imagens
- [`markdownify`](https://pypi.org/project/markdownify/): conversão de HTML

</details>

<details>
<summary><b>Estrutura do repositório</b></summary>

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
skills/            a skill empacotada para o plugin
SKILL.md           orquestrador da skill
tests/             suíte pytest
```

</details>

## FAQ

**Meus dados vão pra algum lugar?**
Não. Todo o processamento é local; a skill gerada fica na sua máquina.

**E se a extração do PDF sair ruim?**
O portão de QA detecta (coluna quebrada, encoding, imagens perdidas) e sinaliza no `.qa/`; a fonte é marcada e não alimenta as seções, sem resumo sobre lixo.

**Posso ir adicionando fontes ao longo do tempo?**
Sim, o `.graph/` é persistente e o design prevê re-emissão incremental (roadmap v2).

## Desenvolvimento

```bash
.venv/Scripts/python.exe -m pytest -v
```

A arquitetura separa lógica determinística (100% coberta por testes) do que precisa de LLM/visão (injetado por dependência): intake, normalização, QA, fatiamento, perfis e verificação são testáveis; extração semântica e descrição de imagem entram por injeção.

## Roadmap

**v1 (atual):** intake multi-formato · normalização preserva-imagem · portão de QA · endereçamento por bloco · perfis adaptativos · emissor completo · cite-check e guardrails.

**v2 (planejado):** intake via APIs acadêmicas (Semantic Scholar, arXiv, OpenAlex, PubMed) · OCR para PDF escaneado · re-emissão incremental · áudio/vídeo via transcrição · artefato explícito de divergência entre fontes.

## Direitos autorais

Copyright © 2026 Igor Bueno. Todos os direitos reservados.

Este é um projeto proprietário. O código-fonte e a documentação são de autoria e propriedade exclusivas de Igor Bueno. A disponibilização pública deste repositório não concede qualquer licença de uso, cópia, modificação ou redistribuição.

Sem autorização prévia e por escrito do autor, é vedado:

- copiar, reproduzir ou distribuir o código, no todo ou em parte;
- modificar, adaptar ou criar trabalhos derivados;
- usar o software para fins comerciais ou incorporá-lo a outros produtos.

Para pedidos de licenciamento ou permissões, entre em contato: ig.dsbueno@gmail.com.
