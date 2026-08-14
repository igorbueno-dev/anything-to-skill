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

## Estado de progresso
Toda skill gerada tem `.study/progress.json`, criado vazio (`{"temas": {}}`) no build e
preservado em rebuilds (o build nunca sobrescreve um `progress.json` que já existe). Cada
tema tem uma entrada opcional com `status` (`nao_iniciado`, `em_andamento`, `revisado`),
`modos_usados` (lista dos modos já aplicados àquele tema) e `nota` (frase curta livre
sobre o que foi coberto). Tema ausente do JSON conta como `nao_iniciado`. Leia o arquivo
inteiro no início de qualquer modo que se beneficia de saber o que já foi coberto
(leitura incremental, revisão espaçada, percentual coberto, currículo). Escreva no fim de
qualquer interação que cobre claramente um tema (`me ensina`, quiz completo, sessão
socrática revelada, flashcards feitos): leia o JSON inteiro, atualize só a entrada do
tema tocado, grave o JSON inteiro de volta, nunca reescreva do zero. Em `modos_usados`,
use rótulos curtos e consistentes, um por interação (ex.: `me_ensina`, `mapa`,
`curriculo`, `debate`, `flashcards`, `cobertura`, `insight`, `nota`, `quiz`, `socratico`,
`desafio`, `perfis`), preferindo o nome da seção correspondente de study_modes.md em vez
de inventar um termo novo.

## Leitura incremental
Gatilho: "vamos por partes", "continua de onde eu parei", "próximo capítulo". Leia
`.study/progress.json`. Se houver um tema `em_andamento`, retome dali com um resumo de
1-2 frases do que já foi coberto (usando a `nota` salva) antes de avançar. Se todos os
temas estão `nao_iniciado`, comece pelo primeiro na ordem do Currículo (pré-requisito via
`depends-on`) se houver aresta registrada, senão a ordem do roteador. Depois de cobrir um
pedaço, atualize `nota` e o `status` (`em_andamento` ou `revisado`, a seu critério) antes
de perguntar se o usuário quer continuar. Tema sem entrada no JSON ainda é tratado como
`nao_iniciado`, sem erro. Se o tema `em_andamento` já não tem conteúdo não coberto (a
seção inteira já foi tratada segundo a `nota`), marque-o `revisado` e siga direto pro
próximo tema não iniciado (mesma lógica de escolha de tema do início da seção: ordem do
Currículo se houver, senão a ordem do roteador), avisando o usuário que está avançando de
tema.

## Revisão espaçada
Gatilho: "o que eu ainda não revisei", "no que eu deveria focar agora". Leia
`.study/progress.json`, liste os temas com status `nao_iniciado` ou `em_andamento`
(nunca `revisado`), priorizando pré-requisitos (`depends-on`) de temas já `em_andamento`
mas não `revisado`. Se tudo estiver `revisado`, diga isso e sugira aprofundar (Insights,
Debate) em vez de fingir que falta revisar algo.

## Percentual coberto
Gatilho: "quanto eu já cobri", "meu progresso". Conte sobre `.study/progress.json`
contra o total de temas do roteador (`SKILL.md`): `revisado` conta cheio, `em_andamento`
conta meio. Relate como fração ou qualitativo ("3 de 7 temas revisados, 2 em
andamento"), não como número decorado ou gráfico. Arquivo vazio (`{"temas": {}}`) é 0 de
N, sem erro.

## Marco
Gatilho: nenhum explícito, é reativo. Sempre que uma atualização de estado faz um tema
passar para `revisado` pela primeira vez nessa transição, reconheça isso brevemente (uma
frase) antes de seguir com o resto da resposta. Não é um modo que o usuário aciona; é um
comportamento anexado aos outros modos quando a condição acontece. Reabrir um tema já
`revisado` não dispara celebração de novo nem regride o status sem pedido explícito do
usuário.
