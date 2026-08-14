<div align="center">

# anything-to-skill

**Transforme livros, artigos, transcrições, links e texto colado em _uma única skill de Claude Code_: organizada por tema, com cada afirmação rastreável até a fonte.**

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Formatos](https://img.shields.io/badge/formatos-PDF%20%C2%B7%20MD%20%C2%B7%20TXT%20%C2%B7%20HTML%20%C2%B7%20URL-informational)
![Testes](https://img.shields.io/badge/testes-103%20passing-brightgreen)
![Licença](https://img.shields.io/badge/licen%C3%A7a-todos%20os%20direitos%20reservados-red)

</div>

---

## O que é

Você tem um corpus (um livro, um curso em transcrições, vários artigos, links) e quer
consultá-lo e aprender com ele sem reler tudo. O **anything-to-skill** transforma esse
corpus em **uma skill de Claude Code**: organizada por tema, com o texto-fonte completo
guardado e **cada afirmação rastreável até o trecho exato da fonte**.

Depois de instalada, você conversa com o seu material: _"me ensina esse assunto"_,
_"revisa tal ponto"_, e o Claude responde a partir do acervo, citando a origem.

## Instalação

Registre o marketplace no Claude Code:

```
/plugin marketplace add igorbueno-dev/anything-to-skill
```

E instale o plugin:

```
/plugin install anything-to-skill@igor-skills
```

Na primeira execução, a skill prepara sozinha um ambiente Python em `~/.anything-to-skill`
com as dependências. Depois disso, `/anything-to-skill` fica disponível.

<details>
<summary><b>A partir do código (para desenvolver)</b></summary>

```bash
git clone https://github.com/igorbueno-dev/anything-to-skill.git
```

```bash
cd anything-to-skill && python -m venv .venv && .venv/Scripts/activate && pip install -e ".[dev]"
```

No macOS/Linux, ative com `source .venv/bin/activate`.

</details>

## Uso

Aponte para um arquivo, uma pasta, uma URL ou uma mistura de fontes:

```
/anything-to-skill <arquivo|pasta|url>
```

O fluxo normaliza as fontes, extrai o grafo de conhecimento, constrói a pasta-skill e
reporta os artefatos. A skill gerada é instalável por si só e, uma vez ativa, responde
suas perguntas citando a fonte e recusando o que não estiver no acervo.

<details>
<summary><b>Uso programático</b></summary>

```python
from pathlib import Path
from anything_to_skill.build import build_skill

def extractor(detect_result, content_dir):
    # devolve {"nodes": [...], "edges": [...]}, ver references/extraction_spec.md
    ...

build_skill([Path("meu_livro.pdf")], Path("work"), Path("minha-skill"),
            extractor=extractor)
```

Partes que precisam de LLM, visão ou rede entram por injeção (`extractor`,
`summarize_fn`, `qa_gen_fn`, `answer_fn`, `similar_fn`, `fetch_fn`); detalhes da
arquitetura em [CONTRIBUTING.md](CONTRIBUTING.md).

</details>

## O que gera

Uma pasta-skill navegável, com carga em camadas (roteador mínimo → seções por tema →
fonte completa):

| Arquivo/pasta | Papel |
|---|---|
| `SKILL.md` | roteador: índice de temas, contrato de citar-ou-recusar e como recuperar (sempre carregado) |
| `COMO_USAR.md` | guia humano de instalação e uso da skill, mostrado no chat logo após o build |
| `study_modes.md` | protocolo dos modos de estudo (mapa, currículo, debate, flashcards, cobertura cruzada, insights, notas, quiz, modo socrático, desafia minha ideia, comparação entre perfis, leitura incremental, revisão espaçada, percentual coberto; marco é automático, não um modo que o usuário aciona) |
| `sections/` | síntese por tema, no template do perfil, com resumo citado no topo |
| `content/` | texto-fonte completo, **byte-idêntico**: a fonte-verdade |
| `sources.md` | registro de fontes + índice cruzado tema↔fonte |
| `glossary.md` | conceitos ancorados, com peso de evidência (quantas fontes apoiam) |
| `tensions.md` | contradições entre fontes, cada lado citado |
| `coverage.md` | densidade e lacunas por segmento (o que o corpus não cobre) |
| `build_report.md` | números autoritativos do build (páginas, conceitos, temas) |
| `figures/` | imagens preservadas dos PDFs |
| `.graph/` · `.qa/` | grafo consultável + âncoras; relatórios de QA, verificação e autoavaliação |
| `.study/` | progresso de estudo do usuário (`progress.json`); diferente de `.graph/` e `.qa/`, NÃO é regenerada no rebuild, sobrevive a atualizações do corpus |

## Pontos centrais

| Princípio | O que significa |
|---|---|
| **Fidelidade primeiro** | O texto-fonte fica guardado byte-a-byte e endereçável; o resumo é navegação, a palavra final é o trecho real, a um passo |
| **Rastreável, citar-ou-recusar** | Cada afirmação carrega `[Sn·âncora]`; fora do acervo, a skill diz que não está nas fontes em vez de inventar |
| **Portão de QA** | Sinais determinísticos marcam fontes `clean / partial / failed`; fonte ruim é sinalizada, nunca resumida sobre lixo |
| **Temas por estrutura** | Os temas emergem entre fontes (detecção de comunidades) e respeitam a estrutura do documento, sem colapsar capítulos |
| **Multi-fonte** | Vários documentos viram uma skill por conceito; conceitos repetidos são consolidados e as contradições ficam explícitas |
| **Perfis adaptativos** | `paper`, `article`, `technical_book`, `transcript`, `reference`, cada um com seu esquema de seção |
| **Autoavaliação** | Gera perguntas do próprio corpus e mede se a skill responde certo, com a citação certa |

## Como funciona

Motor **próprio** de grafo de conhecimento sobre [`networkx`](https://networkx.org/):

```
entrada (arquivos / URLs / texto)
   │
   ├─ [0] intake & registro ................. IDs estáveis + fencing de URL
   ├─ [1] normalização → Markdown ........... preserva imagens do PDF
   ├─ [2] classificação de perfil ........... paper / artigo / livro / transcrição / referência
   ├─ [3] extração com proveniência ......... nós com source_location (subagente/inline)
   ├─ [4] portão de QA ...................... detecta lixo; marca/exclui fontes failed
   ├─ [5] dedup + grafo + afinidade ......... consolida conceitos; temas respeitam a estrutura
   ├─ [6] emissão ........................... roteador + seções + content + tensions + coverage
   └─ [7] verificação + autoavaliação ....... traceabilidade, cite-check, nuance, segurança, score
   │
   ▼
skill gerada
```

O `SKILL.md` **roteia**, nunca despeja conteúdo: o custo de entrada é mínimo e a
profundidade fica sob demanda.

<details>
<summary><b>Requisitos</b></summary>

- **Python 3.11+**
- [`networkx`](https://pypi.org/project/networkx/): grafo e detecção de comunidades (Louvain)
- [`pymupdf`](https://pypi.org/project/pymupdf/): extração de PDF preservando imagens
- [`markdownify`](https://pypi.org/project/markdownify/): conversão de HTML

</details>

## FAQ

**Meus dados vão pra algum lugar?**
Não. Todo o processamento é local; a skill gerada fica na sua máquina.

**E se a extração do PDF sair ruim?**
O portão de QA detecta (coluna quebrada, encoding, imagens perdidas) e sinaliza no `.qa/`;
a fonte é marcada e não alimenta as seções, sem resumo sobre lixo.

**Serve pra estudar um curso longo?**
Sim. Transcrições viram um mapa por tema com índice de onde cada assunto aparece; você
pergunta e aprende sem reassistir tudo. Cursos de código funcionam melhor se as
transcrições já trouxerem o código escrito, não só a fala.

## Contribuindo

Testes, arquitetura determinístico/injeção e estrutura do repositório em
[CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

**Entregue:** intake multi-formato (arquivos + URLs) · normalização preserva-imagem ·
portão de QA · endereçamento por bloco · perfis adaptativos · temas por estrutura ·
cite-check e contrato de citar-ou-recusar · tensions e peso de evidência · relatórios de
cobertura, build e autoavaliação.

**Futuro:** re-emissão incremental · modo entrevista de intake · intake via APIs
acadêmicas (Semantic Scholar, arXiv, OpenAlex, PubMed).

## Direitos autorais

Copyright © 2026 Igor Bueno. Todos os direitos reservados.

Este é um projeto proprietário. O código-fonte e a documentação são de autoria e
propriedade exclusivas de Igor Bueno. A disponibilização pública deste repositório não
concede qualquer licença de uso, cópia, modificação ou redistribuição.

Sem autorização prévia e por escrito do autor, é vedado:

- copiar, reproduzir ou distribuir o código, no todo ou em parte;
- modificar, adaptar ou criar trabalhos derivados;
- usar o software para fins comerciais ou incorporá-lo a outros produtos.

Para pedidos de licenciamento ou permissões, entre em contato: ig.dsbueno@gmail.com.
