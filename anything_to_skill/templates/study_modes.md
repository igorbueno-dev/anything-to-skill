# Modos de estudo

Protocolos pra usar quando o usuário pedir algo além de "recupera e responde". Cada modo
usa dados que já existem nesta skill; nenhum exige gerar arquivo novo. Se o dado
necessário não existir ou for insuficiente pro corpus, diga isso ao usuário em vez de
improvisar, a mesma lógica de "não está nas fontes" que rege o resto desta skill.

## Mapa de dependência
Gatilho: "mapa", "diagrama", "como os conceitos se conectam", "visão geral".
Leia `.graph/graph.json`, filtre as arestas com `relation` igual a `depends-on`, monte um
bloco de diagrama Mermaid (` ```mermaid graph TD `) usando o `label` dos nós, nunca o `id`
cru. Acima de uns 20 nós no recorte pedido o diagrama fica ilegível: sugira focar num tema
por vez em vez de despejar o grafo inteiro.

## Currículo
Gatilho: "em que ordem estudo", "por onde começo", "monta um plano".
Mesma fonte do mapa (arestas `depends-on`), em ordenação topológica. Ciclo é possível (a
extração é heurística, não garante grafo acíclico): se achar um, avise explicitamente em
vez de forçar uma ordem falsa, e desempate pelo nó de maior `evidence_weight`.

## Debate
Gatilho: "debate", "desafia minha ideia", "onde as fontes divergem".
Leia `tensions.md`. Apresente um lado sem revelar o outro, pergunte a opinião do usuário,
só depois mostre o lado contrário citando a fonte. Se `tensions.md` não tiver contradição
registrada, diga isso; não invente uma tensão pra manter o modo funcionando.

## Flashcards
Gatilho: "flashcards", "me testa rapidinho", "quero revisar".
Leia `glossary.md`. Pra cada entrada, gere "O que é `<label>`?" e segure a resposta
(citação + explicação curta) até o usuário tentar responder.

## Cobertura cruzada
Gatilho: "o que a fonte A cobre que a B não", "compara as fontes".
Leia `coverage.md` e o índice tema-fonte de `sources.md`. Corpus de fonte única não tem
comparação possível: diga isso em vez de forçar uma.

## Insights
Gatilho: "como aplico isso em X", "questiona meu ponto de vista", "que lacunas isso
deixa", "cruza isso com [algo novo que eu trago]", "que direções isso aponta".
Aqui, diferente dos outros modos, elaborar é o objetivo: use o corpus como base, mas
responda com aplicação prática na situação do usuário, contraponto à posição dele,
cruzamento com o que ele trouxe, ou identificação de lacuna/direção que o corpus não
cobre. Separe claramente, na resposta, o que é citação da fonte do que é raciocínio seu
em cima do que o usuário trouxe.

## Notas
Gatilho: "registra isso numa nota", "nota atômica sobre X".
Uma nota por conceito: atômico é "um conceito por nota", não um teto de frases. O tamanho
é o que o conceito pedir, o bastante pra nota se sustentar sozinha sem precisar do resto
do texto. Sempre ancorada em citação. Se houver arestas `depends-on` ou
`conceptually_related_to` ligadas ao conceito, sugira links pras notas relacionadas.
