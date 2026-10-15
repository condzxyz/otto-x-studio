# O código de 2026 premia conversa original

Em outubro de 2026, o "Para você" do X é um transformer derivado do Grok-1. Para cada leitor, ele prevê a probabilidade de cerca de vinte ações e soma essas probabilidades com pesos que o X publica e re-sincroniza quase todo dia. No commit de 14/10/2026 (sync de 13/10), os pesos positivos são curtir 0,66, responder 5 (20 entre mútuos, em post original), citar 5, mandar por DM 5, copiar link 20 e seguir o autor 4. Os negativos são "não tenho interesse" −52,272, silenciar −58,8 e denunciar −234. Para uma conta pequena, as regras explícitas em volta dessa soma pesam mais do que os pesos:

- post de quem o leitor não segue vale ×0,75;
- o 2º e o 3º post do mesmo autor no mesmo lote valem ×0,625 e ×0,4375;
- repost e reply não chegam a quem não segue o autor;
- cada conversa ocupa uma única vaga no feed;
- nada com mais de 48 h entra;
- por carregamento, um único post original pode subir até o score da 16ª posição. Ele precisa ser de autor com até 50 mil seguidores, ter menos de 2 h e menos de 200 views na Home, e é escolhido por sorteio ponderado por curtidas ÷ views.

Em relação ao código de 2023, três coisas sumiram: o "reply respondida pelo autor = 75", o clique no perfil que valia 12 e o boost ×4/×2 de verificado. Também não existe penalidade de link, nem peso de bookmark, nem peso de visualização de vídeo. A ciência de difusão chega ao mesmo lugar por outro caminho: a popularidade depende de um broadcast grande e é imprevisível, e os seguidores chegam em rajadas, puxados por reciprocidade e reshares. Os casos de build in public com fonte primária mostram que expor o processo traz os primeiros usuários quando quem acompanha é quem compra. O começo é lento (a Plausible levou 324 dias até US$ 400 de MRR), e a escala vem de conteúdo útil ao comprador.

Para a @ottodoti, isso se traduz em:

- três posts originais por dia, espaçados o bastante para cada um ter a própria janela de 2 h;
- citação no lugar de repost;
- respostas escritas por gente, em conversas de contas médias;
- mútuos reais no nicho;
- imagem 4:5 e vídeo curto e mudo a serviço do texto;
- todo número citado com a data do commit, porque dois pesos mudaram duas vezes nas últimas duas semanas.

*Como ler as etiquetas.* **[código]** = lido no fonte do `xai-org/x-algorithm` (commit `17c96bf`, 14/10/2026; o `param.rs` diz "last sync 2026-10-13T16:00:30Z"). **[código 2023]** = lido no `twitter/the-algorithm` ou `the-algorithm-ml` de 2023. **[declaração oficial]** = README do repositório, central de ajuda ou post de funcionário do X; quando chegou via imprensa, isso é indicado. **[estudo]** = pesquisa com amostra e método declarados; o texto diz se é revisada por pares ou se são dados descritivos de ferramenta. **[relato]** = autodeclaração de fundador, praticante ou vendedor, sem método. **[inferência]** = dedução a partir dessas fontes.

## Vinte probabilidades e uma soma ponderada decidem a ordem do feed

O feed é montado a cada carregamento pelo serviço `home-mixer` [código].

**Fontes de candidatos.** Quatro fontes, ligadas por padrão, rodam em paralelo ([param.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs); [phoenix_candidate_pipeline.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs#L356-L366)):

| Fonte | O que traz | Limite |
|---|---|---|
| Thunder | posts recentes de quem o leitor segue | **1.200** |
| retrieval do Phoenix | posts de fora da rede | **1.000**, mais **200** num retrieval só de cold start |
| SimClusters | posts de comunidades de interesse | não informado |
| posts populares | lista compartilhada | **500** |

Outras fontes, como tweet-mixer e MoE, estão desligadas.

**Hidratação e filtros.** Cada candidato recebe dados do autor, follow mútuo, mídia, idioma, contagens de engajamento e semantic IDs. Depois passa por **19 filtros**.

**Ranking.** O transformer Phoenix pontua o candidato, e o `vm-ranker` recalcula a soma ponderada, aplica cold start, diversidade de autor e desconto fora da rede. Em seguida reordena tudo com um DPP (`DppTheta = 0.65`) que abre mão de um pouco de score para que posts vizinhos sejam menos parecidos ([vm_ranker.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/vm_ranker.rs); [vm-ranker/scoring/mod.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/scoring/mod.rs); [dpp.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/dpp.rs#L40-L140)).

**Saída.** Do top 50 saem **35 posts por resposta**, com "Quem seguir" fixo na 6ª posição ([config.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/config.rs#L17-L34)). Decidir se um post pode ser mostrado é outro sistema: segundo o README, "whether a post can be shown at all is decided separately, by visibility-filtering", que responde ALLOW, NOTICE, INTERSTITIAL ou DROP ([README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)).

O modelo foi "ported from the Grok-1 open source release". O README de 20/01/2026 dizia ter eliminado "every single hand-engineered feature" ([commit aaa167b](https://github.com/xai-org/x-algorithm/commit/aaa167b3de8a674587c53545a43c90eaad360010)). O que ele recebe [declaração oficial]:

- **do post:** semantic IDs de 6 níveis × 256, derivados do embedding multimodal de texto e mídia, mais o hash do autor;
- **do contexto:** fuso, hora local, superfície e idade do post;
- **do leitor:** país, idioma, localização, gênero, faixa etária e apps instalados.

Cada candidato é pontuado isolado dos demais ("candidate isolation") ([phoenix/README.md](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/README.md)). Na prática, o assunto e a mídia de um post viram um código, e o retrieval usa esse código para achar leitores parecidos com quem já engajou com códigos parecidos [inferência]. Daí dois efeitos que puxam em sentidos opostos: um tema constante ajuda o sistema a achar o público, e o DPP rebaixa posts quase iguais que caem na mesma página.

A tabela abaixo traz os pesos espelhados de produção, com a história recente de cada um, tirada do `git log -p` do arquivo [código] ([param.rs, L320-L438](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L320-L438); commits [e1a0375](https://github.com/xai-org/x-algorithm/commit/e1a0375a903899984545c663bb0bccb3cdcdf046), [17c96bf](https://github.com/xai-org/x-algorithm/commit/17c96bf346df3d62b90f1bb01830d432dba74485), [a707cc2](https://github.com/xai-org/x-algorithm/commit/a707cc27ba36d3fa79450c9cffcc48a82d080b02), [0d3cdd8](https://github.com/xai-org/x-algorithm/commit/0d3cdd806c405f04db7030f720b48687aa304061), [78460ca](https://github.com/xai-org/x-algorithm/commit/78460ca8b65c57ddd3a05f9217c8aaeba214b628)).

| Ação prevista | Peso (sync 13/10/2026) | Histórico desde a publicação dos pesos (13/08/2026) |
|---|---|---|
| Curtir | **0,66** | 0,5 → 0,6 (commit de 13/10) → 0,66 (commit de 14/10) |
| Responder | **5**; **20** com follow mútuo, em post original | boost de +20 em 13/07, reduzido para +15 em 24/07 |
| Repostar | 1 | estável |
| Citar | **5** | estável |
| Compartilhar | 2 | estável |
| Compartilhar por DM | **5** | estável |
| Copiar link | **20** | estável |
| Seguir o autor | **4** | estável |
| Clique | 0,3 | 0,4 → 0,3 (29/09) |
| Tempo após o clique (`click_dwell_time`) | 0,4 | 0 → 0,4 (29/09) |
| Abrir link | 0,2 | estável |
| Dwell (binário) | 0,05 | 0 → 0,05 (25/08) |
| Tempo de dwell contínuo | 0,006 | 0,004 → 0,006 (13/10) |
| Expandir foto | 0,05 | estável |
| Abrir vídeo | 0,02 | 0,05 → 0,07 (25/08) → 0,02 (13/10) |
| Visualização qualificada de vídeo (VQV) | **0** | 0,05 → 0 (25/08) |
| Clique no perfil | **0** | estável |
| Não tenho interesse | **−52,272** | −43,2 → −47,52 (29/09) → −52,272 (commit de 14/10) |
| Silenciar o autor | −58,8 | estável |
| Bloquear o autor | −31,2 | estável |
| Denunciar | −234 | estável |
| Não se demorar no post | −0,02 | estável |

O próprio código ensina a ler essa tabela, num comentário escrito para desmontar folclore [código]: "Each weight multiplies the *predicted* probability of that action… the weights do not multiply raw engagement counts". O mesmo comentário diz que é errado concluir que "one report cancels 468 likes", porque "the baseline probability of a Report is more than 1000x lower than a Like, so it's weighted more to allow the prediction to affect the final ranking at all" ([param.rs, L291-L319](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L291-L319)). A nota de 14/08/2026 do README acrescenta que essas probabilidades são "substantially driven by your own behavior" ([README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)). É a lógica que o Twitter já declarava em 2023: os pesos tinham sido calibrados para que cada probabilidade ponderada contribuísse "a near-equal amount to the score" na média ([README do recap, 05/04/2023](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)). **Peso alto sinaliza ação rara, não ação que "vale mais curtidas".**

Quatro detalhes do mesmo comentário e do código em volta mudam a tática:

- **A ação só conta se acontecer num post servido na Home.** Nas palavras do X, "directly navigating to a post (i.e., coordinating via groupchat) has no ranking impact".
- **Denúncia de mal-intencionados pesa pouco fora da bolha deles.** Elas afetam sobretudo as recomendações para usuários parecidos com quem denunciou ([param.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L307-L319)).
- **Soma negativa afunda o post para aquele leitor.** Um offset de 0,001 joga esse post para baixo de todos os posts de soma positiva ([scoring.rs, L161-L171](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L161-L171)).
- **Bookmark não pontua.** Ele existe como rótulo de treino, mas não tem cabeça nem peso no value model ([constants.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/xrex/data/recsys/constants.py#L38-L40); [phoenix_scores.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/phoenix_scores.rs)).

## Regras explícitas pesam mais que os pesos para uma conta pequena

### O que filtra antes do ranking

O primeiro corte é de rede [código]:

- **Desconto fora da rede.** Posts de quem o leitor não segue recebem **×0,75**, ou ×0,5 em pedidos de tópico. O mesmo ×0,75 vale para replies e reposts de contas que o leitor segue, porque `EnableOonRescoreForInNetworkRepliesRetweets = true` ([vm-ranker/params.rs, L187-L228](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs); [scoring.rs, L206-L216](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L206-L216)).
- **Repost e reply não saem da rede.** Reposts de quem o leitor não segue são removidos antes do score. Replies também, porque a flag que deixaria o Phoenix trazer replies de fora da rede, criada em 03/10/2026, está desligada (`EnablePhoenixOonReplies = false`) ([oon_retweet_reply_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/oon_retweet_reply_filter.rs#L15-L27); [param.rs, L73-L84](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L73-L84)).
- **Reply só chega a seguidores em dois casos.** O Thunder inclui a reply se ela responde a um post original, ou se responde a uma reply desse original dirigida a alguém que o leitor segue ([post_store.rs, L338-L359](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/thunder/posts/post_store.rs#L338-L359)).
- **Deduplicação.** Vários reposts do mesmo post viram um só antes do ranking, e depois do ranking cada conversa mantém apenas o item de maior score ([retweet_deduplication_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/retweet_deduplication_filter.rs); [dedup_conversation_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/dedup_conversation_filter.rs)).
- **Já visto sai.** Isso inclui reposts e replies cujo original o leitor já viu, e posts servidos nos últimos 10 minutos ([param.rs, L990-L1001](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L990-L1001); [previously_seen_posts_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/previously_seen_posts_filter.rs)).
- **Corte de idade.** Qualquer post com mais de **48 h**, contadas pelo snowflake do ID, é descartado pelo `AgeFilter` ([config.rs, L40](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/config.rs#L40); [age_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/age_filter.rs)).

O resultado é que, para alcançar quem não segue a marca, só dois formatos chegam: **post original e quote** [inferência].

### Diversidade de autor

A diversidade de autor usa a fórmula `(1 − piso) × 0,5^k + piso`, com piso 0,25. Nela, k é o número de posts do mesmo autor com score maior no mesmo lote de candidatos. Isso dá **1,0 para o 1º post, 0,625 para o 2º, 0,4375 para o 3º e 0,34375 para o 4º**, tendendo a 0,25. O mecanismo está ligado no `vm-ranker` [código] ([scoring.rs, L183-L204](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L183-L204); [vm-ranker/params.rs, L169-L186](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs)).

Há uma ressalva importante sobre esses valores e sobre o ×0,75. Os dois estavam no arquivo marcado como espelho de produção até o sync de 22/09/2026. Em 24/09 foram movidos para `vm-ranker/params.rs`, que não tem essa marca e cujos defaults de curtir e de "não tenho interesse" estão defasados ([commit 44d37eb](https://github.com/xai-org/x-algorithm/commit/44d37ebf87f2185b949cd37b710d410c2a77d21f)). São prováveis em produção hoje, mas **confirmados só até 22/09**.

Nikita Bier descreveu o mesmo mecanismo por volta de 30/05/2026: o app puxa 35 posts por vez, e os posts extras de um autor que aparece várias vezes vão para o lote seguinte [declaração oficial, via página de trending do X; o post original não foi localizado] ([X trending](https://x.com/i/trending/2060629176668094923)).

### A vaga de cold start

Essa é a regra que mais importa para uma conta pequena [código] ([param.rs, L489-L562](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L489-L562); [author_cold_start.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs)). Em cada carregamento, **um** post recebe `max(score próprio, score do 16º candidato)`, desde que cumpra cinco condições:

1. é original (não é reply nem repost; quote conta como original);
2. o autor tem até **50.000 seguidores**;
3. o post tem até **2 h**;
4. tem menos de **200 views na Home**;
5. está entre os 97% melhores candidatos com score diferente de zero.

**Como o vencedor é escolhido.** Para cada elegível, o código sorteia uma amostra de Beta(0,75 + curtidas, 49,25 + views − curtidas). Esse prior tem média de 1,5% de curtidas por view. Ficam os 2 maiores sorteios, e vence o de maior score do modelo. Um teste do repositório mostra que um post com 10.000 views e 0 curtidas perde para um post com 0 views, mesmo com score de modelo 10× maior ([author_cold_start.rs, L988-L1007](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs#L988-L1007)).

**Os limites são recentes.** Mudaram todos de uma vez em 30/09/2026 ([commit 77d431a](https://github.com/xai-org/x-algorithm/commit/77d431aabf409ca1c1eed9bec7e2183f7c914e23)):

| Parâmetro | Antes de 30/09/2026 | Desde 30/09/2026 |
|---|---|---|
| Views na Home | 1.000 | **200** |
| Seguidores do autor | 1.000 | **50.000** |
| Idade do post | 48 h | **2 h** |
| Faixa de posição | 85% | **97%** |
| Thompson sampling | desligado | **ligado** |

Um retrieval dedicado (datasets `HomeCold` e `ZeroFav`, 200 resultados) ajuda a colocar esses posts no lote de quem não segue, além do retrieval normal do Phoenix e do SimClusters ([phoenix_source.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/sources/phoenix_source.rs#L120-L165)). O critério de seleção desse índice não foi publicado.

**Três consequências** [inferência]:

- **A "posição 16" é um score-alvo, não um lugar garantido.** Para não seguidores, o ×0,75 e a diversidade entram depois do lift, e o DPP reordena em seguida ([scoring.rs, L263-L330](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L263-L330)).
- **A janela útil é curta.** Vale até 2 h ou 200 views na Home, o que vier primeiro. Seis curtidas nas primeiras 100 views levam a média do Beta de 1,5% para cerca de 4,5%.
- **Fio não ajuda aqui.** Só o post raiz disputa a vaga, porque replies não são elegíveis.

### Quanto um post da marca precisa para empatar

Os multiplicadores se somam. A tabela compara o post da marca com o 1º post de uma conta que o leitor segue [inferência a partir do código]:

| Post da marca no mesmo lote | Diversidade | Com ×0,75 (leitor não segue) | Score previsto necessário para empatar |
|---|---|---|---|
| 1º | 1,0 | 0,75 | 1,33× |
| 2º | 0,625 | 0,469 | 2,13× |
| 3º | 0,4375 | 0,328 | **3,05×** |
| 4º | 0,344 | 0,258 | 3,88× |

### Visibilidade e o rótulo de replies

A camada de visibilidade e os classificadores com LLM completam o quadro [código]:

- **Filtro eleitoral.** O `Brazil2026ElectionFilter` remove do "Para você" de quem não segue a conta listada todo post que seja da conta, repost, quote ou reply envolvendo uma das contas da lista do TSE (25 IDs no teste; lista atualizada em 13/10/2026) ([brazil_2026_election_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/brazil_2026_election_filter.rs#L84-L98); [README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)).
- **Regras só para recomendação.** Spam detectado "at high recall" e URL maliciosa derrubam o post apenas como recomendação a quem não segue. Se o post citado cair, o quote cai junto ([levels.rs, L60-L123](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/visibility-filtering/rules/levels.rs#L60-L123); [README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)).
- **Nota em tempo real para replies.** O `grox` pontua toda reply ([constants.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/constants.py); [task_filter.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/task_filter.py); [classifier_simple_reply_scorer.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/classifier_simple_reply_scorer.py)):

| Tamanho da conversa | Quem dá a nota |
|---|---|
| post respondido **ou** raiz da thread com mais de **250.000** seguidores | **Grok** (4 mini, com fallback 4.1 fast) |
| ambos com até 250.000, mas algum acima de 125.000 | Gemma 4 26B específico de spam em reply |
| ambos com até 125.000 | Gemma 4 26B genérico |
| reply que contém quote, em qualquer tamanho | Grok |

**Nota zero vira rótulo.** Uma reply com nota 0 recebe o rótulo `RiskyHighVizReply`. Só escapam autores com user-cred ≥ 66, selo cinza ou contas de teste ([task_write.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/task_write.py)). A tarefa que dá nota às replies também registra em log `is_pasted`, `composition_source` e `app_attestation_status`. O código mostra o registro, mas não mostra se esses campos entram na nota ([task_rank_replies.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/reply_spam/task_rank_replies.py)). Os prompts não foram publicados, "to reduce the risk of gaming" ([README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)).

### O que o código não favorece nem pune

- **Premium não multiplica o score.** Não há termo de Premium ou de verificado no ranking. As contas verificadas só entram como metade do vetor de teleporte do PageRank que gera o user-cred (0–100), usado em isenções antiabuso ([UserCredV2App.scala](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/user-cred-v2/UserCredV2App.scala); [weights.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/weights.rs)).
- **Link não é penalizado.** Não há termo de penalidade. O `has_url` só aparece num payload experimental, desligado (`VMRankerSendDebiasInputs = false`) ([vm_ranker_debias_payload.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/vm_ranker_debias_payload.rs)).
- **Vídeo não ganha bônus.** O VQV tem peso 0 e só seria elegível para vídeo acima de 10 s, visto por leitor com menos de 10 mil seguidores ([candidates_util.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/util/candidates_util.rs)). O carrossel de vídeo, que só aceita vertical, está desligado (`EnableVideoCarousel = false`) ([param.rs, L1053-L1082](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L1053-L1082); [video_carousel.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/util/video_carousel.rs)).

## De 2023 para 2026, a conversa com o autor perdeu o peso de 75

Em 2023, o "Para você" combinava um heavy ranker MaskNet de ~48 milhões de parâmetros com uma camada de heurísticas com multiplicadores explícitos ([blog do Twitter Engineering, 31/03/2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)). O ranker usava ~6.000 features e escolhia os melhores entre cerca de 1.500 candidatos por pedido, metade de dentro da rede em média. Em 2026, o centro é um transformer que prevê ações, e os pesos só foram publicados em 13/08/2026. O release de janeiro importava um módulo `params` que não estava na árvore ([commit 47c1bcd](https://github.com/xai-org/x-algorithm/commit/47c1bcdadfe4911568fd6db4f8838b194325beab)).

| Mecanismo | 2023 [código 2023 / declaração oficial] | 2026 [código, 14/10/2026] |
|---|---|---|
| Modelo | MaskNet paralelo, ~48M parâmetros, ~6.000 features | Transformer Phoenix portado do Grok-1, sem features manuais |
| Curtir | 0,5 | 0,66 |
| Responder | 13,5 | 5 (20 entre mútuos) |
| Reply engajada pelo autor | **75** | não existe |
| Abrir o perfil e engajar | 12 | clique no perfil **0** |
| Entrar na conversa e ficar ≥ 2 min | 10 | tempo após o clique 0,4 (contínuo) |
| Citar, DM, copiar link, seguir | sem peso próprio | 5, 5, 20, 4 |
| Vídeo | assistir 50%: 0,005 | VQV 0; abrir vídeo 0,02 |
| Negativos | negative feedback −74; report −369 | não tenho interesse −52,272; mute −58,8; block −31,2; report −234 |
| Autor verificado | ×4 dentro da rede, ×2 fora (default) | sem termo |
| Fora da rede | ×0,75; 1 post por autor; prova social de 2º grau | ×0,75 (inclui replies e reposts de seguidos); vaga de cold start |
| Diversidade de autor | decay 0,5, piso 0,25 | decay 0,5, piso 0,25 (vm-ranker) |
| Links | filtro de URL de concorrentes fora da rede; spam para Tweepcred < 25 | só URL maliciosa derruba |
| Mídia | ×2 imagem/vídeo declarado com `applyBoosts = false` | expandir foto 0,05, sem bônus |
| Recência | decaimento suave (`slope = 0.005`) | corte em 48 h e janela de exploração de 2 h |

Fontes: [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md); [VerifiedAuthorScalingScorer](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/VerifiedAuthorScalingScorer.scala); [OONTweetScalingScorer](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/OONTweetScalingScorer.scala); [DiversityDiscountProvider](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/DiversityDiscountProvider.scala); [RelevanceSearchUtil](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/util/earlybird/RelevanceSearchUtil.scala); [OutOfNetworkCompetitorURLFilter](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/filter/OutOfNetworkCompetitorURLFilter.scala); [SpamVectorScoringFunction](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/java/com/twitter/search/earlybird/search/relevance/scoring/SpamVectorScoringFunction.java).

A tabela mostra uma mudança de filosofia. **Em 2023, o maior prêmio ia para o esforço do autor** (75 para a reply que o autor respondia). **Em 2026, vai para o grafo social e para o "mandar para alguém"**: reply entre mútuos vale 20, DM 5, copiar link 20. A recência deixou de ser um decaimento suave e virou um experimento com prazo, de 2 h para a exploração e 48 h para a vida útil.

O que sobreviveu mostra o que o X considera estrutural. O ×0,75 fora da rede e a diversidade de autor com 0,5 e piso de 0,25 têm a mesma fórmula nos dois códigos. Já existiam em 2023 e continuavam no commit intermediário de 03/09/2025 do repositório antigo ([G25 OONTweetScalingScorer](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/OONTweetScalingScorer.scala); [G25 DiversityDiscountProvider](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/DiversityDiscountProvider.scala)). Esse commit de 2025 também é a ponte para o boost de verificado: o `VerifiedAuthorScalingScorer` já não aparecia entre os scorers. Além disso, ganharam parâmetro próprio bookmark, dwell, share, screenshot, `open_link` e negative feedback forte/fraco, todos com default 0.0 e valores não publicados ([G25 HomeGlobalParams.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/param/HomeGlobalParams.scala); [G25 scorers](https://github.com/twitter/the-algorithm/tree/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer)).

Musk prometeu em 17/10/2025 a "deletion of all heuristics within 4 to 6 weeks" [declaração oficial] ([post](https://x.com/elonmusk/status/1979217645854511402)). O código de outubro de 2026 não cumpre a promessa ao pé da letra: filtros, decaimentos, o ×0,75 e a vaga de cold start continuam explícitos. O que sumiu foram as features manuais do modelo, não as regras de distribuição.

Dois pontos de 2023 não têm equivalente visível nas notas de 2026 e não devem ser repetidos como vigentes. Um é o "see fewer", que filtrava o autor por 14 dias e depois aplicava ×0,2 até voltar a ×1,0 em 140 dias ([FeedbackFatigueScorer 2023](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/FeedbackFatigueScorer.scala)). O outro é a penalidade de Tweepcred para quem segue mais de 2.500 contas com razão seguindo/seguidores acima de 0,6 ([Reputation.scala 2023](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/graph/batch/job/tweepcred/Reputation.scala)). A reputação de 2026 é outra fórmula: `165,2 + 7,07·ln(massa)`, sobre um PageRank do grafo de follows e de engajamento. O teleporte desse PageRank vem metade de contas verificadas e metade de curtidas e reposts dos últimos 7 dias ([UserCredV2.scala](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/user-cred-v2/UserCredV2.scala); [UserCredV2App.scala](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/user-cred-v2/UserCredV2App.scala)). A leitura feita não achou nela penalidade pela razão de follows.

## A ciência de difusão explica por que o código sorteia

A pesquisa sobre o Twitter não estuda o código de 2026; quase toda ela usa dados de 2006 a 2020. Mesmo assim, ela explica por que o X construiu um sorteio para contas pequenas.

**O alcance é imprevisível.** Goel, Anderson, Hofman e Watts analisaram um bilhão de eventos de difusão e concluíram que a viralidade estrutural "is typically low", e que a popularidade "is largely driven by the size of the largest broadcast" [estudo, revisado] ([Management Science, 2016](https://doi.org/10.1287/mnsc.2015.2158)). Salganik, Dodds e Watts mostraram, com 14.341 participantes num mercado musical artificial, que a influência social aumenta "both inequality and unpredictability of success" [estudo, revisado] ([Science, 2006](https://doi.org/10.1126/science.1121066)). Bakshy e colegas, com 1,6 milhão de usuários e 74 milhões de cascatas, acharam a previsão de qual post vai explodir "relatively unreliable" [estudo, revisado] ([WSDM 2011](https://doi.org/10.1145/1935826.1935845)). Weng e colegas reproduziram a heterogeneidade de popularidade de memes só com atenção limitada, sem supor diferença de qualidade entre as ideias [estudo, revisado] ([Scientific Reports, 2012](https://doi.org/10.1038/srep00335)). Num mundo assim, um ranker que só explora o que já tem sinal reforça a sorte inicial.

**O código responde a isso.** O Thompson sampling da vaga de cold start dá chance a posts de alta incerteza, e a ponto de o post com zero views vencer o post com 10 mil views e zero curtidas. Para quem posta, a consequência é a mesma de Salganik e Bakshy [inferência]: **avalie por média de muitos posts, não pelo resultado de um**. Volume constante compra mais bilhetes para o sorteio.

**A vantagem cumulativa existe, mas tem limite.** Um upvote aleatório inicial aumentou em 32% a chance do voto positivo seguinte, num agregador de notícias que não é o Twitter [estudo, revisado] ([Muchnik, Aral & Taylor, Science 2013](https://doi.org/10.1126/science.1240466)). Experimentos de campo mostram que o sucesso inicial aleatório ajuda, mas com **retornos decrescentes** [estudo, revisado] ([van de Rijt et al., PNAS 2014](https://doi.org/10.1073/pnas.1316836111)). O próprio recomendador "Quem seguir" do Twitter, lançado em 2010, fez "the most popular users" ganharem "substantially more than average" [estudo, revisado] ([Su, Sharma & Goel, WWW 2016](https://doi.org/10.1145/2872427.2883040)).

**Seguidores chegam em rajadas.** Myers e Leskovec mostraram que ganhos e perdas seguem taxas estáveis "interrupted by sudden bursts", e que cascatas de reshare "often create such sudden bursts" [estudo, revisado] ([WWW 2014](https://doi.org/10.1145/2566486.2568043)). Antoniades e Dovrolis acharam que follows causados por retweet são "much more likely than the exogenous creation of new followers". Os fatores mais fortes foram **reciprocidade** e o número de retweets que o potencial seguidor recebe [estudo, revisado] ([Computational Social Networks, 2015](https://doi.org/10.1186/s40649-015-0023-6)). Hutto, Yardi e Gilbert acompanharam 507 usuários por 15 meses e concluíram que conteúdo, comportamento social e estrutura de rede "should be given equal consideration" para prever novos seguidores [estudo, revisado] ([CHI 2013](https://doi.org/10.1145/2470654.2470771)). Na cobertura de imprensa do mesmo estudo, conteúdo informativo atraiu muito mais seguidores que conteúdo pessoal, e negatividade e abuso de hashtags atrapalharam [estudo, via imprensa] ([Popular Science, fev/2013](https://www.popsci.com/science/article/2013-02/more-twitter-followers-try-more-information-less-negativity/)). Cha e colegas viram que a influência vem de "concerted effort such as limiting tweets to a single topic" [estudo, revisado] ([ICWSM 2010](https://doi.org/10.1609/icwsm.v4i1.14033)).

**Perder seguidores também tem padrão.** Kwak, Chun e Moon acompanharam 1,2 milhão de usuários coreanos por 51 dias: 43% deram unfollow ao menos uma vez. Nas 22 entrevistas, os motivos citados foram **rajadas de tweets**, temas desinteressantes e detalhes banais do dia a dia [estudo, revisado] ([CHI 2011](https://dspace.kaist.ac.kr/handle/10203/168161)).

**Esses resultados batem com o código** [inferência]. Reciprocidade corresponde ao boost de mútuos. Exposição por reshare corresponde ao quote, que vai para fora da rede. Foco temático corresponde aos semantic IDs e ao SimClusters. Rajadas correspondem ao decaimento de autor.

**A ciência também mostra um atalho que uma marca não deve tomar.** Cada palavra moral-emocional aumentou a difusão em ~20% em 563.312 tweets [estudo, revisado] ([Brady et al., PNAS 2017](https://doi.org/10.1073/pnas.1618923114)). Cada termo sobre o grupo rival aumentou em **67%** as chances de compartilhamento em 2,7 milhões de posts [estudo, revisado] ([Rathje, Van Bavel & van der Linden, PNAS 2021](https://doi.org/10.1073/pnas.2024292118)). A falsidade se espalhou "farther, faster, deeper" que a verdade, puxada pela novidade e por humanos, não por bots [estudo, revisado] ([Vosoughi, Roy & Aral, Science 2018](https://doi.org/10.1126/science.aap9559)). Um audit pré-registrado mostrou, porém, que o ranking por engajamento do Twitter "amplifies emotionally charged, out-group hostile content" e que os usuários **não preferem** os tweets políticos escolhidos por ele [estudo, revisado] ([Milli et al., PNAS Nexus 2025](https://doi.org/10.1093/pnasnexus/pgaf062)).

**No código de 2026, essa insatisfação tem preço.** "Não tenho interesse" vale −52,272 e silenciar −58,8, contra 5 de uma reply. Um post que provoca mute em parte do público pode ficar com soma negativa justamente para os leitores parecidos com quem silenciou. A alavanca que a ciência sustenta sem esse risco é a **novidade**, com dado concreto. A síntese de indústria e academia de 2024 aponta que métricas de qualidade "can improve long-term retention" mesmo quando correlacionam negativamente com engajamento de curto prazo [estudo, workshop] ([Cunningham et al., arXiv 2024](https://arxiv.org/abs/2402.06831)).

## Construir em público traz os primeiros usuários, não a escala

Os casos de build in public com fonte primária contam a mesma história: **o começo é lento e público, e a transparência funciona melhor quando quem acompanha é quem compra**.

| Caso | O que abriram | Números (fonte e data) |
|---|---|---|
| **Plausible** | updates de BIP no blog, no Indie Hackers e no Twitter do Uku | **324 dias** até os primeiros US$ 400 de MRR; mai/2019 US$ 64 → jan/2021 US$ 11.303 → US$ 1M de ARR em 02/06/2022, com 7.000+ assinantes, 4 pessoas e sem anúncio pago |
| **Buffer** | salários, receita e roadmap desde 2013 | candidaturas em 30 dias: **2.886 contra 1.263** depois dos salários abertos (19/12/2013); hoje US$ 27,2M de ARR e 288.527 MAU |
| **Ghost** | dashboard de receita desde abril/2015 | US$ 411 mil por ano em 2015; hoje ARR de **US$ 11.132.578** e 30.547 clientes |
| **Transistor** | post de marco com gráfico e salários | ~US$ 20 mil de MRR em 11,5 meses, contra 60 meses estimados |
| **Marc Lou** | página com receita por produto | US$ 93,1k/mês; o maior produto, TrustMRR (US$ 50k/mês), vende para a própria audiência de BIP |

Na Plausible, a atribuição é explícita: "All the early users came from these updates". A escala veio depois, de conteúdo. Um post no Hacker News levou mais de 25.000 visitantes num dia, e vieram textos pegando carona em notícias sobre o Google. O Product Hunt deu mais de 1.000 visitas e só 15 trials [relato, fonte primária] ([Plausible, 22/06/2022](https://plausible.io/blog/open-source-saas)).

No Buffer, o efeito medido da transparência foi no **recrutamento**, não em clientes [relato, via imprensa] ([GovExec, jan/2014](https://www.govexec.com/management/2014/01/after-disclosing-employee-salaries-buffer-was-inundated-resumes/77528/)). Os números atuais vêm da página de transparência [relato, fonte primária] ([Buffer Transparency, acesso em 14/10/2026](https://buffer.com/transparency)). Os da Ghost também ([ghost.org/open, acesso em 14/10/2026](https://ghost.org/open/); [Ghost, abril/2015](https://ghost.org/changelog/april-2015-update/)).

Na Transistor, o fundador atribui o resultado à **demanda do mercado**, não ao BIP [relato, fonte primária] ([justinjackson.ca/30k, 04/10/2019](https://justinjackson.ca/30k)). A página do Marc Lou não diz como a receita é verificada [relato, fonte primária] ([marclou.com, acesso em 14/10/2026](https://marclou.com)). No Brasil, Tiago Costa documentou a Freelup e captou 132 leads em cerca de 10 dias. Ele credita o feedback dos seguidores e o compromisso público [relato, fonte primária] ([TabNews](https://tabnews.com.br/tiagocosta/o-que-30-dias-de-build-in-public-me-ensinaram)).

Os fracassos são tão concretos quanto os sucessos, e quase todos aparecem quando a tração cresce [relato]:

- **Fornecedor de olho na sua receita.** Pieter Levels conta que o provedor de GPU subiu o preço de treino "$3 to $20" depois de ver quanto ele ganhava ([transcrição no Lex Fridman](https://lexfridman.com/pieter-levels-transcript)).
- **Copycat com mais distribuição.** A Lensa copiou o Avatar AI e, segundo a estimativa dele, fez "like $30 million" (mesma fonte).
- **Audiência errada.** Para Cory Zue, BIP é "a pretty terrible channel (unless your product is targeted at other indie hackers)", e mostrar receita "attracted and helped copycats" ([Indie Hackers](https://www.indiehackers.com/post/is-building-in-public-still-worth-your-time-indie-hackers-with-bip-experience-weigh-in-d31f694a34)).
- **Audiência não é receita.** O Indie Hackers, maior comunidade de BIP, estava com "exactly $0 in MRR" em 05/04/2023 ([Indie Hackers](https://www.indiehackers.com/post/whats-new-indie-hackers-is-indie-again-1d228c6387)).
- **Transparência não garante boa saída.** O Baremetrics, pioneiro do "Open Startups", foi vendido por US$ 4M, cerca de 2,65× o ARR ([They Got Acquired](https://theygotacquired.com/saas/baremetrics-acquired-by-xenon-partners/)).
- **Transparência não evita erro de gestão.** O Buffer demitiu 10 pessoas (11%) em 16/06/2016, com US$ 1,3M em caixa que zeraria em 5 meses ([Buffer](https://buffer.com/resources/layoffs-and-moving-forward/)).
- **Print de MRR falso.** A crítica de Levels em out/2025 levou Marc Lou a lançar em 30/10/2025 o TrustMRR, que verifica a receita por API do provedor de pagamento ([IndieRadar](https://indieradar.app/blog/fake-mrr-pandemic-real-benchmarks); [trustmrr.com](https://trustmrr.com/)).
- **Viés de sobrevivência.** É total: não existe estudo causal mostrando que BIP aumenta receita.

A ciência comportamental separa duas coisas que o BIP costuma misturar: **mostrar o processo tem base experimental, mostrar receita é prova social com risco**. As evidências a favor de mostrar o trabalho [estudo, revisado]:

- **Labor illusion.** Em 5 experimentos, as pessoas preferiram um site mais lento que mostrava o trabalho sendo feito a um instantâneo com resultado idêntico, por reciprocidade ao esforço percebido ([Buell & Norton, Management Science 2011](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.1110.1376)).
- **Transparência operacional recíproca.** Quando clientes e cozinheiros se viam, a qualidade percebida subiu **22,2%** e o tempo de atendimento caiu **19,2%** ([Buell, Kim & Tsay, Management Science 2017](https://dash.harvard.edu/entities/publication/73120378-ddad-6bd4-e053-0100007fdf3b)).
- **Transparência de custo.** Mostrar o custo dos ingredientes fez a probabilidade de compra subir de 2,3% para 2,8% (+21,1%). O efeito vale para transparência voluntária e sai pela culatra quando revela margem alta ([Mohan, Buell & John, Marketing Science 2020](https://informs.org/News-Room/INFORMS-Releases/News-Releases/New-Research-Finds-Cost-Transparency-Can-Increase-Sales-20)).

E os limites da transparência:

- **Anunciar a meta pode tirar o esforço.** Intenções ligadas à identidade, quando notadas por outros, foram executadas com **menos** empenho [estudo, revisado] ([Gollwitzer et al., Psychological Science 2009](https://www.socmot.uni-konstanz.de/node/131)).
- **Prova social nem sempre replica.** O experimento das toalhas de hotel não se repetiu na Alemanha [estudo, revisado] ([Bohner & Schlüter, PLoS One 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4118982)).
- **Ser observado pode piorar o trabalho.** Observar operários os levou a esconder o que faziam, e um pouco de privacidade melhorou a performance [estudo, revisado] ([Bernstein, ASQ 2012](https://www.library.hbs.edu/working-knowledge/hiding-from-managers-can-increase-your-productivity)).

Para a @ottodoti, o público do BIP e o comprador coincidem: são criadores e fundadores que publicam em X, LinkedIn e Threads [inferência]. É a condição em que os casos mostram BIP funcionando (Plausible no começo, Marc Lou com o TrustMRR). As regras práticas que saem dessa evidência:

- **Bastidor antes de faturamento.** Como um post foi feito, que decisão o time tomou e por quê, o erro e o que mudou.
- **Resultado antes de intenção.** "Fizemos X, deu Y" em vez de "vamos chegar a Z".
- **Só números verificáveis e datados**, nunca print recortado.
- **Cuidado com custo e margem.** Mostrar o custo de IA por post só funciona se a margem visível não parecer abusiva.

Há também uma diferença de canal. A metanálise de Collins e Miller mostra que a autorrevelação aumenta a simpatia entre pessoas [estudo, revisado] ([Psychological Bulletin, 1994](https://pubmed.ncbi.nlm.nih.gov/7809308/)), um efeito interpessoal que a voz de uma marca captura pior que a do fundador [inferência]. Por isso faz sentido a marca cuidar do processo e do produto, e o fundador da história pessoal, com um citando o outro.

## Quote vence repost, e a reply vale pela conversa

### Repost, quote e reply têm destinos diferentes no código

O **repost é o formato mais fraco** para distribuição [código]:

- só chega a quem já segue quem repostou;
- leva ×0,75;
- é deduplicado contra o original;
- some para quem já viu o original;
- não disputa a vaga de cold start, que exige `retweeted_tweet_id.is_none()` ([author_cold_start.rs, L188-L193](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs#L188-L193)).

O **quote é um post original novo** [código]:

- passa no filtro fora da rede;
- disputa a vaga de cold start;
- pode ganhar o boost de mútuos;
- não herda o "já visto" do post citado, porque o `quoted_tweet_id` não está na lista de IDs checados ([candidates_util.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/util/candidates_util.rs)).

Ser citado também pesa: a probabilidade prevista de o leitor citar tem peso 5, igual à de responder.

A política do X empurra para o mesmo lado [declaração oficial]. Em 11/04/2026, Bier cortou os pagamentos de contas agregadoras para 60%, dizendo que "flooding the timeline with 100 stolen reposts and clickbait everyday crowded-out real creators and hurt new author growth" ([post](https://x.com/nikitabier/status/2043045929750794399); [TechCrunch, 12/04/2026](https://techcrunch.com/2026/04/12/x-says-its-reducing-payments-to-clickbait-accounts/)). Em 23/05/2026, ele anunciou que as impressões de re-uploads passam a ser atribuídas ao criador original ([post](https://x.com/nikitabier/status/2058020001823793265)). Não há estudo com amostra comparando o alcance de quote e repost. A tática "cite com uma linha de opinião ou um dado novo em vez de repostar" vem do código, não de teste.

A reply tem dois destinos diferentes. **Como candidata no feed, ela viaja pouco** [código]:

- não sai da rede;
- leva ×0,75;
- divide uma vaga por conversa;
- some para quem já viu o post-pai.

**Como conversa, ela vale muito para o post que a recebe**: 5 de peso, ou 20 quando o post é original e autor e leitor se seguem ([inputs.rs, L20-L22](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/inputs.rs#L20-L22); [weights.rs, L84-L91](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/weights.rs#L84-L91)). O boost foi testado com 5, 10, 15 e 20 a partir de 10/07/2026, lançado com 20 em 13/07 e reduzido para 15 em 24/07 depois de reclamações de que a Copa do Mundo sumira do feed [declaração oficial] ([BIDIRECTIONAL_BOOST_CHANGE.md](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/docs/BIDIRECTIONAL_BOOST_CHANGE.md)). Bier publicou as métricas do teste em 14/07/2026: "Replies: +3.15% Original Posts: +1.8% Small Account Reach: +1.19% Time Spent: -0.13%" [declaração oficial] ([post](https://x.com/nikitabier/status/2076917480518558035)).

Responder contas grandes, portanto, vale pela **conversa do post grande**: é lá que alguém clica no perfil e segue, e não no "Para você" de quem não segue a marca [inferência]. Acima de 250 mil seguidores, cada reply recebe nota do Grok. A central de ajuda promete prioridade nas respostas em escala por plano (Basic < Premium < Premium+), sem números [declaração oficial, lida via resumo do buscador] ([help.x.com, X Premium](https://help.x.com/en/using-x/x-premium)). A estratégia "reply guy" só tem evidência de [relato]: guias comerciais prometem saltos como "500 → 50 mil seguidores em 8 meses", sem método ([Teract](https://www.teract.ai/resources/twitter-reply-guy-strategy-2026); [Pounce](https://www.pounce.so/blog/reply-guy-tactics-that-actually-grow-your-account)).

Responder no próprio post tem efeito pequeno e positivo. A central diz que a resposta do autor original é sinal na ordenação da conversa [declaração oficial, lida via resumo do buscador] ([help.x.com, Conversations](https://help.x.com/en/resources/recommender-systems/conversations-recommendations)). Num estudo do Buffer com ~2 milhões de posts (nov/2025), responder comentários se associou a **+8% de engajamento no X**, contra +42% no Threads e +30% no LinkedIn, sem causalidade estabelecida [estudo, dados de ferramenta] ([Buffer](https://buffer.com/resources/replying-to-comments-boosts-engagement/)).

### Do zero, a janela de duas horas é o principal canal

**A expectativa inicial é baixa.** Contas sem Premium tinham mediana **abaixo de 100 impressões por post** entre ago/2024 e ago/2025, numa amostra de 18,8 milhões de posts e 71 mil contas [estudo, dados de ferramenta] ([Buffer, 02/10/2025](https://buffer.com/resources/x-premium-review/)). Com esse ponto de partida, o canal de descoberta que o código oferece a uma conta nova é a vaga de cold start, e cada post original é um bilhete [inferência]. Daí saem cinco táticas:

1. **Publicar quando a base está online**, para que as primeiras views na Home virem curtida rápida.
2. **Abrir com um gancho que mereça curtida**, porque o sorteio é por curtidas ÷ views.
3. **Espaçar os originais por pelo menos 2 h**, porque dois posts elegíveis ao mesmo tempo disputam a mesma vaga para o mesmo leitor.
4. **Preferir original e quote a reply e repost** enquanto a conta é pequena.
5. **Não contar com recompensa por perfil.** O clique no perfil tem peso 0, e seguir o autor a partir do post tem peso 4 ([param.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L320-L438)). Bio, cabeçalho e post fixado não aparecem no código de ranking e só afetam a conversão de visita em follow [relato].

Os primeiros seguidores vêm de três frentes:

- **Mútuos reais no nicho.** Reciprocidade é o preditor de follow mais forte em Antoniades e Dovrolis, e cada mútuo faz as respostas dele aos originais da marca valerem 20.
- **Conversas de contas médias.** Nelas o filtro é de spam, não a nota de qualidade do Grok.
- **Starterpacks.** São as listas de "top posters in every niche & country" anunciadas em 21/01/2026 [declaração oficial] ([post](https://x.com/nikitabier/status/2014079005025247240)), com critério de seleção não publicado.

As **Comunidades do X foram extintas em 30/05/2026**: eram usadas por "less than 0.4% of users" e geravam "80% of spam reports, financial scams, and malware" [declaração oficial] ([post](https://x.com/nikitabier/status/2047180747690434994); [Engadget, 23/04/2026](https://www.engadget.com/social-media/x-is-shutting-down-its-communities-feature-182843958.html)). As substitutas são grupos no XChat e Custom Timelines (21/04/2026). Se uma Custom Timeline gera um pedido de tópico, o que é provável mas não está confirmado, dois parâmetros mudam: o fator fora da rede cai para 0,5 e o cold start é ignorado [inferência a partir do código]. Não há estudo com amostra sobre prazos realistas de 0 a 1 mil ou 10 mil seguidores. Os prazos que circulam são [relato].

### Com cerca de 100 posts, a auditoria olha mediana e top 10%

Com 100 posts, a distribuição já tem cauda longa, e a auditoria deve espelhar o que o modelo prevê [inferência, a partir de código e estudos]. Um roteiro em sete passos:

1. **Separar originais de replies e reposts.** Só os originais disputam o cold start e a distribuição fora da rede.
2. **Medir por mil impressões, em mediana e p90.** Curtidas por impressão, respostas, citações, compartilhamentos e follows, nunca pela média.
3. **Isolar o top 10%** e procurar o padrão de tema, formato, gancho, horário e dia.
4. **Comparar as primeiras 2 h dos outliers com as da mediana**, porque é ali que o sorteio decide.
5. **Checar a conversão de visitas ao perfil em follows.** Uma conversão baixa pede bio e fixado melhores.
6. **Abrir o Under the Hood** para ver se há rótulo limitando visibilidade.
7. **Dobrar a aposta em 2–3 padrões do topo** e cortar formatos sempre abaixo da mediana.

O Under the Hood (`x.com/i/jf/under_the_hood`) é um piloto lançado em 13/08/2026 [declaração oficial] ([README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)). Segundo a imprensa, vale para um grupo aleatório de contas com mais de 1 ano e pelo menos 10 posts no mês anterior, e exporta um JSON que o VP de produto sugeriu entregar a uma IA junto com o repositório ([Gigazine](https://gigazine.net/gsc_news/en/20260814-x-timeline-algorithm/); [ProPakistani](https://propakistani.pk/2026/08/17/x-will-finally-tell-you-if-its-algorithm-is-limiting-your-reach/)).

Os benchmarks externos servem como régua grosseira. O Metricool mediu média de 2.711 impressões e 42,7 interações por post no X em 2025, com cliques no perfil caindo 31%, em 1.123.528 posts de 15.116 contas [estudo, dados de ferramenta] ([Metricool](https://metricool.com/x-twitter-statistics/)). Um detalhe atrapalha a auditoria: o código usa views **na Home**, e o painel do X não separa essa origem de forma documentada.

### Cadência: 35 posts por lote e retorno decrescente

O código não pune uma conta por postar muito. O que ele faz é descontar a concentração no mesmo lote [código]. Cada carregamento devolve 35 posts, e os posts não vistos das últimas 48 h de um mesmo autor competem entre si, com 0,625 e 0,4375 para o 2º e o 3º. Para quem abre o app várias vezes por dia, posts espaçados chegam sozinhos, porque os já vistos saem. Para quem abre pouco, os posts do dia disputam o mesmo lote, e **o mais fraco paga o desconto** [inferência].

Não existe estudo causal sobre frequência no X. O Metricool viu a média subir de 15,97 para 17,34 posts por semana entre 2024 e 2025 (cerca de 2,5 por dia), enquanto as impressões médias por post caíram 5% [estudo, dados de ferramenta] ([Metricool](https://metricool.com/x-twitter-statistics/)). Criadores reagiram à fala de Bier sobre os lotes espaçando posts por 30–90 minutos [relato] ([X trending](https://x.com/i/trending/2060629176668094923)). Pela vaga de cold start, a regra coerente com o código para conta pequena é **pelo menos 2 h entre originais** [inferência].

Os estudos de horário convergem só no essencial [estudo, dados de ferramenta]:

| Estudo | Amostra | Melhor janela | Pior janela |
|---|---|---|---|
| Buffer (13/03/2026) | 8,7 milhões de tweets | terça 9h, quarta 9h e 10h; faixa mais confiável 9h–11h em dias úteis | noite (18h–23h); sábado e sexta são os piores dias |
| Sprout Social (mar/2026) | ~2 bilhões de engajamentos, ~307 mil perfis em 6 redes, 27/11/2025–27/02/2026 | terça a quinta, 12h–18h | fim de semana |

Fontes: [Buffer](https://buffer.com/resources/best-time-to-post-on-twitter-x-x/); [Sprout Social](https://sproutsocial.com/insights/best-times-to-post-on-twitter/). Os dois usam hora local, e nenhum tem recorte para o Brasil. A pesquisa revisada recomenda horários **personalizados** por audiência, não uma hora universal [estudo, revisado] ([Spasojevic et al., KDD 2015](https://doi.org/10.1145/2783258.2788584)).

### Formatos: nenhum bônus no código, vantagens pequenas e instáveis nos dados

O código não premia formato. Ele pontua ações, e a ação de mídia que tem algum peso é o tempo de atenção depois do clique (0,4), muito acima de expandir foto (0,05) e abrir vídeo (0,02) [código]. Os dados observacionais divergem por métrica [estudo, dados de ferramenta]:

| Formato no X | Buffer 2026: ER mediano por seguidor | Ordinal: ER por impressão | Ordinal: impressões médias |
|---|---|---|---|
| Texto | 3,56% | 0,67% | **46.731** |
| Imagem | 3,40% | **0,99%** (imagem/GIF) | 13.053 |
| Vídeo | 2,96% | 0,53% | 30.684 |
| Link | 2,25% | 0,68% | 9.573 |
| Fio | não informado | **1,89%** | 27.508 |
| Carrossel | não informado | 0,72% | 12.335 |
| Enquete | não informado | 0,89% | 3.634 |

Amostras e métodos ([Buffer](https://buffer.com/resources/state-of-social-media-engagement-2026/); [Ordinal](https://www.tryordinal.com/blog/twitter-analytics)):

- **Buffer, State of Social Engagement 2026:** mais de 52 milhões de posts, jan/2024–dez/2025; ER = interações ÷ seguidores.
- **Ordinal:** 87.528 posts, jan/2024–mai/2026; ER = (curtidas + RTs + replies + bookmarks) ÷ impressões. Não descreve como selecionou a amostra nem faz teste de significância, e em outro trecho dá 35.975 impressões médias para texto.

Para contas Premium, o Buffer viu texto perto de 0,9% de mediana, vídeo acima de 0,7%, imagem em 0,4–0,5% e link em 0,25–0,3%. Para contas comuns, o link chegou a mediana de 0% a partir de mar/2025 ([Buffer, 02/10/2025](https://buffer.com/resources/x-premium-review/)).

**A pesquisa revisada é mais firme sobre imagem do que sobre vídeo.** Com correção de viés de seleção, a "mera presença" de imagem aumenta o engajamento no Twitter, e fotos profissionais e de alta qualidade ajudam [estudo, revisado] ([Li & Xie, Journal of Marketing Research 2020](https://doi.org/10.1177/0022243719881113)). Em 656.992 tweets de #SciComm, tweets com imagem tiveram em média 4,4 retweets contra 0,7 dos de texto puro [estudo, observacional] ([Mondal et al., 2023](https://www.explorationpub.com/Journals/edht/Article/10115)). Não há estudo revisado de 2024–2026 sobre vídeo nativo contra imagem no X.

**Para vídeo mudo, a melhor evidência é do próprio X, e é antiga e feita para anúncio.** Um estudo com a Omnicom e a Neuro-Insight (127 participantes, set/2016) concluiu três coisas [declaração oficial com estudo próprio] ([marketing.x.com, 06/06/2017](https://marketing.x.com/en/insights/how-to-create-video-with-thumb-stopping-power-on-twitter)):

- vídeos de até 15 s geram mais codificação de memória que os de 30 s;
- os 3 primeiros segundos "doesn't need audio";
- vídeos com texto são 11% mais vistos e têm conclusão 28% maior.

As boas práticas atuais de anúncio repetem esse caminho: "under 15 seconds", movimento logo no início, legenda para quem assiste sem som ([business.x.com](https://business.x.com/en/advertising/creative-best-practices)).

**Para fio e link, o código e as declarações bastam.** O fio, para o algoritmo, é o post raiz: o resto não sai da rede e a conversa ocupa uma vaga [código]. Sobre links, Bier afirmou em 06/04/2026 que "Links are not deboosted. We fixed that issue last year", e em 12/04/2026 orientou: "Just post the link in the body of the post and provide sufficient context about what the user will see before they click it" [declaração oficial] ([post de 06/04](https://x.com/nikitabier/status/2040968250604102105); [post de 12/04](https://x.com/nikitabier/status/2043428612108644848)). Os dados de link na lanterna do Buffer são de antes dessa correção, e não há estudo pós-correção.

As specs oficiais definem o que aparece inteiro. Uma imagem única com proporção entre **2:1 e 3:4** aparece completa na timeline, o que inclui 16:9, 1:1 e 4:5, e "what you see in the Post composer is what you'll get" ([help.x.com, fotos](https://help.x.com/en/using-x/posting-gifs-and-pictures)). As grades de várias imagens não têm recorte documentado. As fontes oficiais de vídeo conflitam ([help.x.com, vídeos](https://help.x.com/en/using-x/x-videos); [docs.x.com](https://docs.x.com/x-api/media/quickstart/best-practices)):

| Limite | Central de ajuda | API |
|---|---|---|
| Duração e tamanho para conta comum | 140 s e 512 MB | 20 min e 8 GB |
| Taxa de quadros | 40 fps (upload web) | até 60 fps |
| Resolução | até 1920×1200 | 1280×1024 |

O alt text vai por imagem, com até 1.000 caracteres, e não existe para vídeo. Ele não aparece nos scorers de ranking. O único A/B público, sem teste de significância, deu cerca de +5% de impressões e +15% de engajamentos [estudo, relato com método] ([Accessible Social](https://accessible-social.com/images-and-visuals/a-b-test)).

## Para a @ottodoti, três originais por dia, cada um com janela própria

**O código diz como espaçar.** Três posts por dia é uma cadência compatível com o código, desde que cada um tenha a própria janela de exploração e se sustente sozinho [inferência]. Com 3 h ou mais entre originais, cada post disputa a vaga de cold start sem concorrer com o anterior, e chega sozinho para quem abre o app várias vezes. Para quem abre pouco, os posts das últimas 48 h disputam o mesmo lote. Nesse caso, o terceiro post da marca precisa de score previsto 2,3× maior que o de uma conta seguida para empatar, se o leitor segue a marca, e cerca de 3× maior se não segue. Isso tem duas consequências: nada de "parte 1, 2, 3" espalhada pelo dia, e nenhum post de enchimento.

**A grade abaixo é hipótese de partida, não resultado medido.** Ela combina as janelas do Buffer e do Sprout, evita a noite e usa como formato principal o que os dados mostram de melhor por impressão. Deve ser revalidada pelos dados da própria conta depois de umas quatro semanas.

| Horário inicial (BRT, dias úteis) | Formato principal | Função | Base |
|---|---|---|---|
| ~09h30 | texto com dado ou mecanismo, às vezes fio de raiz forte (1× por semana) | autoridade e reply | texto tem as maiores impressões médias (Ordinal); o fio vale pelo raiz (código) |
| ~13h00 | card estático 4:5 (1080×1350): dado, diagrama, antes e depois de um post | parar o scroll, fazer mandar a alguém | imagem lidera o ER por impressão (Ordinal); presença de imagem ajuda (Li & Xie) |
| ~16h30 | vídeo mudo de 11–15 s com legenda queimada, mostrando o produto em movimento; nos dias sem vídeo, card ou texto | demonstrar o mecanismo | ≤15 s e texto na tela (estudo do X de 2016); vídeo não tem bônus (código) |

**O conteúdo deve ser feito para provocar as ações de maior peso que o leitor faz por conta própria** [inferência]. São elas: responder (pergunta específica, posição defensável), citar (dado novo que alguém quer comentar) e mandar a alguém por DM ou link copiado (checklist, referência, comparação). Bookmark não pontua, então "salve este post" é um CTA mais fraco que "manda para quem...". Pelo lado negativo, provocação que rende reply mas também mute tende a sair no prejuízo.

**Construir em público, nessa conta, é mostrar o processo do próprio produto** [inferência apoiada em estudo]:

- como um post da grade foi escrito com o Otto;
- que decisão de produto foi tomada e por quê;
- o erro da semana e o que mudou;
- métricas reais da @ottodoti com data, uma vez por semana.

A ordem é sempre resultado antes de intenção. Receita, só verificável. Um ângulo natural para uma ferramenta de IA de conteúdo é o próprio Otto lendo o JSON do Under the Hood e o repositório, como o VP de produto do X sugeriu fazer com uma IA. Para a conta pessoal de quem fundou o produto, a tática que sai do código é **citar a @ottodoti com uma linha própria em vez de repostar**. O quote vira post original do fundador, pode ir para fora da rede e disputa a vaga de cold start dele, se ele tiver até 50 mil seguidores. O repost ficaria preso aos seguidores dele, com ×0,75.

**Respostas.** A rotina diária de respostas deve ser escrita por gente, específica, com dado, e focada em conversas de contas médias do nicho de criadores e IA em português [inferência]. Uma marca de IA que automatiza replies corre um risco duplo: o `grox` registra `is_pasted` e `composition_source`, e reply com nota 0 vira `RiskyHighVizReply`. Nas primeiras 2 h de cada post, alguém do time responde as replies. Seguir de volta, com critério, quem interage de verdade no nicho cria mútuos, e faz as respostas deles aos originais da marca valerem 20 em vez de 5.

**O que evitar** [código / declaração oficial]:

- **Pods e grupos de WhatsApp pedindo curtida.** Navegar direto ao post "has no ranking impact".
- **Repostar vídeo alheio.** Agregação virou alvo explícito.
- **Recomendar Comunidades.** Foram extintas.
- **Quote ou reply a contas da lista eleitoral do TSE.** O post sai do "Para você" de quem não segue a conta listada.
- **Tom hostil a um "grupo rival".** O mesmo efeito de +67% em compartilhamento é o que gera "não tenho interesse" e mute.

**Visual.** O sistema visual deve servir à leitura no celular, que o X diz ser o meio de 80% do público ([business.x.com](https://business.x.com/en/advertising/creative-best-practices)). Na prática:

- 4:5 ou 16:9 para imagem e nunca 9:16, que fica fora da faixa 2:1–3:4 e é recortado;
- quadro 0 do vídeo desenhado como capa, porque o X não documenta capa personalizada para vídeo orgânico;
- legenda queimada, porque "not all videos will have captions";
- texto com contraste mínimo de 4,5:1 ([WCAG 2.2](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html));
- alt text em toda imagem, pela acessibilidade, não pelo alcance.

Para fugir da "cara de IA", vale o que a Anthropic descreve: os modelos convergem para Inter, Roboto e gradiente roxo sobre branco, e a saída é uma fonte com personalidade usada com decisão [declaração, blog técnico] ([Claude blog, 12/11/2025](https://www.claude.com/blog/improving-frontend-design-through-skills)).

**DPP e template fixo.** Como os semantic IDs vêm de um embedding multimodal e o DPP rebaixa posts parecidos na mesma página, um template idêntico todo dia pode aproximar os posts da marca entre si [inferência de baixa confiança]. O mais seguro é manter a marca constante e variar composição, ângulo e assunto.

**Premium ou verificação.** O código não mostra multiplicador de ranking por Premium. Os ganhos documentados são prioridade nas respostas, posts longos e Articles, analytics completo e elegibilidade ao Original Content Rewards. Os dados do Buffer mostram cerca de 10× mais alcance mediano para Premium (perto de 600 contra menos de 100 impressões por post), mas é correlação [estudo, dados de ferramenta] ([Buffer, 02/10/2025](https://buffer.com/resources/x-premium-review/)). Para uma marca cuja estratégia passa por respostas, o Premium ou a verificação de organização é custo operacional, não alavanca de algoritmo, e não deve ser vendido em post como "boost".

**Idioma.** Escrever sempre em português do Brasil é coerente com um modelo que recebe idioma e país do leitor e hidrata o idioma de cada candidato [inferência; não há medição do efeito].

## Mitos para nunca repetir e números para rechecar antes de cada post

### Mitos que não devem aparecer em nenhum post da marca

| Mito que circula | O que a evidência diz | Etiqueta e fonte |
|---|---|---|
| "1 reply vale 27 curtidas" ou "10 respostas valem mais que 100 likes" | Conta feita com a tabela de 2023 (13,5 ÷ 0,5). Pesos multiplicam probabilidades previstas, e o próprio X diz que não são câmbio. | [código 2023](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md); [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L291-L319) |
| "Se o autor responde, a reply vale 75× (ou 150 likes)" | `reply_engaged_by_author = 75` é de 05/04/2023 e não existe no value model de 2026 | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/weights.rs) |
| "1 denúncia cancela 468 curtidas" | O código chama essa leitura de incorreta, e o 468 usava curtir = 0,5 | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L291-L319) |
| "Clique no perfil pesa 12" | 2023; em 2026 o `ProfileClickWeight` é 0 | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L320-L438) |
| "Premium dá 4× (ou 2×) no ranking" | Era o default de 2023; o scorer sumiu em 2025 e não há termo em 2026. O documentado é prioridade nas respostas. | [código 2023](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/VerifiedAuthorScalingScorer.scala); [declaração oficial](https://help.x.com/en/using-x/x-premium) |
| "O X penaliza link" ou "link tira 30–90% do alcance" | Não há termo no código. Bier: "Links are not deboosted" (06/04/2026). Os percentuais não têm fonte primária. | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/vm_ranker_debias_payload.rs); [declaração oficial](https://x.com/nikitabier/status/2040968250604102105) |
| "Imagem e vídeo dão ×2, várias hashtags ×0,6" | Esses números estavam num bloco de 2023 com `applyBoosts = false` | [código 2023](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/util/earlybird/RelevanceSearchUtil.scala) |
| "O algoritmo ama vídeo" | VQV pesa 0, abrir vídeo 0,02, e o carrossel de vídeo está desligado | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L1053-L1082) |
| "Bookmark é o novo superlike" | Só rótulo de treino, sem peso no value model | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/phoenix_scores.rs) |
| "Postar mais de N vezes por dia derruba a conta" (ou "20 por dia é obrigatório") | Existe desconto por lote (0,625, 0,4375…), não punição à conta, e não há estudo causal de frequência | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L183-L204) |
| "Repostar o próprio post reinicia o relógio" | O repost só chega a seguidores, leva ×0,75, é deduplicado e some para quem viu. Qual ID o `AgeFilter` usa para repost não está confirmado. | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/age_filter.rs) |
| "Grupo de engajamento ajuda" | "Directly navigating to a post… has no ranking impact" | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L307-L319) |
| "Entre em Comunidades para crescer" | Extintas em 30/05/2026 | [declaração oficial](https://www.engadget.com/social-media/x-is-shutting-down-its-communities-feature-182843958.html) |
| "A vaga de conta pequena garante a 16ª posição" (ou "1 vaga por feed") | É o score-alvo da 16ª posição, 1 por carregamento, aplicado antes do ×0,75 e do DPP, e só para original ou quote | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs) |
| "O Grok lê tudo e não há mais heurísticas" | Filtros, decaimentos e multiplicadores seguem explícitos. O Grok aparece na nota de replies e em rótulos. | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md); [declaração oficial](https://x.com/elonmusk/status/1979217645854511402) |
| "O Grok só avalia replies em contas acima de 250 mil" | Abaixo disso, a Gemma 4 26B avalia; reply com quote vai ao Grok | [código](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/classifier_simple_reply_scorer.py) |
| "Fora da rede, só aparece com prova social de 2º grau" ou "seguir muita gente derruba a reputação" | Heurísticas de 2023 que não aparecem entre os filtros nem na fórmula de reputação de 2026 lidos | [código 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm) |
| "Existe um melhor horário universal" | Buffer e Sprout divergem; a pesquisa recomenda horário personalizado | [estudo](https://doi.org/10.1145/2783258.2788584) |
| "Anunciar a meta em público faz você cumprir" | Para metas de identidade, o efeito medido foi o contrário | [estudo](https://www.socmot.uni-konstanz.de/node/131) |
| "Print de Stripe é prova" ou "prova social sempre funciona" | Prints são forjáveis (daí o TrustMRR), e o experimento das toalhas não replicou | [relato](https://indieradar.app/blog/fake-mrr-pandemic-real-benchmarks); [estudo](https://pmc.ncbi.nlm.nih.gov/articles/PMC4118982) |

### Números que mudam e precisam ser rechecados antes de cada post

| Item | Valor em 14/10/2026 | Como mudou | Onde rechecar |
|---|---|---|---|
| Curtir | 0,66 | 0,5 → 0,6 (commit de 13/10) → 0,66 (commit de 14/10, sync de 13/10) | `home-mixer/params/param.rs`, L320, e `git log -p` |
| Não tenho interesse | −52,272 | −43,2 → −47,52 (29/09) → −52,272 (14/10), sempre ×1,1 | mesmo arquivo, L414–L419 |
| Abrir vídeo | 0,02 | 0,05 → 0,07 (25/08) → 0,02 (13/10) | mesmo arquivo |
| Clique e tempo após o clique | 0,3 e 0,4 | 0,4 → 0,3 e 0 → 0,4 (29/09) | mesmo arquivo |
| Dwell e VQV | dwell 0,05, contínuo 0,006, VQV 0 | VQV 0,05 → 0 e dwell 0 → 0,05 (25/08); contínuo 0,004 → 0,006 (13/10) | mesmo arquivo |
| Boost de reply entre mútuos | +15 (total 20) | +20 em 13/07, +15 em 24/07, com braços de experimento em 0, 5, 10 e 15 | param.rs, L322–L333, e `docs/BIDIRECTIONAL_BOOST_CHANGE.md` |
| Vaga de cold start | 200 views, 50 mil seguidores, 2 h, 97%, Thompson ligado | até 30/09: 1.000, 1.000, 48 h, 85%, Thompson desligado | param.rs, L489–L562 |
| Diversidade de autor e fora da rede | 0,5/0,25 e ×0,75 | confirmados no espelho de produção só até 22/09; desde 24/09 em arquivo sem marca de espelho | `vm-ranker/params.rs` e o cabeçalho de `param.rs` |
| Replies de fora da rede | desligadas | flag criada em 03/10 e "root only" em 13/10; se ligar, a reply passa a alcançar não seguidores | param.rs, L73–L84 |
| Carrossel de vídeo, payload com `has_url`, filtros de holdout | todos desligados | podem ser ligados em experimento | param.rs |
| Lista do filtro eleitoral | atualizada em 13/10/2026 | muda com o TSE | README e `brazil_2026_election_filter.rs` |
| Specs de vídeo | central: 140 s, 512 MB, 40 fps; API: 20 min, 8 GB, 60 fps | as fontes oficiais divergem | help.x.com e docs.x.com |
| Declarações de produto | Bier anunciou a saída em 05/08/2026; a Wikipedia dá o fim do mandato em 02/10/2026 | falas dele podem não refletir a gestão atual | [post](https://x.com/nikitabier/status/2085105586966827343); [Wikipedia](https://en.wikipedia.org/wiki/Nikita_Bier) |
| Programas e superfícies | OCR (07/08/2026), Under the Hood (piloto), Custom Timelines, Starterpacks | todos novos e em rollout | help.x.com e README |

Para qualquer post que cite um número do algoritmo, a checagem é fixa:

1. **Abrir o `param.rs` no `main`** e ler o "last sync" do cabeçalho.
2. **Conferir no `git log -p`** se o parâmetro mudou desde a última vez.
3. **Escrever a data no próprio post** ("pesos de 13/out/2026").
4. **Marcar a ressalva de diversidade e ×0,75**: para esses valores, escrever "confirmado em produção até 22/09/2026".
5. **Nunca usar número de 2023 sem "em 2023"** ao lado.
6. **Conferir o texto final do Otto** contra o briefing, para garantir que números e datas não foram alterados.


## Conclusão

O código de 2026 transformou a descoberta de contas pequenas num experimento explícito. Cada post original de uma conta com até 50 mil seguidores ganha duas horas e duzentas views na Home para provar, por curtidas ÷ views, que merece ser mostrado a quem não segue. Isso muda a unidade de planejamento: em vez de "quantos posts por dia", a pergunta é "quantas janelas de duas horas boas por dia". Também explica por que a terceira, quarta ou décima postagem do dia rende cada vez menos para o mesmo leitor. A ciência de difusão e os casos de build in public apontam na mesma direção. O resultado de um post é ruído, e o crescimento chega em rajadas, puxado por reciprocidade e por alguém maior que reverbera. A vantagem durável não é um truque de formato. É acumular mútuos reais no nicho e originais que as pessoas querem responder, citar e mandar a alguém.

Para uma marca que vende um copiloto de conteúdo com IA, a melhor prova de competência é a própria disciplina de método. Os pesos mudaram duas vezes em duas semanas, a imprensa ainda mistura 2023 com 2026, e os valores de diversidade e fora da rede não são verificáveis em produção desde 22/09. Num ambiente assim, citar o commit e a data, separar código de declaração e de relato, e mostrar como cada post foi feito já é conteúdo de build in public, sustentado pela evidência de que mostrar o processo aumenta o valor percebido. O que segue desconhecido define o que monitorar:

- como o retrieval de cold start escolhe os posts;
- o que os prompts do Grox premiam numa reply;
- se as replies de fora da rede serão ligadas, o que mudaria a estratégia de respostas da noite para o dia.
