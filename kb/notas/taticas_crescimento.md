# Táticas práticas de crescimento no X (2025–2026): playbook com nível de evidência

Legenda usada em TODOS os itens:
- **[A]** mecanismo visível no código aberto. Por padrão é o `xai-org/x-algorithm` (commit `17c96bf`, 14/10/2026; `param.rs` diz "last sync 2026-10-13T16:00:30Z"). Quando o item vier do código de 2023 (`twitter/the-algorithm` ou `the-algorithm-ml`), ele aparece como **[A-2023]**.
- **[B]** declaração oficial: central de ajuda, X Eng, Elon Musk, Nikita Bier ou outro funcionário do X. Os posts trazem a data UTC decodificada do ID (snowflake).
- **[C]** estudo de dados com amostra e método declarados.
- **[D]** relato de praticante ou de vendedor de ferramenta, sem método.

Avisos gerais:
- O README do repositório diz que os valores padrão em `param.rs` são sincronizados por cron com "os valores primários de produção", e que experimentos com cerca de 10% ou mais do tráfego devem aparecer no repositório ([README](https://github.com/xai-org/x-algorithm/blob/main/README.md#experiments-and-configuration)). Ou seja: os pesos mudam. Exemplo: em 13/10/2026 o peso de curtida estava em 0,66 e o de "não tenho interesse" em −52,272.
- Nikita Bier anunciou em 05/08/2026 que deixaria a chefia de produto ([post](https://x.com/nikitabier/status/2085105586966827343)). A Wikipedia dá o fim do mandato como 02/10/2026 ([Wikipedia](https://en.wikipedia.org/wiki/Nikita_Bier)). As falas dele de 2025–2026 continuam sendo [B], mas podem não refletir a gestão atual.

---

## 1. Repost vs. quote (citação) vs. reply: o que o código faz e quando usar cada um

### Takeaway
No código de 2026, o **repost é o formato mais fraco para distribuição**:
- só chega a quem já segue você;
- leva o multiplicador 0,75;
- é deduplicado contra o original e contra o que o leitor já viu;
- não concorre à vaga de conta pequena.

O **quote é um post original novo**: concorre à vaga de cold start, pode ir para fora da rede e pode ganhar o boost de mútuos. Ser citado também pesa muito (peso 5, igual a resposta). A reply tem as restrições da seção 2. Na prática: cite com opinião em vez de só repostar, e reserve o repost para dar sinal social a quem já segue você.

### Cited Findings

**Repost**
- [A] **Deduplicação de repost.** O `RetweetDeduplicationFilter` usa `retweeted_tweet_id` (ou o próprio ID) como chave. Quando o original e vários reposts do mesmo post chegam juntos, fica só o primeiro que aparece e o resto é removido. Os testes cobrem os três casos: vários reposts, original antes dos reposts e repost antes do original ([retweet_deduplication_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/retweet_deduplication_filter.rs)).
- [A] **No feed Seguindo, o original vence.** O `FollowingRetweetDeduplicationFilter` mantém todos os posts nativos e descarta o repost cujo ID ou cujo original já tenha sido visto ([following_retweet_deduplication_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/following_retweet_deduplication_filter.rs)).
- [A] **Fora da rede, repost não entra.** O `OONRetweetReplyFilter` remove do "Para você" todo repost de quem o leitor não segue (`in_network == false && is_retweet`) ([oon_retweet_reply_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/oon_retweet_reply_filter.rs)).
- [A] **Dentro da rede, repost e reply também levam 0,75.** O fator "fora da rede" (`OonWeightFactor = 0.75`) também vale para replies e reposts de quem o leitor segue, porque `EnableOonRescoreForInNetworkRepliesRetweets = true` ([vm-ranker/params.rs](https://github.com/xai-org/x-algorithm/blob/main/vm-ranker/params.rs); a função `oon_applies` está em [xai-value-model/scoring.rs](https://github.com/xai-org/x-algorithm/blob/main/xai-value-model/scoring.rs)).
- [A] **Quem já viu o original não vê o repost.** O `PreviouslySeenPostsFilter` remove o candidato quando o leitor já viu qualquer ID ligado a ele: o próprio post, o `retweeted_tweet_id` ou o `in_reply_to_tweet_id`. O ID citado (`quoted_tweet_id`) não está nessa lista ([previously_seen_posts_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/previously_seen_posts_filter.rs); `related_post_ids_iter` em [candidates_util.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/util/candidates_util.rs)).
- [A] **Repost não concorre à vaga de conta pequena.** A elegibilidade do cold start exige `in_reply_to_tweet_id.is_none() && retweeted_tweet_id.is_none()` ([author_cold_start.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/scorers/author_cold_start.rs), função `cold_start_base_eligible`).
- [A] **Boost de mútuos só para original.** O boost de resposta entre mútuos (+15) só se aplica a quem `!is_reply && !is_retweet && is_mutual_follow_author` ([xai-value-model/inputs.rs](https://github.com/xai-org/x-algorithm/blob/main/xai-value-model/inputs.rs)).
- [A] **O limite de 48 h olha a data do repost.** O `AgeFilter` usa a data do `tweet_id` do candidato, e no repost esse ID é o do próprio repost (os testes do filtro de deduplicação usam `tweet_id=1` com `retweeted_tweet_id=100`). O teto é `MAX_POST_AGE = 48 * 60 * 60` ([age_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/age_filter.rs), [config.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/config.rs)). Por isso um repost de hoje de um post seu antigo passa no filtro de idade, mas continua limitado aos seguidores, ao 0,75 e ao filtro de "já visto".

**Quote**
- [A] **Pesos da ação de citar.** `QuoteWeight = 5.0`, o mesmo da resposta (`ReplyWeight = 5.0`) e muito acima de repostar (`RetweetWeight = 1.0`) e curtir (`FavoriteWeight = 0.66`). Também há `QuotedClickWeight = 0.05` e `QuotedVqvWeight = 0.0` ([param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)). Os pesos multiplicam a probabilidade prevista de o leitor citar, curtir etc., e não a contagem.
- [A] **Contra o mito "1 denúncia = 468 curtidas".** O próprio X avisa que os pesos não podem ser lidos como equivalência de contagens, e que a probabilidade base de uma denúncia é "mais de 1000x menor" que a de uma curtida. Ações só contam quando acontecem num post servido na Home; chegar ao post por link direto, por exemplo combinado em grupo, "não tem impacto no ranking" ([comentários em param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs); nota de 14/08/2026 no [README](https://github.com/xai-org/x-algorithm/blob/main/README.md#august-14th-2026)).
- [A] **O quote é um post novo e não herda o "já visto".** Ele não é reply nem repost, então passa no `OONRetweetReplyFilter`, concorre ao cold start e não é removido por quem já viu o post citado. Se o post citado for derrubado pelo filtro de visibilidade, o quote cai junto: o README diz que "any post whose ... quoted post ... was itself dropped" também é removido ([README, Labeling Path](https://github.com/xai-org/x-algorithm/blob/main/README.md#labeling-path)).

**Referência de 2023**
- [A-2023] Na tabela de 05/04/2023: curtir 0,5, repostar 1,0, responder 13,5, `good_profile_click` 12,0, `good_click` 11,0, `good_click_v2` 10,0, `reply_engaged_by_author` 75,0, `negative_feedback_v2` −74,0, denunciar −369,0, `video_playback50` 0,005. Não havia peso separado para quote ([the-algorithm-ml README](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)).

**Declarações do X sobre reposts**
- [B] Em 11/04/2026, Bier anunciou que os pagamentos de todas as contas agregadoras caíram para 60% naquele ciclo, com mais 20% de corte no ciclo seguinte. A justificativa: "flooding the timeline with 100 stolen reposts and clickbait everyday crowded-out real creators and hurt new author growth" ([post](https://x.com/nikitabier/status/2043045929750794399); [TechCrunch, 12/04/2026](https://techcrunch.com/2026/04/12/x-says-its-reducing-payments-to-clickbait-accounts/)).
- [B] Em 23/05/2026, Bier disse que o X passou a identificar contas grandes que re-sobem conteúdo de contas menores, e que as impressões desses posts passam a ser atribuídas inteiramente ao criador original ([post](https://x.com/nikitabier/status/2058020001823793265)).

**Dados**
- [C] Metricool 2026: 1.123.528 posts de 15.116 contas no X. De 2024 para 2025, os reposts por post subiram 35% (4,93 → 6,67), as respostas 21% (2,10 → 2,56) e as curtidas 8% (30,25 → 32,89) ([Metricool, X stats 2026](https://metricool.com/x-twitter-statistics/)). Não encontrei estudo com amostra que compare o alcance de quote e de repost.

### Inferences
- **Tática "citar em vez de repostar"** [A]: para levar um post bom ao seu público e ao de fora, cite com uma linha de opinião ou um dado novo. O quote ganha:
  - a vaga de conta pequena, se você tem até 50 mil seguidores e o post tem menos de 2 h e menos de 200 views na Home;
  - a distribuição fora da rede;
  - o boost de mútuos;
  - a chance de aparecer para quem já viu o original.
- **Repost puro** [A]: serve como sinal social para os seus seguidores e quase nada além disso. Não expande alcance para fora da rede.
- **Repostar o próprio post antigo** [A]: tecnicamente volta ao feed dos seguidores por até 48 h a partir do repost, mas com 0,75 e sem a parcela que já viu (o filtro de "já visto" usa bloom filter; a janela de memória não é publicada).
  - Para reaproveitar um post antigo que performou, a inferência pelo código é **republicar como post original reescrito** ou **citar o próprio post com um gancho novo**. As duas formas concorrem ao cold start e à distribuição fora da rede.
  - Risco de política: repostar ou re-subir conteúdo alheio em massa foi alvo explícito de corte de pagamento [B].
- **Mito:** "repost vale 20x curtida" ou "repost é o sinal mais forte". No código de 2026, a ação de repostar tem peso 1,0, contra 5,0 de responder e citar e 20,0 de copiar link [A].
- **Mito:** contar pesos como se fossem contagens ("1 reply = 27 likes", "10 replies > 100 likes"). O README de 14/08/2026 desmente isso explicitamente [A].
- **Mito de 2023 que não vale em 2026:** o `reply_engaged_by_author = 75` não aparece no conjunto de pesos de 2026 [A-2023 vs A].

### Gaps
- Não achei a fala de Bier de que citar um post molda o seu "Para você" por 3 a 6 meses. Ela aparece só num resumo de busca de um artigo do BeInCrypto que retornou 403, e não foi verificada. Tratar como **não confirmada**.
- Não encontrei estudo com amostra (Buffer, Sprout etc.) comparando o alcance de quote, repost e post original em 2025–2026.
- A duração da memória do filtro de "já visto" não é publicada.

---

## 2. Respostas: responder os outros vs. responder no próprio fio, estratégia "reply guy" e como as respostas são ranqueadas (Grok, Premium)

### Takeaway
- **Gerar respostas no seu post é o que mais pesa**: peso 5, que sobe para 20 quando o post é original de um mútuo.
- **Suas respostas viajam pouco no "Para você"**:
  - nunca vão para fora da rede (padrão atual);
  - só aparecem para quem segue você **e** segue a pessoa respondida;
  - levam 0,75;
  - cada conversa ocupa uma vaga só;
  - somem para quem já viu o post-pai.

O valor de responder contas grandes está na **conversa do post grande**. Lá, acima de 250 mil seguidores, o **Grok dá nota a cada resposta**, e a central de ajuda diz que assinantes Premium têm prioridade nas respostas. A evidência de "reply guy" como motor de crescimento é só [D].

### Cited Findings

**Suas respostas como candidatas no "Para você"**
- [A] Respostas de quem o leitor não segue são removidas do "Para você" porque `EnablePhoenixOonReplies = false` e `PhoenixOonRepliesRootOnly = false` por padrão. Respostas sem ancestrais carregados também são removidas ([oon_retweet_reply_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/oon_retweet_reply_filter.rs); [param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)).
- [A] **`SelfReplyChainFilter`.** Uma resposta só fica no feed se o leitor segue o primeiro usuário da cadeia que não é o próprio autor, ou seja, quem foi efetivamente respondido. Respostas em cadeia do próprio autor no próprio fio passam ([self_reply_chain_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/self_reply_chain_filter.rs)).
- [A] **`DedupConversationFilter`.** Depois do ranking, fica só o post de maior nota por conversa (o ID da conversa é o menor ancestral). Um fio inteiro ocupa uma vaga por feed ([dedup_conversation_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/dedup_conversation_filter.rs)).
- [A] Respostas de quem você segue também levam o 0,75 ([scoring.rs](https://github.com/xai-org/x-algorithm/blob/main/xai-value-model/scoring.rs); [vm-ranker/params.rs](https://github.com/xai-org/x-algorithm/blob/main/vm-ranker/params.rs)).
- [A] Uma resposta some para o leitor que já viu o post respondido, porque `in_reply_to_tweet_id` está entre os IDs checados pelo filtro de "já visto" ([candidates_util.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/util/candidates_util.rs)).

**Respostas recebidas pelo seu post**
- [A] `ReplyWeight = 5.0` mais `BidirectionalFollowReplyWeightBoost = 15.0`, só para post original de autor mútuo, o que dá 20 no total ([param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs); `reply_weight_for` em [weights.rs](https://github.com/xai-org/x-algorithm/blob/main/xai-value-model/weights.rs)).
  - Linha do tempo: teste A/B começou em 10/07/2026 com valores 5/10/15/20; 20 para muitos usuários em 13/07; 15 em 24/07, depois de reclamações de que a Copa do Mundo sumiu do feed ([BIDIRECTIONAL_BOOST_CHANGE.md](https://github.com/xai-org/x-algorithm/blob/main/docs/BIDIRECTIONAL_BOOST_CHANGE.md)).
- [B] Bier, 13/07/2026: "We noticed this data was missing from the algo and it made your friends appear less in your replies". A mudança também deve "help clusters form around interests" ([post](https://x.com/nikitabier/status/2076747704248758617); [TechCrunch, 13/07/2026](https://techcrunch.com/2026/07/13/x-just-tweaked-its-algorithm-to-make-it-more-friendly-less-battleground/)).
- [B] Bier, 14/07/2026, listou métricas do teste: "Replies: +3.15% Original Posts: +1.8% Small Account Reach: +1.19% Time Spent: -0.13% Unregretted Time Spent: ∞" ([post](https://x.com/nikitabier/status/2076917480518558035)).

**Ranking das respostas na conversa (Grox)**
- [A] Respostas em conversas cujo post raiz ou post respondido tem **mais de 250.000 seguidores** (`GROK_GEMMA_FOLLOWER_SPLIT = 250_000`) entram no fluxo de *reply ranking* (`TaskReplyRankingFilter`).
  - Quem dá a nota é o **Grok** (`GROK_4_MINI_CRITICAL`, com fallback `GROK_4_1_FAST_HEDGEHOG_CRITICAL`). O histograma das notas usa a faixa 0–3.
  - Respostas do próprio autor do post raiz ou do post respondido são puladas.
  - Abaixo de 250 mil, a resposta passa por detecção de spam com Gemma; acima de 125 mil (`GEMMA_REPLY_SPAM_MIN_FOLLOWERS`) com um Gemma específico de spam em respostas. O filtro de spam coordenado usa o limite de 180.000.
  - Fontes: [task_filter.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/reply_spam/task_filter.py), [constants.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/reply_spam/constants.py), [classifier_reply_ranking.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/reply_spam/classifier_reply_ranking.py), [classifier_simple_reply_scorer.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/reply_spam/classifier_simple_reply_scorer.py).
- [A] Os prompts (.j2) do ranking de respostas **não foram publicados**: "prompts are excluded to reduce gameability of the system" ([prompts.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/reply_spam/prompts.py); seção "What's not in this repo?" do [README](https://github.com/xai-org/x-algorithm/blob/main/README.md#whats-not-in-this-repo)).
- [A] A tarefa que dá nota às respostas registra em log `is_pasted` (texto colado), `user_agent`, `composition_source`, `app_attestation_status`, `has_risky_user_safety_label` e `num_legit_blocks_received_last_24hrs` ([task_rank_replies.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/reply_spam/task_rank_replies.py)). O código mostra o registro; não mostra se esses campos entram na nota.

**Central de ajuda**
- [B] Página "Conversations recommendations": os sinais de ordenação incluem se o leitor segue o autor da resposta, se o autor original respondeu, o status de verificação e um ranqueamento por ML com base em curtidas e na relação leitor–autor. Respostas abusivas vão para uma seção separada ([help.x.com](https://help.x.com/en/resources/recommender-systems/conversations-recommendations)). A página deu 403 no fetch; o conteúdo veio do resumo do buscador.
- [B] Página "About X Premium": prioridade nas respostas em escala por plano (Basic < Premium < Premium+). O Premium+ tem "largest reply prioritization", sem números ([help.x.com/en/using-x/x-premium](https://help.x.com/en/using-x/x-premium)). Também lida via resumo do buscador por causa do Cloudflare.

**Dados**
- [C] Buffer, novembro de 2025: cerca de 2 milhões de posts de mais de 220 mil contas em 6 redes. Responder comentários no próprio post foi associado a +8% de engajamento no X, contra a base da própria conta. É o menor ganho entre as redes, atrás de Threads +42% e LinkedIn +30%. O Buffer diz que não estabelece causalidade ([Buffer](https://buffer.com/resources/replying-to-comments-boosts-engagement/)).
- [D] Guias comerciais de "reply guy" relatam saltos como "500 → 50 mil seguidores em 8 meses" com a "regra 70/30" (70% do tempo em respostas) e "800 → 15 mil em 4 meses". Recomendam mirar contas com 2–10x ou 5–20x os seus seguidores. Nenhum publica método, e a maioria vende ferramenta ou curso ([Teract](https://www.teract.ai/resources/twitter-reply-guy-strategy-2026), [Pounce](https://www.pounce.so/blog/reply-guy-tactics-that-actually-grow-your-account), [crítica em Tony Reviews Things](https://www.tonyreviewsthings.com/reply-guy-strategy-x-growth/)). Não consegui atribuir cada número a um site específico.

### Inferences
- **Tática 1: "post que pede resposta"** [A]. A ação mais valiosa ao seu alcance é aumentar a chance de o leitor responder: pergunta específica, posição defensável, lacuna a completar.
  - Copiar link (20) e compartilhar por DM (5) também pesam muito.
  - Com mútuos, a resposta vale 20 no post original, então **construir mútuos reais no nicho** (seguir de volta pares ativos) aumenta o peso das respostas que eles dão [A + B].
- **Tática 2: responder contas grandes, mas pela conversa** [A + B + D]. A resposta quase não leva você ao "Para você" de quem não te segue. O ganho vem de ser visto na conversa do post grande, onde o perfil é clicado e a pessoa segue. Acima de 250 mil seguidores, cada resposta recebe nota do Grok.
  - O critério do prompt é secreto, mas o filtro de spam e o registro de `is_pasted` sugerem evitar respostas genéricas, coladas ou automatizadas.
  - Premium tem prioridade declarada nas respostas [B].
- **Tática 3: responder no próprio post** [B + C]. A central diz que a resposta do autor original é sinal na conversa, e o Buffer mede +8%. Responder no próprio post é barato e tem efeito pequeno e positivo.
  - O peso de 2023 de "resposta engajada pelo autor = 75" não existe no código de 2026. **Mito:** "responder cada comentário multiplica 75x" [A-2023 vs A].
- **Tática 4: fio** [A]. As respostas do próprio fio não saem da rede e a conversa ocupa uma vaga só, então o post raiz carrega toda a distribuição. Ver a seção 6.
- **Escolha de alvo** [A + D, inferência]: em conta com mais de 250 mil seguidores sua resposta é julgada pelo Grok entre milhares. Em contas de 10 mil a 250 mil a disputa é menor e o filtro é de spam, não de qualidade. Os guias [D] sugerem mirar contas 2–20x maiores que a sua; isso é compatível, mas não está provado.

### Gaps
- Os critérios exatos da nota do Grok (prompt) e como a nota 0–3 entra na ordenação da conversa não são públicos.
- O peso numérico da prioridade Premium nas respostas não é publicado.
- Não há estudo com amostra que meça o crescimento de seguidores pela estratégia "reply guy" (só [D]).
- O serviço de ranking da conversa (aba de respostas) não está no repositório; o repositório cobre o "Para você".

---

## 3. Do zero: cold start, perfil, nicho, primeiros seguidores, Comunidades e prazos realistas

### Takeaway
O código de 2026 tem uma **vaga reservada para posts novos de contas pequenas**:
- 1 por carregamento de feed, na faixa da 16ª posição;
- vale para post original, de conta com até 50 mil seguidores, com até 2 h no ar e menos de 200 views na Home;
- a escolha é feita por um bandit que privilegia a razão curtidas ÷ views.

As **Comunidades do X foram extintas em 30/05/2026**. Hoje as alternativas são Custom Timelines, Starterpacks e grupos no XChat. Não há prova no código de que bio, cabeçalho ou post fixado mudem o ranking. Também não há estudo sério de prazos.

### Cited Findings

**A vaga de cold start**
- [A] Parâmetros: `EnableViewerColdStart = true`, `ColdStartSlotMin = 15`, `ColdStartSlotMax = 16`, `ColdStartFollowerCap = 50000`, `ColdStartMaxPostAgeSecs = 7200`, `ColdStartImpressionThreshold = 200`, `LowImpressionsMaxPositionRatio = 0.97`, `EnableColdStartThompsonSampling = true`, `ColdStartBetaAlpha0 = 0.75`, `ColdStartBetaBeta0 = 49.25`, `ColdStartTsTopK = 2` ([param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)).
- [A] Mecânica ([author_cold_start.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/scorers/author_cold_start.rs)):
  - a posição-alvo é sorteada em `[15,16)` do ranking, isto é, a 16ª posição;
  - elegível: post original (não reply, não repost), autor com até 50 mil seguidores, até 2 h de idade, menos de 200 `view_count_on_home`, e dentro dos 97% superiores das posições;
  - para cada elegível, o código sorteia uma amostra de Beta(0,75 + curtidas, 49,25 + views − curtidas), o que dá prior de 1,5% de curtidas por view;
  - entre os 2 maiores sorteios, vence o de maior nota do modelo;
  - há braços de experimento por leitor (holdout, controle e tratamento).
- [A] Os embeddings são por hash, então "um post novo é representável imediatamente" ([README, Key Design Decisions](https://github.com/xai-org/x-algorithm/blob/main/README.md#key-design-decisions)).
- [B] Bier, 14/07/2026: "Small Account Reach: +1.19%" no teste de mútuos ([post](https://x.com/nikitabier/status/2076917480518558035)).
- [B] Musk, 17/10/2025: a mudança para o Grok "should" ajudar contas pequenas a serem vistas, e o objetivo era "deletion of all heuristics within 4 to 6 weeks" ([post](https://x.com/elonmusk/status/1979217645854511402); [Social Media Today](https://www.socialmediatoday.com/news/x-formerly-twitter-switching-to-fully-ai-powered-grok-algorithm/803174/)). O código de out/2026 ainda tem várias heurísticas explícitas (filtros, decaimentos, vaga de cold start), então a promessa não se cumpriu ao pé da letra [A vs B].

**Nicho**
- [A] Os SimClusters continuam como fonte de posts de fora da rede. Usam o modelo `Model20m145k2020` com embeddings "InterestedIn" baseados em quem você segue e no que você curte (`FollowBasedUserInterestedIn`, `LogFavBasedUserInterestedInFromAPE`) ([EmbeddingStoreModule.scala](https://github.com/xai-org/x-algorithm/blob/main/simclusters/simclustersann/modules/EmbeddingStoreModule.scala); [README](https://github.com/xai-org/x-algorithm/blob/main/README.md)). O Phoenix prevê ações a partir do histórico de engajamento do leitor.
- [A] O Grox (Gemma) classifica posts com tração mínima em tópicos e marca qualidade (`isHighQuality`, `isSpam` etc.) no fluxo "banger initial screen" ([grox/flows/upa/models.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/upa/models.py); [constants.py](https://github.com/xai-org/x-algorithm/blob/main/grox/flows/upa/constants.py)). Em pedidos de timeline por tópico, o fator fora da rede é 0,5 (`TopicOonWeightFactor`) ([vm-ranker/params.rs](https://github.com/xai-org/x-algorithm/blob/main/vm-ranker/params.rs); [vm-ranker/scoring/value_model.rs](https://github.com/xai-org/x-algorithm/blob/main/vm-ranker/scoring/value_model.rs)).
- [A] O DPP (*determinantal point process*) de diversidade está ligado (`DppEnabled = true`, `DppTheta = 0.65`, `DppMaxSelectedRank = 150`) e usa similaridade de embeddings entre os candidatos ([vm-ranker/dpp.rs](https://github.com/xai-org/x-algorithm/blob/main/vm-ranker/dpp.rs); [vm-ranker/params.rs](https://github.com/xai-org/x-algorithm/blob/main/vm-ranker/params.rs)).

**Comunidades, Custom Timelines e Starterpacks**
- [B] **Comunidades:** Bier anunciou o fim em 23/04/2026. Elas eram usadas por "less than 0.4% of users" e geravam "80% of spam reports, financial scams, and malware on X". O desligamento total ficou para **30/05/2026**, depois de proposto para 06/05 ([post 1](https://x.com/nikitabier/status/2047180747690434994), [post 2](https://x.com/nikitabier/status/2047147126183137468); [Engadget, 23/04/2026](https://www.engadget.com/social-media/x-is-shutting-down-its-communities-feature-182843958.html)). A substituição proposta: links de grupo no XChat (até 350 membros, com plano de 1.000) ([post](https://x.com/nikitabier/status/2047041338106159484)) e Custom Timelines.
- [B] **Custom Timelines:** anunciadas em 21/04/2026. Fixam um tópico na Home, com mais de 75 tópicos, "powered by Grok" ([post](https://x.com/nikitabier/status/2046736181002645520)).
- [B] **Starterpacks:** anunciados em 21/01/2026. São listas dos "top posters in every niche & country", contas "big or small", para novos usuários ([post](https://x.com/nikitabier/status/2014079005025247240)).

**Expectativa de alcance para conta nova**
- [C] Buffer (18,8 milhões de posts, 71 mil contas, ago/2024–ago/2025, medianas): conta sem Premium tem **mediana abaixo de 100 impressões por post**. A mediana geral caiu de cerca de 1.000 para menos de 750 no período ([Buffer, 02/10/2025](https://buffer.com/resources/x-premium-review/)).

**Prazos e perfil**
- [D] Guias de praticantes prometem prazos como 0→10 mil seguidores em poucos meses, sem método publicado ([Teract](https://www.teract.ai/resources/grow-twitter-following-2026); [Postory](https://postory.io/blog/grow-on-x-after-communities-shutdown)).
- [A] Não há peso para clique no perfil no "Para você" (`ProfileClickWeight = 0.0`). Há peso para o leitor seguir o autor a partir do post (`FollowAuthorWeight = 4.0`) ([param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)). Não encontrei no código nenhum uso de bio, cabeçalho ou post fixado no ranking.

### Inferences
- **Tática "as primeiras 2 horas"** [A]. Cada post original tem uma janela de 2 h e menos de 200 views na Home para disputar a vaga de conta pequena. O critério do sorteio é curtidas ÷ views na Home.
  - Poste quando a sua base está online.
  - Abra o post com um gancho que gere curtida rápida.
  - Não "gaste" a janela com posts fracos.
- **Espaçar posts por pelo menos cerca de 2 h na fase do zero** [inferência de A]. A vaga é uma por carregamento e dois posts seus elegíveis ao mesmo tempo disputam a mesma vaga para o mesmo leitor. Espaçar dá a cada post uma janela própria.
- **Original > reply > repost para quem está começando** [A]. Só o post original concorre à vaga de cold start e à distribuição fora da rede.
- **Consistência de nicho** [A + inferência]. A recuperação fora da rede (SimClusters InterestedIn, Phoenix, tópicos do Grox) depende de quem engaja e do assunto. Manter um tema ajuda o post a cair nos clusters certos. Porém o DPP rebaixa posts parecidos demais no mesmo feed, então varie o ângulo e o formato dentro do nicho, sem repetir o mesmo post.
- **Primeiros seguidores** [A + B]: construir mútuos com pares do nicho (boost de 15 nas respostas aos seus originais), responder em conversas de contas médias e tentar entrar em Starterpacks do nicho e país (critério de seleção não publicado).
- **Perfil (bio, header, fixado)** [D, sem evidência A/B]: provavelmente afeta a conversão de visita em follow, que entra como probabilidade prevista de seguir (peso 4). Não há prova de efeito direto no ranking. Tratar como boa prática de conversão.
- **Mito / desatualizado:** "entre em Comunidades para crescer" ou "posts em Comunidades aparecem no Para você". As Comunidades foram extintas em 30/05/2026 [B]. **Qualquer conteúdo agendado que recomende Comunidades está desatualizado.**
- **Expectativa realista** [C]: conta nova e sem Premium começa em mediana abaixo de 100 impressões por post (Buffer). O crescimento depende de achar posts outliers e não da média.

### Gaps
- Não há estudo com amostra sobre prazos realistas de 0→1k ou 0→10k em 2025–2026.
- Os critérios de inclusão nos Starterpacks e nas Custom Timelines não foram publicados.
- O efeito de bio, header e post fixado não tem evidência A, B ou C.
- A comparação entre os braços de controle e tratamento do cold start não foi publicada (resultado do experimento).

---

## 4. Já tem ~100 posts: como auditar

### Takeaway
Com cerca de 100 posts, audite pela **mediana** e não pela média, porque a distribuição tem cauda longa. Olhe as métricas que espelham o que o modelo prevê: curtidas por view nas primeiras 2 h, respostas, citações, compartilhamentos e follows por mil impressões. Separe por formato, tema e horário. Lembre que um post com mais de 48 h não volta ao "Para você". Use também a ferramenta "Under the Hood" para checar rótulos que limitam visibilidade.

### Cited Findings
- [A] **Pesos atuais** que definem o que medir ([param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)):

  | Ação prevista | Peso |
  |---|---|
  | Curtir | 0,66 |
  | Responder | 5 (20 entre mútuos, só em post original) |
  | Repostar | 1 |
  | Citar | 5 |
  | Compartilhar | 2 |
  | Compartilhar por DM | 5 |
  | Copiar link | 20 |
  | Seguir o autor | 4 |
  | Clique | 0,3 |
  | Abrir link | 0,2 |
  | Expandir foto | 0,05 |
  | Abrir vídeo | 0,02 |
  | Dwell | 0,05 |
  | Tempo contínuo de dwell | 0,006 |
  | Dwell após clique | 0,4 |
  | Clique no perfil | 0 |
  | Não tenho interesse | −52,272 |
  | Silenciar | −58,8 |
  | Bloquear | −31,2 |
  | Denunciar | −234 |
  | Não se demorar | −0,02 |

- [A] **Bookmark não tem peso** no value model publicado. Ele aparece apenas como tipo de ação e de evento no proto (`P_BOOKMARK`, `CLIENT_TWEET_BOOKMARK`) ([recsys.proto](https://github.com/xai-org/x-algorithm/blob/main/phoenix/crates/serving/xai-recsys-proto/proto/recsys.proto); [weights.rs](https://github.com/xai-org/x-algorithm/blob/main/xai-value-model/weights.rs)).
- [A] O sorteio do cold start usa `fav_count` e `view_count_on_home` ([author_cold_start.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/scorers/author_cold_start.rs)). O corte de idade é 48 h (`MAX_POST_AGE`) ([config.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/config.rs)).
- [A/B] **Under the Hood**: ferramenta piloto (desde ago/2026) em [x.com/i/jf/under_the_hood](https://x.com/i/jf/under_the_hood). Mostra estatísticas dos rótulos que limitam visibilidade na conta e nos posts. Desde 18/09/2026 mostra também retenções por exigência legal, por país ([README](https://github.com/xai-org/x-algorithm/blob/main/README.md#under-the-hood-label-transparency-tool)).
- [B/C] **Analytics nativo**: o painel completo fica atrás do Premium (o Basic não inclui). Métricas citadas: impressões, engajamentos, taxa de engajamento, visitas ao perfil, novos seguidores, top posts e vídeo. Cliques em link reportadamente não aparecem ([Sociality](https://sociality.io/blog/twitter-analytics/); [PostEverywhere](https://posteverywhere.ai/blog/x-twitter-metrics-kpis); [Buffer](https://buffer.com/resources/best-time-to-post-on-twitter-x-x/)). Não consegui abrir a documentação oficial (Cloudflare).
- [C] **Mediana vs. média**: o Buffer reporta medianas. O estudo da Adilo (cerca de 3.200 posts, 2025) usa médias, e nele imagem lidera com 2,09% de engajamento médio "com a maior variabilidade" ([resumo da Adilo via busca](https://adilo.com/blog/?p=20988); [Buffer](https://buffer.com/resources/x-premium-review/)).
- [C] **Benchmark do Metricool 2026** (1,12 milhão de posts no X): média de 2.711 impressões e 42,7 interações por post em 2025, e cliques no perfil caindo 31% (8,29 → 5,68) ([Metricool](https://metricool.com/x-twitter-statistics/)). O público do Metricool tende a ser de marcas e contas que usam a ferramenta.
- [B] **Elegibilidade ao Original Content Rewards**: 500.000 impressões na Home vindas de usuários verificados em 90 dias, **sem contar replies**, e 500 seguidores verificados ([help.x.com, Original Content Rewards](https://help.x.com/en/using-x/original-content-rewards), via resumo do buscador). Para quem monetiza, a métrica de auditoria é "impressões na Home de verificados em posts originais".

### Inferences
**Roteiro de auditoria em 7 passos (para o post "já tem 100 posts? faça isso")** [inferência de A + C]:
1. Exporte os últimos 100 posts. Separe originais de replies e reposts: só os originais concorrem ao cold start e à distribuição fora da rede, e reply não conta para o OCR.
2. Calcule por post: impressões, curtidas ÷ impressões, respostas ÷ mil impressões, citações, compartilhamentos e follows ÷ mil impressões. Use **mediana e percentis (p50, p90)**, não média.
3. Marque o top 10% (os outliers) e procure o padrão: tema, formato (texto, imagem, vídeo, fio, link), tipo de gancho, horário, dia da semana.
4. Compare as primeiras 2 h dos outliers com as da mediana. A taxa de curtidas por view no começo é o critério da vaga de conta pequena.
5. Veja visitas ao perfil → follows. Clique no perfil tem peso 0 no ranking, mas o follow é o resultado que importa; uma conversão baixa sugere arrumar a bio e o fixado [D].
6. Abra o Under the Hood e confira se há rótulo limitando visibilidade (por exemplo spam ou NSFW) [A/B].
7. Dobre a aposta nos 2–3 padrões do top 10% e corte os formatos que ficam sempre abaixo da mediana.

**Mitos para esta seção:**
- "Bookmark é o novo superlike." Não há peso de bookmark no value model publicado [A]. Bookmarks podem influenciar o histórico do usuário, mas não são termo de ranking.
- "Clique no perfil pesa 12." Isso era o `good_profile_click` de 2023 [A-2023]. Em 2026 o `ProfileClickWeight` é 0 [A].

### Gaps
- Não consegui confirmar na documentação oficial a lista exata de métricas do X Analytics em 2026: se bookmarks, compartilhamentos e cliques em link aparecem por post.
- Não achei benchmark público de "100 posts" (mediana de impressões por faixa de seguidores) com amostra declarada além dos agregados do Buffer e do Metricool.

---

## 5. Cadência: posts por dia, espaçamento, decaimento por autor, horários e fim de semana

### Takeaway
Cada carregamento do "Para você" devolve **35 posts**. Dentro do conjunto de candidatos, o segundo post do mesmo autor vale 0,625x, o terceiro 0,44x e o quarto 0,34x, com piso de 0,25x. Postar em rajada desperdiça alcance, e Bier confirmou isso em maio de 2026. Os estudos de horário (Buffer e Sprout) concordam: dias úteis no meio da semana, manhã ou começo da tarde, fim de semana e noite mais fracos. Os horários estão em hora local, sem recorte para o Brasil.

### Cited Findings
- [A] **Decaimento por autor**: `AuthorDiversityDecay = 0.5`, `AuthorDiversityFloor = 0.25`, `EnableAuthorDiversity = true` ([vm-ranker/params.rs](https://github.com/xai-org/x-algorithm/blob/main/vm-ranker/params.rs)).
  - Fórmula: `(1 − piso) × decay^k + piso`, em que k é o número de posts do mesmo autor com nota maior no mesmo conjunto ([xai-value-model/scoring.rs](https://github.com/xai-org/x-algorithm/blob/main/xai-value-model/scoring.rs), `diversity_multiplier` e `author_pool_counts`).
  - Resultado: 1º post 1,0; 2º 0,625; 3º 0,4375; 4º 0,34375; daí em diante tendendo a 0,25.
- [A] **Tamanho do lote**: `RESULT_SIZE = 35`, `TOP_K_CANDIDATES_TO_SELECT = 50`, `MaxPostsToCache = 750`, "Quem seguir" na posição 6 e pesquisa no feed na posição 12 ([config.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/config.rs); [param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)).
- [B] Bier, cerca de 30/05/2026: o app puxa 35 posts por vez, e se um autor aparece várias vezes num lote, os posts extras vão para o lote seguinte. Ele disse que a solução não é ideal e que querem algo melhor contra contas grandes ocupando o topo ([X trending, 30/05/2026](https://x.com/i/trending/2060629176668094923), página resumida pelo X; o post original não foi localizado). O `RESULT_SIZE = 35` do código bate com a fala [A].
- [D] Criadores responderam à fala de Bier espaçando posts em 30–90 minutos, e alguns (como Grummz) criticaram o mecanismo como "deboost" de posts seguidos (mesma página de [X trending](https://x.com/i/trending/2060629176668094923), via resumo do buscador).
- [A] O DPP de diversidade também rebaixa conteúdo parecido entre si no mesmo feed ([vm-ranker/dpp.rs](https://github.com/xai-org/x-algorithm/blob/main/vm-ranker/dpp.rs)). Posts com mais de 48 h saem do "Para você" ([config.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/config.rs)).
- [A-2023/2025] O repositório antigo já tinha parâmetros de diversidade por autor (`AuthorDiversityDecayFactor`, `AuthorDiversityFloor`, versões dentro e fora da rede) e `OutOfNetworkScaleFactorParam = 0.75` ([ScoredTweetsParam.scala](https://github.com/twitter/the-algorithm/blob/main/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/param/ScoredTweetsParam.scala), versão do repositório atualizada em set/2025).
- [C] **Buffer** ("8,7 milhões de tweets", publicado em 13/03/2026): melhores horários terça 9h, quarta 10h e quarta 9h; a faixa mais confiável é 9h–11h em dias úteis; noite (18h–23h) é a pior faixa em todos os dias; sábado e sexta são os piores dias; horários normalizados para hora local. O artigo não diz se usa mediana ou média nem o período ([Buffer](https://buffer.com/resources/best-time-to-post-on-twitter-x-x/)). O título fala em "1 milhão de posts", em conflito com o corpo.
- [C] **Sprout Social** (atualizado em mar/2026): quase 2 bilhões de engajamentos entre 27/11/2025 e 27/02/2026, cerca de 307 mil perfis em 6 redes; recomenda terça a quinta, 12h–18h em hora local, e fim de semana mais fraco. O artigo não diz quantos perfis são do X ([Sprout Social](https://sproutsocial.com/insights/best-times-to-post-on-twitter/)).
- [C] **Metricool 2026**: a média de posts semanais no X subiu de 15,97 para 17,34 entre 2024 e 2025, cerca de 2,5 por dia, enquanto as impressões médias por post caíram 5% ([Metricool](https://metricool.com/x-twitter-statistics/)).
- [C] O Buffer recomenda postar diariamente ou várias vezes ao dia, sem número próprio que sustente a frequência ([Buffer](https://buffer.com/resources/best-time-to-post-on-twitter-x-x/)).

### Inferences
- **Regra de cadência** [inferência de A]. O 2º post do dia que concorre com o 1º no feed do mesmo leitor vale 0,625x e o 3º 0,44x. Três a cinco originais bons por dia rendem mais do que dez medianos. O decaimento é dentro do conjunto de candidatos de cada carregamento, então posts não vistos das últimas 48 h competem entre si para quem abre o app pouco.
- **Espaçamento** [A + B + D]. Espaçar ajuda principalmente quem atualiza o feed com frequência e, para contas pequenas, dá a cada post a própria janela de cold start de 2 h (seção 3). Uma regra prática coerente com o código: **pelo menos 2 h entre originais** para contas pequenas; os 30–90 min dos criadores são [D].
- **Horário** [C]: comece testando terça a quinta, das 9h às 11h e das 12h às 15h no fuso do público (BRT), e evite noite e fim de semana para posts importantes. Valide nos seus dados: são estudos de clientes das ferramentas, majoritariamente em inglês e de marcas.
- **Fim de semana** [C]: ambos os estudos apontam o fim de semana como mais fraco. Use para posts de teste ou leves.
- **Mito**: "postar 20x por dia é obrigatório para o algoritmo". O código penaliza a repetição do mesmo autor no mesmo lote [A]. Volume ajuda a achar outliers (a lógica do "hero diário"), mas cada post extra disputa espaço com os seus.

### Gaps
- Não achei dataset de horário específico para o público brasileiro ou em português.
- Não há estudo com amostra comparando 1, 3, 5 e 10 posts por dia no X em 2025–2026.
- O tempo que um leitor leva entre carregamentos (e por isso o efeito real do espaçamento) não é publicado.
- O post original de Bier sobre os lotes de 35 não foi recuperado; a fonte é a página de trending do X, com resumo gerado.

---

## 6. Formatos: fio vs. post único vs. post longo (Premium) vs. Artigos; imagem, vídeo, texto; links; enquetes

### Takeaway
O código não dá bônus de formato. Ele pontua ações previstas: dwell e clique pesam um pouco, abrir vídeo e expandir foto quase nada, e visualização qualificada de vídeo pesa 0.

**Fio:** para o algoritmo, o fio é o **post raiz**. As respostas dele não saem da rede e a conversa ocupa uma vaga.

**Links:** desde out/2025, a posição oficial é que **links não são penalizados**, e no código não há termo de penalidade. Mas os dados do Buffer (ago/2024–ago/2025) mostram link como o formato de pior mediana. **Texto puro** lidera nos dados do Buffer para contas Premium.

### Cited Findings

**Código**
- [A] Pesos por formato: `PhotoExpandWeight = 0.05`, `VideoOpenWeight = 0.02`, `VqvWeight = 0.0`, `DwellWeight = 0.05`, `ContDwellTimeWeight = 0.006`, `ContClickDwellTimeWeight = 0.4`, `ClickWeight = 0.3`, `OpenLinkWeight = 0.2`. O vídeo só conta como "qualified view" se tiver mais de 10 s (`MinVideoDurationMs = 10_000`), e mesmo assim o peso é 0 por padrão ([param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs); [candidates_util.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/util/candidates_util.rs)).
- [A] Há um módulo de carrossel de vídeo (`VIDEO_CAROUSEL_MIN_VIDEOS = 3`, `VIDEO_CAROUSEL_MAX_VIDEOS = 5`, `VIDEO_CAROUSEL_EXTRA_CANDIDATES = 30`), uma superfície à parte para vídeos ([config.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/config.rs)).
- [A] **Sem penalidade de link no ranking publicado.** O `has_url` (número de URLs externas no texto) existe só num pacote experimental de "debias" enviado ao reranker, junto com tamanho do texto, quebras de linha e vídeo. O envio está desligado: `VMRankerSendDebiasInputs = false` ([content_features.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/models/content_features.rs); [vm_ranker_debias_payload.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/scorers/vm_ranker_debias_payload.rs); [param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)).
- [A] **Fio:** as respostas do próprio fio passam no `SelfReplyChainFilter`, mas são removidas fora da rede (`OONRetweetReplyFilter`), levam 0,75 dentro da rede e são colapsadas para uma por conversa (`DedupConversationFilter`) ([filtros](https://github.com/xai-org/x-algorithm/tree/main/home-mixer/filters)).

**Declarações sobre links**
- [B] Out/2025: Bier anunciou o teste de uma nova experiência de link no iOS, que mantém o post visível enquanto a página abre, porque "the web browser covers the post and people forget to Like or Reply" ([Engadget](https://www.engadget.com/x-is-testing-a-new-way-of-opening-links-in-posts-to-improve-engagement-211210520.html); [Nieman Lab, out/2025](https://www.niemanlab.org/2025/10/x-makes-overtures-to-journalists-with-new-feature-designed-to-improve-reach-for-links/)).
- [B] 19/10/2025: Bier disse que o post "should stand on its own" mesmo sem o link e precisa de uma boa legenda ([post](https://x.com/nikitabier/status/1979994223224209709); paráfrase via [roboin](https://roboin.io/article/en/2026/04/13/x-denies-link-deboost-recommends-in-post-links/)).
- [B] 06/04/2026: "Links are not deboosted. We fixed that issue last year." ([post](https://x.com/nikitabier/status/2040968250604102105)).
- [B] 08/04/2026: "1. Links were never 'deboosted' 2. They received lower engagement because websites cover the very buttons that cause something to rank better in the algorithm. 3. Today, the buttons are no longer covered, so links now have the same shot…" ([post](https://x.com/nikitabier/status/2041911302541730237)).
- [B] 12/04/2026: Bier chamou de "Fake news" a alegação de penalidade e orientou: "Just post the link in the body of the post and provide sufficient context about what the user will see before they click it" ([post](https://x.com/nikitabier/status/2043428612108644848); [roboin, 13/04/2026](https://roboin.io/article/en/2026/04/13/x-denies-link-deboost-recommends-in-post-links/)).
- [B] Fim de jul/2026: Bier disse a Mark Zuckerberg que não precisava mais pôr links nas respostas, e Musk respondeu "We haven't for over a year" ([Free Press Journal, 29/07/2026](https://www.freepressjournal.in/tech/x-product-head-nikita-bier-confirms-link-penalty-removed-over-a-year-ago-tells-mark-zuckerberg-he-can-post-them-directly)).
- [D/B] Jay Baxter, do X, explicou que o alcance menor vinha de menos curtidas por view, e não de uma regra explícita ([post](https://x.com/jaybaxter/status/2040973743351324773)). Críticos como Nate Silver e Philippe Lemoine contestam o enquadramento ([resumo do buscador; posts no X](https://x.com/nikitabier/status/2040968250604102105)).

**Dados por formato**
- [C] **Buffer** (18,8 milhões de posts, ago/2024–ago/2025, medianas de engajamento):
  - Premium: texto perto de 0,9% em meados de 2025, vídeo acima de 0,7%, imagem 0,4–0,5%, link 0,25–0,3%;
  - contas comuns: texto cerca de 0,25% e imagem cerca de 0,2%; link com mediana de 0% a partir de mar/2025.
  - O estudo é descritivo e não causal ([Buffer, 02/10/2025](https://buffer.com/resources/x-premium-review/)).
- [C, verificação pendente] Relatório do Buffer "State of Social Media Engagement 2026" (dados de 2025, mais de 52 milhões de posts): no X, texto 3,56% contra imagens 3,40%, e uma divisão crescente entre Premium e contas comuns. Visto só via resumo do buscador ([Social Media Today](https://www.socialmediatoday.com/news/instagram-linkedin-and-threads-engagement-declined-in-2025/814141/)).
- [C, baixa confiança] Números atribuídos ao Socialinsider 2026, que circulam só em agregadores (não achei o relatório original): mediana de engajamento por impressão de cerca de 0,12%; texto 0,011% contra vídeo nativo 0,043%. Os agregadores divergem muito entre si ([hypefy](https://hypefy.ai/blog/what-is-engagement-rate); [amraandelma](https://www.amraandelma.com/best-x-engagement-rate-statistics/)).
- [C, amostra pequena] Adilo 2025 (cerca de 3.200 posts, médias): imagem com 2,09% de engajamento médio, acima de vídeo e de anúncios ([Adilo](https://adilo.com/blog/?p=20988), via resumo).

**Fios vs. posts longos**
- [D] Hootsuite testou 3 fios contra a própria média de 150–200 impressões por post e obteve 8.155, 247 e 2.381 impressões ([Hootsuite](https://blog.hootsuite.com/experiment-x-threads-vs-longform-posts/), via resumo; a página deu 403).
- [D] Buffer testou 10 fios contra tweets com link, num experimento antigo de amostra mínima ([Buffer](https://buffer.com/resources/twitter-thread-experiment/)).
- [D] A OpenTweet diz que fios de 4–7 tweets têm cerca de 35% mais engajamento por tweet do que posts únicos, sem metodologia publicada ([OpenTweet](https://opentweet.io/blog/best-time-to-post-on-twitter-data-study)).

**Artigos**
- [B] X Articles abertos a assinantes Premium em jan/2026 ([PiunikaWeb, 07/01/2026](https://piunikaweb.com/2026/01/07/x-articles-premium-nikita-bier-updates/)). Não encontrei dado de alcance de Artigos.

### Inferences
- **Fio** [A]: escreva o fio pelo post raiz. A distribuição fora da rede é só dele, e o resto do fio aumenta dwell e cliques na conversa (clique 0,3, dwell após clique 0,4). Um post longo do Premium coloca todo o conteúdo no raiz e captura dwell nele.
  - **Inferência**: para alcance, um post longo ou um raiz forte com fio curto tende a ser melhor do que um fio de 15 partes com raiz fraco. Os dados C são inconclusivos.
- **Link** [A + B + C]: o código atual não penaliza, e o X diz que o problema (a página cobrindo os botões) foi corrigido entre o fim de 2025 e o começo de 2026. Os dados do Buffer que mostram link na lanterna são de antes ou da época da correção.
  - Tática segundo Bier: link no corpo, com contexto claro do que a pessoa vai ver, e o post de pé sozinho.
  - Na prática: o link tira gente do app e a abertura de link pesa só 0,2, então ainda compensa que o post gere curtida, resposta ou compartilhamento antes do clique.
- **Mito**: "link tira 50–90% do alcance". Esses números de blogs não têm fonte primária, e o código de 2026 não tem esse termo [A + B].
- **Vídeo** [A + C]: não há bônus fixo para vídeo (peso de visualização qualificada 0), mas existe o carrossel de vídeos como superfície extra, e o dwell conta. Use vídeo quando ele segura a atenção, não porque "o algoritmo ama vídeo".
- **Texto puro** [C]: foi o melhor formato em mediana de engajamento para Premium no Buffer, o que combina com o X ser lido como rede de texto. Bom formato padrão para posts diários.
- **Enquetes** e **Artigos**: sem evidência de alcance. Ver Gaps.

### Gaps
- Não encontrei estudo de 2025–2026 com amostra sobre enquetes no X, nem peso para voto em enquete na lista de ações do value model publicado.
- Não há dados de alcance de X Articles nem de posts longos do Premium versus fio.
- Falta estudo de links pós-correção (2026) que compare a mediana de posts com e sem link.
- O relatório original do Socialinsider 2026 e o "State of Social Media Engagement 2026" do Buffer não foram lidos diretamente.

---

## 7. Mudanças oficiais 2025–2026 e o que mudam na estratégia

### Takeaway
A sequência relevante:
1. Grok passa a ranquear o feed (out/2025 a jan/2026).
2. Código aberto em 19–20/01/2026.
3. Links "não penalizados" (out/2025 a jul/2026).
4. Corte para agregadores e reposts roubados (abr/2026).
5. Fim das Comunidades (maio/2026).
6. Lotes de 35 com diversidade por autor (maio/2026).
7. Boost de mútuos (jul/2026).
8. Filtro eleitoral do Brasil (ago/2026).
9. **Fim do Revenue Sharing e criação do Original Content Rewards** (ago a set/2026), que paga só por impressões de **posts originais** vistas por **usuários Premium** na Home, sem contar replies.

Tudo empurra para **conteúdo original e conversa entre mútuos**, e contra agregação, isca e repost.

### Cited Findings
- [B] **Musk, 17/10/2025**: "We are aiming for deletion of all heuristics within 4 to 6 weeks. Grok will literally read every post and watch every video (100M+ per day)…" ([post](https://x.com/elonmusk/status/1979217645854511402)).
- [B/C] **Nov/2025**: o feed Seguindo também passou a ser ordenado pelo Grok, com opção cronológica mantida ([Social Media Today](https://www.socialmediatoday.com/news/x-formerly-twitter-sorts-following-feed-algorithm-ai-grok/806617/)).
- [A] **Código aberto**: o repositório `xai-org/x-algorithm` foi criado em 19/01/2026 (API do GitHub, `created_at`) e recebe commits quase diários até 14/10/2026 ([GitHub](https://github.com/xai-org/x-algorithm)). O X Eng o descreveu como "powered by the same transformer architecture as xAI's Grok model" ([Decrypt](https://decrypt.co/355108/elon-musks-x-open-sources-grok-powered-algorithm-driving-for-you-feed)).
- [A] **Notas do README**:
  - 13/08/2026: o repositório passou a incluir pesos, filtros de visibilidade, código de treino do Phoenix e SimClusters.
  - 14/08/2026: explicação dos pesos e o `Brazil2026ElectionFilter`, que remove posts de contas denunciadas ao TSE, a menos que o leitor siga a conta (lista atualizada em 13/10/2026).
  - 18/09/2026: o Under the Hood passou a mostrar retenções legais.
  - Fontes: [README](https://github.com/xai-org/x-algorithm/blob/main/README.md); [brazil_2026_election_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/brazil_2026_election_filter.rs); anúncio da [@XBR, 14/08/2026](https://x.com/XBR/status/2088341967864320507).
- [B] **Links**: falas de out/2025, abr/2026 e jul/2026 (detalhes na seção 6).
- [B] **Agregadores**: cortes de pagamento em abr/2026 e realocação de impressões de re-uploads em maio/2026 (detalhes na seção 1).
- [B] **Comunidades** extintas em 30/05/2026; **Custom Timelines** (abr/2026); **Starterpacks** (jan/2026) (detalhes na seção 3).
- [B] **Diversidade por autor em lotes de 35**, ~30/05/2026 (detalhes na seção 5).
- [B] **Mútuos**, 13/07/2026, com métricas de 14/07/2026 incluindo "Unregretted Time Spent: ∞" ([post](https://x.com/nikitabier/status/2076917480518558035)).
- [B] **Original Content Rewards (OCR)**:
  - lançado em 07/08/2026 por Allegra Jacchia, do X: "Today, we're launching Original Content Rewards"; "Creators should be focused on bringing net new content to the platform instead of maximizing payouts"; o Revenue Sharing tinha incentivos "misaligned" ([WERSM, atualizado em 24/08/2026](https://wersm.com/x-original-content-rewards-creator-payouts/));
  - requisitos na central de ajuda: 500 mil impressões na Home de usuários verificados em 90 dias (sem replies), 500 seguidores verificados, conteúdo original e assinatura Premium, Premium+ ou Premium Business; cumprir os requisitos não garante admissão; há uma apelação ([help.x.com](https://help.x.com/en/using-x/original-content-rewards), via resumo do buscador);
  - inscrições no Revenue Sharing encerradas em 07/08/2026, com pagamentos finais até setembro (fontes secundárias com datas conflitantes: [Complex](https://www.complex.com/pop-culture/a/markelibert/x-original-content-rewards-program-creator-payouts); [Lindsey Gamble](https://www.lindseygamble.com/blog/x-replaces-creator-revenue-sharing-with-new-original-content-rewards-program); [X trending, 07/08/2026](https://x.com/i/trending/2085832166529794516)).
- [B] **Saída de Bier**: anúncio em 05/08/2026 ([post](https://x.com/nikitabier/status/2085105586966827343)).
- [B] Bier, 23/05/2026: "1. Providing the best tools to create content 2. Incentivizing the highest quality content 3. Ranking that content so it finds its audience" ([post](https://x.com/nikitabier/status/2058275858331455815)).

### Inferences
- **Para estratégia de conteúdo** [A + B]:
  - originais (inclusive quotes com opinião) valem mais que reposts em alcance e, desde ago/2026, em dinheiro;
  - isca do tipo "🚨BREAKING" e agregação de conteúdo alheio são alvos explícitos;
  - os mútuos ganharam peso real;
  - links voltaram a ser aceitáveis no corpo do post.
- **Para conteúdo em PT-BR sobre política em 2026** [A]: contas denunciadas ao TSE ficam fora do "Para você" de não seguidores. Crescer nesse nicho via descoberta fica mais difícil para essas contas.
- **"Grok lê tudo e não há heurísticas"** é parcialmente mito [A vs B]. O ranking principal é um transformer (Phoenix) que prevê ações, mas filtros, decaimentos, a vaga de cold start e o multiplicador 0,75 continuam explícitos no código. O LLM Grok aparece no Grox para rótulos e para a nota das respostas.

### Gaps
- Não recuperei a fonte primária da expressão "unregretted user-seconds" de Musk (2022–2023); em 2026 há só o "Unregretted Time Spent" de Bier.
- A página oficial do OCR não pôde ser aberta (Cloudflare). O que é "impressão qualificada", como os pagamentos são calculados e se quotes e fios contam integralmente foram confirmados apenas por fontes secundárias, que divergem.
- Não está claro se mudanças anunciadas por Bier (como os lotes de 35) continuam após a saída dele.

---

## 8. Premium: o que a documentação diz vs. o que o código mostra

### Takeaway
A documentação oficial promete **prioridade nas respostas** (Basic < Premium < Premium+), sem números. O código de ranking do "Para você" de 2026 **não tem multiplicador para autor Premium**: o Premium aparece só como semente do PageRank de credibilidade (user-cred-v2) e como nível do leitor para anúncios. Os dados do Buffer mostram cerca de 10x de alcance mediano para Premium, mas é correlação. Desde ago/2026 o Premium virou **pré-requisito para monetizar** pelo OCR, e o OCR só conta impressões vindas de usuários verificados ou Premium.

### Cited Findings
- [B] **Central de ajuda, "About X Premium"**: três planos (Basic, Premium, Premium+), com prioridade crescente nas respostas; o Premium+ tem "largest reply prioritization", além de Articles e de não ver anúncios ([help.x.com](https://help.x.com/en/using-x/x-premium), via resumo do buscador; a página deu bloqueio do Cloudflare).
- [A] **Sem boost de autor Premium no ranking.** A busca por "premium", "blue_verified" e "verified" em `home-mixer/params`, `home-mixer/scorers`, `xai-value-model` e `vm-ranker` não achou termo de ranking. O `subscription_level` em `home-mixer` é do **leitor** e é usado em logs e anúncios ([query.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/models/query.rs); [ads_injection_logging_side_effect.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/side_effects/ads_injection_logging_side_effect.rs)).
- [A] **user-cred-v2**: contas Premium (selo azul, cinza, dourado ou de organização verificada) recebem massa uniforme de semente no PageRank de credibilidade ([UserCredV2App.scala](https://github.com/xai-org/x-algorithm/blob/main/user-cred-v2/UserCredV2App.scala); `isPremium` em [ValidUserInfo.scala](https://github.com/xai-org/x-algorithm/blob/main/user-cred-v2/ValidUserInfo.scala)). O `user_cred_score` é lido pelo `abuse-enforcement-service` ([entities.rs](https://github.com/xai-org/x-algorithm/blob/main/abuse-enforcement-service/service-lib/src/entities.rs)), isto é, pelo sistema de enforcement, não pela soma de pesos do feed.
- [A-2023, secundário] Em 2023, análises do código citavam boost para assinantes Blue (2x e 4x, em sentidos divergentes entre as fontes). O Twitter depois removeu do repositório dados de ranking "old and unused" ([resumo de busca; nota do Birdwatch](https://birdwatcharchive.org/notes/1732732383076757572); [CSMaP NYU](https://csmapnyu.org/impact/news/what-can-we-learn-from-twitters-open-source-algorithm)). Não verifiquei o parâmetro no código.
- [C] **Buffer** (18,8 milhões de posts, 71 mil contas, cerca de 27% delas Premium, ago/2024–ago/2025, medianas): Regular abaixo de 100 impressões por post, Premium perto de 600, Premium+ acima de 1.550, ou "around 10x more reach per post". O Basic tem pouco ou nenhum ganho mensurável (o texto se contradiz). Mediana de engajamento: Basic cerca de 0,55%, Premium+ 0,53%, Premium cerca de 0,49%, Regular 0%. Sem controle de viés de seleção; descritivo ([Buffer, 02/10/2025](https://buffer.com/resources/x-premium-review/)).
- [B] **OCR** exige Premium, Premium+ ou Premium Business, e o limite é de impressões vindas de usuários verificados ([help.x.com](https://help.x.com/en/using-x/original-content-rewards), via resumo). Um guia de terceiros diz que o pagamento conta impressões únicas de assinantes Premium na Home, com pelo menos metade do post visível; não confirmado na página oficial ([roo.beehiiv](https://roo.beehiiv.com/p/x-original-content-rewards-program-guide)).
- [B] O X publica Articles só a partir de contas Premium ([PiunikaWeb, 07/01/2026](https://piunikaweb.com/2026/01/07/x-articles-premium-nikita-bier-updates/)).

### Inferences
- **O Premium compensa para crescer?** [A + B + C]. O ganho comprovado em documento está nas **respostas** (prioridade) e no **acesso** (posts longos, Articles, analytics completo, monetização). O "10x" do Buffer mistura causa e seleção: quem paga tende a postar mais e melhor.
  - Inferência: para quem usa a estratégia de respostas e quer monetizar, o Premium é praticamente obrigatório.
  - Para quem só publica originais, o código não mostra um multiplicador de ranking; o ganho viria de efeitos indiretos (credibilidade, prioridade nas respostas, formatos).
- **Basic**: o Buffer não vê ganho claro de alcance [C]. A prioridade nas respostas existe, mas é a menor [B].
- **Mito**: "o Premium dá 4x no ranking do Para você". Esse número vem do código de 2023, que foi removido; no código de 2026 não há esse termo [A-2023 vs A].

### Gaps
- O tamanho da prioridade Premium na ordenação das respostas não é público, e o serviço de ranking da conversa não está no repositório.
- O efeito causal do Premium no alcance não tem estudo controlado (diferenças na mesma conta antes e depois de assinar, com amostra).
- O peso do `user_cred_score` em decisões que afetam a distribuição (e não só o enforcement) não ficou claro no código lido.
