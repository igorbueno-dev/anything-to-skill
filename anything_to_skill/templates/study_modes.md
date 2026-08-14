# Modos de estudo

Protocolos pra usar quando o usuário pedir algo além de "recupera e responde". Cada modo
usa dados que já existem nesta skill; nenhum exige gerar arquivo novo. Se o dado
necessário não existir ou for insuficiente pro corpus, diga isso ao usuário em vez de
improvisar, a mesma lógica de "não está nas fontes" que rege o resto desta skill.

## Mapa de dependência
Gatilho: "mapa", "diagrama", "como os conceitos se conectam", "visão geral".
Leia `.graph/graph.json`, filtre as arestas com `relation` igual a `depends-on`, monte um
bloco de diagrama Mermaid (` ```mermaid graph TD `) usando o `label` dos nós, nunca o `id`
cru. Desenhe a seta na ordem de estudo, do pré-requisito pro dependente: numa aresta em que
`source` depends-on `target`, desenhe `target --> source` (quem deve ser estudado primeiro
é o `target`, então a aresta crua sai invertida no diagrama). Acima de uns 20 nós no
recorte pedido o diagrama fica ilegível: sugira focar num tema por vez em vez de despejar o
grafo inteiro. Um nó sem nenhuma aresta `depends-on` tocando ele, nem como source nem como
target, não tem pré-requisito registrado nem nada que dependa dele: liste esse nó à parte,
fora do bloco Mermaid, com uma nota curta dizendo que pode ser estudado a qualquer momento.

## Currículo
Gatilho: "em que ordem estudo", "por onde começo", "monta um plano".
Mesma fonte do mapa (arestas `depends-on`), em ordenação topológica. Ciclo é possível (a
extração é heurística, não garante grafo acíclico): se achar um, avise explicitamente em
vez de forçar uma ordem falsa, e desempate pelo nó de maior `evidence_weight`. Um nó sem
nenhuma aresta `depends-on` tocando ele não tem pré-requisito registrado: liste-o à parte
da ordem, com a nota de que pode ser estudado a qualquer momento.

## Debate
Gatilho: "debate", "onde as fontes divergem".
Leia `tensions.md`. Apresente um lado sem revelar o outro, pergunte a opinião do usuário,
só depois mostre o lado contrário citando a fonte. Se `tensions.md` não tiver contradição
registrada, diga isso; não invente uma tensão pra manter o modo funcionando.

## Flashcards
Gatilho: "flashcards", "me testa rapidinho", "quero revisar".
Leia `glossary.md`. Pra cada entrada do tipo `concept`, gere "O que é `<label>`?". Pra
entrada do tipo `rationale` (uma afirmação, não um nome de conceito), troque pra "Isso é
sempre verdade, segundo a fonte: `<label>`?", já que a resposta existe pra trazer a
nuance/ressalva daquela afirmação. Nos dois casos, segure a resposta (citação + explicação
curta) até o usuário tentar responder.

## Cobertura cruzada
Gatilho: "o que a fonte A cobre que a B não", "compara as fontes".
Leia `coverage.md` e o índice tema-fonte de `sources.md`. Se `coverage.md` não existir
nesta skill, use só o índice tema-fonte de `sources.md`. Corpus de fonte única não tem
comparação possível: diga isso em vez de forçar uma.

## Insights
Gatilho: "como aplico isso em X", "questiona meu ponto de vista", "que lacunas isso
deixa", "cruza isso com [algo novo que eu trago]", "que direções isso aponta".
Aqui, diferente dos outros modos, elaborar é o objetivo: use o corpus como base, mas
responda com aplicação prática na situação do usuário, contraponto à posição dele,
cruzamento com o que ele trouxe, ou identificação de lacuna/direção que o corpus não
cobre. Separe claramente, na resposta, o que é citação da fonte do que é raciocínio seu
em cima do que o usuário trouxe. Quando o usuário traz uma tese própria específica pra
testar contra o corpus, não uma situação pra elaborar em cima, esse é o modo Desafia
minha ideia, não Insights.

## Notas
Gatilho: "registra isso numa nota", "nota atômica sobre X".
Uma nota por conceito: atômico é "um conceito por nota", não um teto de frases. O tamanho
é o que o conceito pedir, o bastante pra nota se sustentar sozinha sem precisar do resto
do texto. Sempre ancorada em citação. Se houver arestas `depends-on` ou
`conceptually_related_to` ligadas ao conceito, sugira links pras notas relacionadas.

## Quiz
Gatilho: "quiz sobre `<tema>`", "monta um quiz", "avalia minhas respostas sobre
`<tema>`". Diferente de Flashcards: aqui é resposta aberta avaliada, não par
pergunta-resposta autoguiado. Gere 3 a 5 perguntas abertas a partir dos conceitos do
tema (`glossary.md` e/ou `sections/<tema>.md`), uma de cada vez, nunca formulada de um
jeito que entregue a resposta na própria pergunta. Depois de cada resposta do usuário,
compare com o que a fonte diz, aponte o que bateu e o que faltou, citando. Sem nota
numérica: feche com um resumo qualitativo do que foi bem e o que vale revisar. Tema com
menos conceitos que o pedido usa quantos houver e avisa.

## Modo socrático
Gatilho: "me guia por `<tema>`", "quero descobrir sozinho", "modo socrático". Em vez de
responder direto, faça uma pergunta-pista primeiro, apontando pro pré-requisito via
aresta `depends-on` (mesma lógica do Currículo) ou um trecho da fonte sem entregar a
conclusão. Na resposta seguinte do usuário, certa, errada ou "não sei", revele e
explique citando a fonte. Uma rodada de pista, não insista em várias. Conceito sem
pré-requisito registrado usa uma pista baseada no próprio trecho da fonte em vez do
grafo. Se o tema tiver mais de um conceito candidato e o pedido do usuário não
especificar qual, pergunte ao usuário qual conceito ele quer trabalhar antes de montar a
pista, em vez de escolher um arbitrariamente.

## Desafia minha ideia
Gatilho: usuário apresenta uma tese própria ("desafia isso:", "questiona:"). Busque no
corpus (`content/`, `sections/`) evidência que sustente ou contradiga a tese trazida
pelo usuário. Diferente do modo Debate: Debate parte de uma tensão já registrada em
`tensions.md`; aqui não há arquivo pronto, é busca no texto. Se achar, cite; se o corpus
não tiver nada diretamente relacionado à tese, diga isso em vez de inventar um
contra-argumento não ancorado. Se o corpus tiver evidência dos dois lados, que sustenta e
que contradiz a tese, apresente as duas, cada uma citada, sem forçar um veredito único e
sem reconciliar as duas numa conclusão própria: isso não é o modo Insights.

## Comparação entre perfis
Gatilho: "como um paper trata isso comparado com um livro didático", "compara os
perfis sobre `<tema>`". Leia `sources.md` (lista `perfil: <profile>` por fonte) e o
índice tema-fonte. Se o tema tiver fontes de perfis diferentes cobrindo-o, compare como
cada uma trata o assunto, citando trechos de cada. Corpus de perfil único não tem o que
comparar: diga isso em vez de forçar uma. Diferente de Cobertura cruzada: Cobertura
cruzada olha o que cada fonte cobre ou não cobre (presença/ausência de tema);
Comparação entre perfis olha como fontes de perfis diferentes tratam o mesmo tema
(diferença de ênfase/formalismo), assumindo que o tema já é coberto por ambas.
