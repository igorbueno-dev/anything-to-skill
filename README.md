# anything-to-skill

> Transforma um corpus heterogêneo — livros, artigos, múltiplos artigos, transcrições, links e texto colado — em **uma única skill de Claude Code**: de alta fidelidade, organizada por tema, com o texto-fonte completo consultável e **cada afirmação rastreável até a fonte**.

Skills que convertem um documento numa referência consultável costumam ter três fraquezas: forçam todo conteúdo no mesmo molde, achatam a nuance do autor em resumos, e degradam silenciosamente quando a extração do PDF falha. O **anything-to-skill** ataca as três — e vai além, sendo **multi-fonte** e **preservando imagens**.

---

## Por que existe

- **Fidelidade acima de resumo.** O texto-fonte completo é convertido, fatiado em blocos endereçáveis e guardado na skill. O resumo vira camada de navegação; a palavra final é sempre o trecho real do autor, a um passo de distância.
- **Proveniência de primeira classe.** Toda afirmação carrega uma âncora `[Sn·bloco]` que resolve para o trecho exato do `content/`. Nada é afirmado sem origem verificável.
- **Honestidade sobre falha.** Um portão de QA detecta extração corrompida (coluna quebrada, scan ruim, imagens perdidas) e **sinaliza** em vez de mascarar com um resumo bonito.
- **Estrutura que serve ao conteúdo.** Um paper, uma transcrição, um artigo de opinião e um livro técnico geram formatos de seção diferentes.

## Recursos

| Recurso | O que faz |
|---|---|
| **Multi-fonte por tema** | Várias fontes viram uma skill organizada por conceito; a síntese entre fontes emerge da detecção de comunidades |
| **Normalização multi-formato** | PDF, Markdown, texto e HTML → Markdown, **preservando as imagens** embutidas do PDF |
| **Portão de QA de extração** | Sinais determinísticos (palavra-quebrada, encoding, layout, rendimento, fidelidade de imagem) marcam fontes `clean / partial / failed` |
| **Endereçamento por bloco** | Conteúdo fatiado em âncoras estáveis; a recuperação puxa o trecho certo, nunca o arquivo inteiro |
| **Perfis adaptativos** | `paper`, `article`, `technical_book`, `transcript`, `reference` — cada um com seu esquema de seção |
| **Cite-check** | Verifica que cada citação verbatim existe literalmente na fonte; bloqueia alucinação |
| **Guardrails de nuance** | Sinaliza afirmação categórica sobre fonte que hesita |
| **Fencing anti-injeção** | Conteúdo buscado de URL é cercado para instruções injetadas não sequestrarem o build |

## Como funciona

O anything-to-skill usa o motor de grafo de conhecimento da [graphify](https://github.com/safishamsi/graphify) para extração com proveniência e detecção de comunidades, e adiciona camadas próprias de qualidade e um emissor de skill:

```
entrada (arquivos / URLs / texto)
   │
   ├─ [0] intake & registro de fontes ....... IDs estáveis + fencing de URL
   ├─ [1] normalização → Markdown ........... preserva imagens do PDF
   ├─ [2] classificação de perfil ........... paper / artigo / livro / transcrição / referência
   ├─ [3] extração com proveniência ......... nós com source_location (graphify)
   ├─ [4] portão de QA ...................... detecta lixo; marca/​exclui fontes failed
   ├─ [5] cluster & síntese ................. temas emergem entre fontes (graphify)
   ├─ [6] emissão ........................... roteador + seções + content + âncoras
   └─ [7] verificação ....................... traceabilidade + cite-check + nuance + segurança
   │
   ▼
skill gerada
```

## Estrutura da skill gerada

```
<skill>/
  SKILL.md            roteador mínimo (índice de temas + gatilhos + legenda de citações)
  sections/           síntese por tema, no template do perfil (carregada sob demanda)
  content/            texto-fonte completo, byte-idêntico (a fonte-verdade)
  sources.md          registro de fontes + índice cruzado tema↔fonte + perfil
  glossary.md         conceitos alfabetizados, ancorados
  cheatsheet.md       regras de decisão (quando o perfil pede)
  figures/            imagens preservadas + figures.md
  .graph/             grafo consultável (graph.json) + índice de âncoras (anchors.json)
  .qa/                relatórios de extração e verificação (trilha de auditoria)
```

O `SKILL.md` **roteia**, nunca despeja conteúdo: o custo de entrada é mínimo e a profundidade fica sob demanda.

## Requisitos

- Python **3.11+**
- [`graphifyy`](https://pypi.org/project/graphifyy/) (motor de extração e grafo)
- `pymupdf` e `markdownify` (normalização)

## Instalação

```bash
git clone https://github.com/igorbueno-dev/anything-to-skill.git
cd anything-to-skill
python -m venv .venv
.venv/Scripts/activate          # Windows
pip install -e .
```

## Uso

Como skill de Claude Code:

```
/anything-to-skill <arquivo|pasta>
```

O fluxo resolve as entradas, extrai o grafo de conhecimento (via subagente ou inline), constrói e emite a pasta-skill, e reporta os artefatos gerados. Veja `SKILL.md` para o detalhe do orquestrador.

Programaticamente:

```python
from pathlib import Path
from anything_to_skill.build import build_skill

def extractor(detect_result, content_dir):
    # devolve {"nodes": [...], "edges": [...]} no schema graphify
    ...

build_skill([Path("meu_livro.pdf")], Path("work"), Path("minha-skill"),
            extractor=extractor)
```

## Desenvolvimento

```bash
.venv/Scripts/python.exe -m pytest -v
```

A arquitetura mantém a fronteira entre lógica determinística (coberta por testes) e o que precisa de LLM/visão (injetado por dependência): intake, normalização, QA, fatiamento, perfis e verificação são 100% testáveis; extração semântica e descrição de imagem entram por injeção.

## Roadmap

**v1 (atual):** intake multi-formato · normalização preserva-imagem · portão de QA · endereçamento por bloco · perfis adaptativos · emissor completo · cite-check e guardrails.

**v2 (planejado):** intake via APIs acadêmicas (Semantic Scholar, arXiv, OpenAlex, PubMed) · OCR para PDF escaneado · re-emissão incremental · áudio/vídeo via transcrição · artefato explícito de divergência entre fontes.

## Autoria

Autor único: **Igor Bueno** (ig.dsbueno@gmail.com). Todos os direitos reservados.
