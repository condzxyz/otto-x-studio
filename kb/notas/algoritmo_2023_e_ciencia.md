# Algoritmo do Twitter aberto em 2023 + ciência de difusão e crescimento no Twitter/X

> Notas de pesquisa, 14/10/2026. Convenções usadas aqui:
> - **[2023]** = o que estava no código/README/blog publicados entre março e julho de 2023 (commit original `ef4c5eb65e…`, de 31/03/2023, do repo `twitter/the-algorithm`).
> - **[2025]** = o que mudou no mesmo repo no commit `c54bec0d4e…`, de 03/09/2025 ("update for-you recommendations code"). Eu só conferi alguns pontos para marcar o que ficou velho. **O código de 2026 da xAI fica com outro pesquisador.**
> - Links de código apontam para o arquivo no commit exato. `G23` = `https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/`. `G25` = `https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/`.
> - O blog oficial (blog.x.com) bloqueia leitura automática. Li a cópia do Wayback Machine de 01/04/2023 da URL original em blog.twitter.com.

## 1. Pesos do heavy ranker em 2023: valores exatos e como o Twitter mandou interpretar

### Takeaway
No README do heavy ranker, datado de 05/04/2023, o score final é uma soma ponderada de 10 probabilidades previstas. As de maior peso eram "reply que o autor responde" (75), reply (13,5), good profile click (12) e good click (11/10). Like valia 0,5, e os sinais negativos eram muito fortes: negative feedback −74 e report −369. O próprio Twitter avisou que os pesos foram calibrados para que **cada sinal contribuísse mais ou menos o mesmo em média**. Ou seja, peso alto quer dizer evento raro, não que aquele evento "vale mais curtidas".

### Cited Findings
- O modelo é um "parallel MaskNet" que dá, para cada par usuário–tweet, várias probabilidades entre 0 e 1, uma por tipo de engajamento. O score final é `score = sum_i (weight_i × probability_i)` [2023] — [the-algorithm-ml/projects/home/recap/README.md](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)
- Pesos "atuais (April 5, 2023)", copiados do README [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md):

| Label (`scored_tweets_model_weight_*`) | Definição oficial | Peso | Razão vs. like |
|---|---|---|---|
| `fav` | probabilidade de curtir | **0,5** | 1× |
| `retweet` | probabilidade de retweetar | **1,0** | 2× |
| `reply` | probabilidade de responder | **13,5** | 27× |
| `good_profile_click` | abrir o perfil do autor **e** curtir ou responder um tweet | **12,0** | 24× |
| `video_playback50` | (tweet com vídeo) assistir pelo menos metade | **0,005** | 0,01× |
| `reply_engaged_by_author` | responder **e** o autor engajar com essa reply | **75,0** | 150× |
| `good_click` | entrar na conversa **e** responder ou curtir um tweet | **11,0** | 22× |
| `good_click_v2` | entrar na conversa **e ficar ≥ 2 minutos** | **10,0** | 20× |
| `negative_feedback_v2` | reação negativa ("show less often" no tweet ou no autor, block, mute) | **−74,0** | −148× |
| `report` | clicar em Report Tweet | **−369,0** | −738× |

- Como o Twitter mandou ler esses números, palavra por palavra: "Since each engagement has a different average probability, the weights were originally set so that, on average, each weighted engagement probability contributes a near-equal amount to the score. Since then, we have periodically adjusted the weights to optimize for platform metrics." [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)
- O mesmo README avisa que os pesos "can be adjusted at any time" e que o modelo aberto pode ter "small differences from the production model" [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)
- No código aberto, os parâmetros de peso vinham com valor padrão de placeholder (ex.: `ReplyParam` default 1.0 e `ReplyEngagedByAuthorParam` default 1.0, max 200). Os valores reais ficavam numa configuração interna, e o README é a única fonte dos números de produção [2023] — [G23 home-mixer/…/scored_tweets/param/ScoredTweetsParam.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/param/ScoredTweetsParam.scala)
- O `WeightedScoresSumScorer` faz a soma ponderada. Se a soma der **negativa**, ela é comprimida para um valor positivo minúsculo: `(soma + |pesos negativos|) / soma_dos_|pesos| × 0,001`. Na prática, tweets com expectativa líquida negativa vão para o fundo da fila [2023] — [G23 …/scored_tweets/scorer/WeightedScoresSumScorer.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/WeightedScoresSumScorer.scala)
- Pelo blog, o heavy ranker tinha "~48M parameter", era treinado continuamente em interações para otimizar "positive engagement (e.g. Likes, Retweets, and Replies)", usava "thousands of features" e dava "ten labels" [2023] — [Twitter Engineering, "Twitter's Recommendation Algorithm", 31/03/2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm) ([cópia Wayback](https://web.archive.org/web/20230401000000/https://blog.twitter.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm))
- O README do Home Mixer fala em "~6000 features needed for ranking" [2023] — [G23 home-mixer/README.md](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/README.md)

### Inferências
- Se a calibração original igualava a contribuição média, as razões entre pesos são aproximadamente o **inverso** das razões entre probabilidades médias. Exemplo: peso de reply 27× o de like sugere que, na média, uma reply era umas 27× mais rara que um like para um par usuário–tweet. Isso vale para a calibração original. O README diz que os pesos foram reajustados depois, então a relação é só aproximada.
- O que o modelo recompensa é a **probabilidade prevista, para cada espectador**, de conversa (reply, reply respondida pelo autor, entrar na thread e ficar). Não é a contagem bruta de replies que o post já recebeu. Engajamento já acumulado entra como feature, não como multiplicador direto.
- `good_click_v2` (≥ 2 min na conversa) e `good_profile_click` já eram, em 2023, sinais de "atenção de qualidade" (tempo de permanência e interesse no autor), não só cliques.

### Gaps
- Não há valores de peso publicados para depois de abril de 2023. O README nunca foi atualizado com novos números, e no código de 2025 os parâmetros vêm com default 0.0 (ver seção 3).
- O código não mostra as taxas-base reais de cada evento, então não dá para checar se o equilíbrio de contribuições ainda valia em 2023.

## 2. Mecânica de 2023: fontes de candidatos, embeddings, reputação, diversidade, verificado, links e recência

### Takeaway
Em 2023, cada pedido de timeline puxava cerca de 1.500 candidatos. Metade, em média, vinha de quem o usuário segue (Earlybird + RealGraph) e metade de fora da rede (UTEG/GraphJet, que servia uns 15% da timeline, e embeddings SimClusters/TwHIN, a maior fonte de fora da rede). Depois vinham o heavy ranker e uma camada de heurísticas com multiplicadores explícitos no código:
- Blue verified ×4 dentro da rede e ×2 fora.
- Tweets de fora da rede ×0,75.
- Diversidade de autor: decaimento de 0,5 por posição, com piso de 0,25.
- "See fewer": tweet filtrado por 14 dias e depois ×0,2, voltando a ×1,0 em 140 dias.
- Só o melhor tweet de fora da rede por autor passava.
- Filtros contra "concorrentes": contas e URLs.
- Tweepcred (PageRank) com penalidade para quem segue muito mais gente do que tem de seguidores.

### Cited Findings

**Funil e proporção dentro/fora da rede**
- O sistema tenta extrair "the best 1500 Tweets from a pool of hundreds of millions" por pedido. O For You "consists of 50% In-Network Tweets and 50% Out-of-Network Tweets on average, though this may vary from user to user" [2023] — [Blog Twitter Engineering 31/03/2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)
- O README do repo descreve o search-index (Earlybird) como fonte de posts da rede, "~50% of posts come from this candidate source". A frase continua no README de 2025 [2023→2025] — [README do the-algorithm](https://github.com/twitter/the-algorithm/blob/main/README.md)
- As travessias de grafo de engajamento/follow (GraphJet/UTEG: "What Tweets did the people I follow recently engage with?") "currently serve about 15% of Home Timeline Tweets". As abordagens de embedding "have become the larger source of Out-of-Network Tweets" [2023] — [Blog 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)
- Escala: o pipeline roda "approximately 5 billion times per day", termina "in under 1.5 seconds on average", e cada execução gasta "220 seconds of CPU time" [2023] — [Blog 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)
- Heurísticas listadas no blog: Visibility Filtering; **Author Diversity** ("Avoid too many consecutive Tweets from a single author"); **Content Balance** (equilíbrio dentro/fora da rede); **Feedback-based Fatigue**; **Social Proof** ("Exclude Out-of-Network Tweets without a second degree connection… ensure someone you follow engaged with the Tweet or follows the Tweet's author"); Conversations; Edited Tweets [2023] — [Blog 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)

**RealGraph (afinidade entre pessoas)**
- Blog: "The most important component in ranking In-Network Tweets is Real Graph… The higher the Real Graph score between you and the author of the Tweet, the more of their tweets we'll include." [2023] — [Blog 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)
- O RealGraph é um classificador de gradient boosting que prevê a chance de um usuário interagir com outro. Ele é alimentado por interações públicas (favs, RTs, follows) e privadas: "profile views, tweet clicks, and whether or not a user has another user in their address book", agregadas como "decayed sum" diária [2023] — [G23 src/scala/com/twitter/interaction_graph/README.md](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/interaction_graph/README.md)

**SimClusters (comunidades)**
- Usa o grafo de follow como bipartido produtor–consumidor. A similaridade de cosseno entre seguidores gera comunidades por amostragem Metropolis-Hastings. O "Known For" cobre "the top 20M producers and k ~= 145000" comunidades. Cada produtor é Known For no máximo uma comunidade. O InterestedIn do consumidor é `A × V` [2023] — [G23 src/scala/com/twitter/simclusters_v2/README.md](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/simclusters_v2/README.md)
- Blog: "There are 145k communities, which are updated every three weeks." Elas vão de "a few thousand users for individual friend groups, to hundreds of millions of users for news or pop culture" [2023] — [Blog 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)
- Paper: Satuluri et al., "SimClusters: Community-Based Representations for Heterogeneous Recommendations at Twitter", KDD 2020 [2020] — [doi:10.1145/3394486.3403370](https://doi.org/10.1145/3394486.3403370)

**TwHIN (embeddings densos)**
- São embeddings de grafo de conhecimento treinados em relações como "User follows User", "User favorites Tweet" e "User clicks Advertisement". São usados em candidate retrieval e como features [2023] — [the-algorithm-ml/projects/twhin/README.md](https://github.com/twitter/the-algorithm-ml/blob/main/projects/twhin/README.md)
- Paper: El-Kishky et al., "TwHIN: Embedding the Twitter Heterogeneous Information Network for Personalized Recommendation", KDD 2022. Relata ganhos offline e online em ads, follow-recommendation, detecção de conteúdo ofensivo e busca [2022] — [doi:10.1145/3534678.3539080](https://doi.org/10.1145/3534678.3539080)

**Tweepcred (reputação via PageRank)**
- PageRank ponderado sobre o grafo de interações (menções, retweets etc.), com "user mass" baseada em idade da conta, seguidores/seguindo, dispositivo e status de segurança [2023] — [G23 …/graph/batch/job/tweepcred/README](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/graph/batch/job/tweepcred/README)
- Escala 0–100: `round(130 + 5,21 × ln(PageRank))`, com corte em 0 e 100 [2023] — [G23 …/tweepcred/Reputation.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/graph/batch/job/tweepcred/Reputation.scala)
- **Penalidade por seguir demais**: quando a conta segue mais de 2.500 pessoas, calcula-se `ratio = (1+seguindo)/(1+seguidores)`. O PageRank é dividido por `exp(3,0 × (ratio − 0,6) × ln(ln(seguindo)))`, limitado entre 1 e 50 [2023] — [G23 Reputation.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/graph/batch/job/tweepcred/Reputation.scala)
- **Anti-gaming no Earlybird**: os defaults do thrift de busca são `maxHitsPerUser = 3` e `maxTweepcredForAntiGaming = 65`. O `AntiGamingFilter` aceita sem limite os tweets de quem tem Tweepcred acima do teto. Para os demais, aceita até `maxHitsPerUser` resultados por usuário por consulta [2023] — [G23 src/thrift/…/earlybird/thrift/earlybird.thrift](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/thrift/com/twitter/search/earlybird/thrift/earlybird.thrift); [G23 …/earlybird/search/AntiGamingFilter.java](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/java/com/twitter/search/earlybird/search/AntiGamingFilter.java)

**Earlybird / light ranker**
- O README do light ranker diz: "an old part of the stack… last trained several years ago, and uses some very strange features". É uma regressão logística em dois modelos: `recap_earlybird` (dentro da rede) e `rectweet_earlybird` (fora da rede/UTEG). Entre as features estáticas estão "Whether the tweet contains a link", trends, se é reply, qualidade estática do texto e tweepcred [2023] — [G23 …/models/earlybird/README.md](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/python/twitter/deepbird/projects/timelines/scripts/models/earlybird/README.md)
- O blog confirma que o modelo de regressão logística dentro da rede "was last updated and trained several years ago!" e estava sendo redesenhado. Também diz que o Fanout Service, de 12 anos, tinha sido desligado [2023] — [Blog 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)
- Parâmetros de relevância que o Home Mixer manda ao Earlybird: `tweetHasImageUrlBoost = 2.0`, `tweetHasVideoUrlBoost = 2.0`, `multipleHashtagsOrTrendsBoost = 0.6`, `unknownLanguageBoost = 0.05`, `inDirectFollowBoost = 4.0`, `inTrustedCircleBoost = 3.0`, `ageDecayParams(slope = 0.005, base = 1.0)`. O mesmo bloco vem com **`applyBoosts = false`** e usa modelo TensorFlow [2023] — [G23 home-mixer/…/util/earlybird/RelevanceSearchUtil.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/util/earlybird/RelevanceSearchUtil.scala)
- No `FeatureBasedScoringFunction`, os multiplicadores (mídia, trends, hashtags múltiplas, follow direto, penalidade de reply fora da rede) só são aplicados `if (params.applyBoosts)` [2023] — [G23 …/relevance/scoring/FeatureBasedScoringFunction.java](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/java/com/twitter/search/earlybird/search/relevance/scoring/FeatureBasedScoringFunction.java)
- O CR-Mixer, fonte de candidatos fora da rede, também envia `applyBoosts = false` com os mesmos boosts declarados [2023] — [G23 cr-mixer/…/EarlybirdTensorflowBasedSimilarityEngine.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/cr-mixer/server/src/main/scala/com/twitter/cr_mixer/similarity_engine/EarlybirdTensorflowBasedSimilarityEngine.scala)

**Multiplicadores e filtros do Home Mixer (pós-ranking)**
- **Blue verified**: o `VerifiedAuthorScalingScorer` multiplica o score de autores Blue Verified por `BlueVerifiedAuthorInNetworkMultiplierParam` (default **4.0**) dentro da rede e por `BlueVerifiedAuthorOutOfNetworkMultiplierParam` (default **2.0**) fora dela [2023] — [G23 …/functional_component/scorer/VerifiedAuthorScalingScorer.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/VerifiedAuthorScalingScorer.scala); [G23 …/param/HomeGlobalParams.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/param/HomeGlobalParams.scala)
- **Fora da rede ×0,75**: o `OONTweetScalingScorer` (`ScaleFactor = 0.75`) se aplica a tweets de fora da rede. Retweets dentro da rede de um tweet de fora ficam isentos [2023] — [G23 …/scorer/OONTweetScalingScorer.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/OONTweetScalingScorer.scala)
- **Author diversity**: no `AuthorDiversityDiscountProvider` (`Decay = 0.5`, `Floor = 0.25`), o desconto é `score × ((1 − 0,25) × 0,5^posição + 0,25)`, onde posição é a ordem (base 0) do tweet entre os candidatos do mesmo autor [2023] — [G23 …/scored_tweets/scorer/DiversityDiscountProvider.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/DiversityDiscountProvider.scala)
- **Só um tweet de fora da rede por autor**: o `KeepBestOutOfNetworkTweetPerAuthorFilter` agrupa os candidatos de fora da rede por autor e mantém só o de maior score. Ele está no `ScoredTweetsRecommendationPipelineConfig` [2023] — [G23 …/filter/KeepBestOutOfNetworkTweetPerAuthorFilter.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/filter/KeepBestOutOfNetworkTweetPerAuthorFilter.scala); [G23 …/scored_tweets/ScoredTweetsRecommendationPipelineConfig.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/ScoredTweetsRecommendationPipelineConfig.scala)
- **Feedback fatigue**: no `FeedbackFatigueScorer`, um feedback "SeeFewer" vale para 14 dias de filtragem (`DurationForFiltering`). Depois disso, o multiplicador começa em **0,2** e sobe linearmente até **1,0** em 140 dias (`DurationForDiscounting`). O desconto pega o autor do tweet e também tweets curtidos, seguidos ou retweetados pelas contas que o espectador marcou [2023] — [G23 …/scorer/FeedbackFatigueScorer.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/FeedbackFatigueScorer.scala)
- **Concorrentes**: o `OutOfNetworkCompetitorFilter` remove tweets de fora da rede escritos por autores de uma lista `CompetitorSetParam`. O `OutOfNetworkCompetitorURLFilter` remove tweets de fora da rede (que não sejam RT) com URLs de uma lista `CompetitorURLSeqParam`. As listas não são públicas [2023] — [G23 …/filter/OutOfNetworkCompetitorURLFilter.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/filter/OutOfNetworkCompetitorURLFilter.scala); [G23 …/filter/OutOfNetworkCompetitorFilter.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/filter/OutOfNetworkCompetitorFilter.scala)

**Links e URLs em 2023**
- Pelo que encontrei, não há multiplicador explícito de "link" no heavy ranker nem no Home Mixer. `HAS_LINK` aparece como **feature** dos modelos (EarlybirdAdapter, configs de treino do light ranker), com peso aprendido [2023] — [G23 home-mixer/…/adapters/earlybird/EarlybirdAdapter.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/feature_hydrator/adapters/earlybird/EarlybirdAdapter.scala)
- No Earlybird, o `SpamVectorScoringFunction` trata link que não é de mídia nem de notícia como "definite spam vector". Esse tweet ganha spam score quando o Tweepcred do autor está abaixo de `min_tweepcred_with_non_whitelisted_link` (default **25**). Ficam de fora contas verificadas, contas novas (sentinela −128) e casos com engajamento acima de um limiar [2023] — [G23 …/scoring/SpamVectorScoringFunction.java](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/java/com/twitter/search/earlybird/search/relevance/scoring/SpamVectorScoringFunction.java)
- Um audit independente (8 contas sock-puppet, um mês no início de 2020, **antes de Musk**) achou que a curadoria algorítmica "drastically decreases the number of external links in the timeline", mas aumenta a diversidade de fontes (contas e domínios) [2020/2021] — [Bandy & Diakopoulos, "More Accounts, Fewer Links", PACM HCI/CSCW 2021, doi:10.1145/3449152](https://doi.org/10.1145/3449152)
- Declaração oficial pós-2023, de Nikita Bier (head de produto do X), em 19/10/2025: posts com link têm menos alcance "because the web browser covers the post and people forget to Like or Reply". Ele negou que haja "deboost" e, em abril de 2026, chamou a ideia de penalidade a links de "Fake news". Fontes secundárias, mas com citação direta [2025–2026] — [Roboin, 20/10/2025](https://roboin.io/article/en/2025/10/20/x-begins-testing-persistent-post-view-while-opening-links-on-ios/); [Roboin, 13/04/2026](https://roboin.io/article/en/2026/04/13/x-denies-link-deboost-recommends-in-post-links/); [Gigazine, 05/11/2025](https://gigazine.net/gsc_news/en/20251105-x-post-url-link)

**Recência**
- A recência aparece explicitamente nos parâmetros de relevância do Earlybird (`ageDecayParams slope = 0.005, base = 1.0`) [2023] — [G23 RelevanceSearchUtil.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/util/earlybird/RelevanceSearchUtil.scala). O blog descreve o In-Network source como voltado aos tweets "most relevant, recent" [2023] — [Blog 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)

### Inferências
- **Diversidade de autor, em números.** Multiplicadores por posição dentro de um mesmo pedido de feed: 1º tweet do autor ×1,0; 2º ×0,625; 3º ×0,4375; 4º ×0,344; 5º ×0,297; depois tende a ×0,25. É um desconto de concentração **dentro de um feed**, não uma punição à conta por postar muito no dia.
- **Fora da rede, um post por vez.** Juntando "só o melhor tweet de fora da rede por autor", ×0,75 e a exigência de prova social de 2º grau, cada pedido de feed de um não seguidor mostrava no máximo um post de uma conta pequena. E só se alguém que o espectador segue tivesse engajado com o post ou seguisse o autor.
- **Peso do follow ratio.** Uma conta seguindo 3.000 pessoas com 1.000 seguidores (ratio ≈ 3) bate no teto de 50 da divisão do PageRank. Isso tira cerca de 5,21 × ln(50) ≈ 20 pontos do Tweepcred, numa escala de 0–100. Contas abaixo de 2.500 seguindo não sofrem essa penalidade.
- **Boosts de mídia e hashtag.** Os famosos "imagem/vídeo ×2" e "várias hashtags ×0,6" estão declarados num bloco com `applyBoosts = false` nos chamadores do Home Mixer e do CR-Mixer. Muito provavelmente **não** eram aplicados como multiplicadores no For You de 2023. O efeito de mídia viria do que o modelo aprendeu, não de regra fixa.
- **Anti-gaming 3/65.** O limite de 3 resultados por usuário para Tweepcred ≤ 65 existe nos defaults de busca do Earlybird. Não confirmei se o pedido do For You ativa esse filtro.

### Gaps
- Não achei no código de 2023 quais endpoints usam o `SpamVectorScoringFunction`, nem se o pedido do Home Mixer ativa o `AntiGamingFilter`.
- As listas `CompetitorSetParam` e `CompetitorURLSeqParam` não são públicas.
- Como o "Content Balance" mira a proporção dentro/fora da rede não aparece como número fixo no código que li. Só existe a afirmação "50% em média" do blog.
- Não confirmei a forma exata do `AgeDecay` (meia-vida) além dos parâmetros citados.

## 3. O que provavelmente está desatualizado (sinalização para quem cobre 2026)

### Takeaway
O próprio repo `twitter/the-algorithm` recebeu em 03/09/2025 uma grande atualização. Ela muda vários pilares de 2023:
- **Novos rótulos** previstos: bookmark, dwell, share, screenshot, open_link, tempo de vídeo, negative feedback forte/fraco.
- **Pesos não publicados**: os parâmetros aparecem com default 0.0.
- **Novo modelo/serviço "Phoenix"**.
- **Multiplicador de Blue Verified** não aparece mais como scorer.
- **Diversidade de autor** passa a contar também o que o usuário já viu do autor.

Portanto, os números de abril de 2023 (27×, 150×, 4×/2×) não devem ser tratados como vigentes.

### Cited Findings
- Histórico de commits do repo: `c54bec0d4e` em 2025-09-03, "update for-you recommendations code". O commit anterior relevante é `72eda9a24f`, de 2023-07-07 [2025] — [GitHub API, commits de twitter/the-algorithm](https://github.com/twitter/the-algorithm/commits/main)
- Em 2025, o `HomeGlobalParams.scala` declara pesos `home_mixer_model_weight_*` para: `bookmark`, `dwell` (e `dwell_0…4`), `share`, `share_menu_click`, `screenshot`, `open_link`, `profile_dwelled`, `tweet_detail_dwell`, `video_quality_viewed`, `video_quality_viewed_immersive`, `video_quality_watched`, `video_watch_time_ms`, `strong_negative_feedback`, `weak_negative_feedback`. Os de 2023 continuam (fav, reply, retweet, good_click v1/v2, good_profile_click, reply_engaged_by_author, negative_feedback_v2, report, video_playback50). Todos têm **default 0.0** e faixa de −10000 a 10000 [2025] — [G25 home-mixer/…/param/HomeGlobalParams.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/param/HomeGlobalParams.scala)
- Em 2025, a pasta `functional_component/scorer` traz `PhoenixScorer`, `PhoenixModelRerankingScorer`, `WeighedModelRerankingScorer`, `NaviModelScorer`, `FeedbackFatigueScorer` e `OONTweetScalingScorer`. **Não tem mais o `VerifiedAuthorScalingScorer`**. `AuthorIsBlueVerifiedFeature` segue sendo hidratada como feature [2025] — [G25 …/functional_component/scorer/](https://github.com/twitter/the-algorithm/tree/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer)
- O ×0,75 para fora da rede continua em 2025 (`OONTweetScalingScorer`, `ScaleFactor = 0.75`). O desconto de diversidade de autor 0,5/0,25 também [2025] — [G25 OONTweetScalingScorer.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/OONTweetScalingScorer.scala); [G25 DiversityDiscountProvider.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/DiversityDiscountProvider.scala)
- Em 2025, o novo `ImpressedAuthorDecayRescoringProvider` calcula o índice efetivo como `posição + nº de tweets do autor que o usuário já viu (impressed)`. Usa decaimento e piso separados para dentro (`AuthorDiversityInNetworkFloor`, default 0.25) e fora da rede (`AuthorDiversityOutNetworkFloor`, default 0.25). Também existe um `SmallFollowGraphAuthorDiversityDecayFactor` [2025] — [G25 …/scorer/ImpressedAuthorDecayRescoringProvider.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/ImpressedAuthorDecayRescoringProvider.scala); [G25 …/scored_tweets/param/ScoredTweetsParam.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/param/ScoredTweetsParam.scala)
- Em 2025 surgem `TwhinDiversityRescoringParam` e `CategoryDiversityRescoringParam`, ou seja, diversidade por tema/embedding além de por autor [2025] — [G25 HomeGlobalParams.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/param/HomeGlobalParams.scala)
- O README de 2025 se chama "X's Recommendation Algorithm" e lista o `tweet-mixer` como camada de coordenação de candidatos de fora da rede [2025] — [README do the-algorithm](https://github.com/twitter/the-algorithm/blob/main/README.md)

### Inferências
- **O que provavelmente ficou velho:**
  - A tabela de pesos de abril de 2023 (os famosos 27× e 150×).
  - O boost fixo de 4×/2× para Blue Verified. Pode existir de outra forma, mas não está visível como scorer em 2025.
  - O light ranker de regressão logística, que já em 2023 estava sendo substituído.
  - A ausência de sinais de "salvar/compartilhar/tempo de permanência". Em 2025 eles viram rótulos de primeira classe.
- **O que provavelmente sobreviveu até 2025:**
  - Desconto de fora da rede (0,75).
  - Diversidade por autor, agora também cross-sessão, por impressões.
  - Feedback fatigue.
  - Estrutura "prever probabilidades × pesos".
  - Separação entre sinal negativo fraco e forte.

### Gaps
- Os valores reais dos pesos de 2025 não aparecem no código (default 0.0).
- O que é o "Phoenix" (arquitetura, se usa Grok etc.) e o código de 2026 da xAI ficam com o outro pesquisador. Não verifiquei.

## 4. Mitos derivados dos números de 2023: o que a evidência sustenta

### Takeaway
A maioria dos "hacks" que circulam vem de fazer divisão com a tabela de abril de 2023 ou de ler parâmetros que nem eram aplicados. Resumo:
- **Parcialmente verdade, mas mal interpretado**: "1 reply = 27 likes".
- **Sem número fixo comprovado**: "link mata X% do alcance".
- **Falso como regra fixa diária**: "postar mais de N vezes prejudica". O que existe é desconto por concentração no mesmo feed.
- **Verdade em 2023, não visível em 2025**: "Blue = 4×/2×".

### Cited Findings
- **"1 reply = 27 likes" / "reply respondida pelo autor = 150 likes" / "1 report = −738 likes".** A conta sai da tabela: 13,5/0,5 = 27; 75/0,5 = 150; −369/0,5 = −738 [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md). Sites de terceiros ainda repetem o 27× como se valesse em 2026 (prática/marketing) — [BlckAlpaca, base de conhecimento](https://blckalpaca.at/en/knowledge-base/social-media/social-media-algorithms-distribution/x-twitter-algorithm-open-source); [Pashanomics Substack, análise de 2023](https://pashanomics.substack.com/p/twitter-algorithm-review-parts-234). O README, porém, diz que os pesos foram calibrados para igualar a contribuição média de cada probabilidade e depois reajustados por métricas da plataforma [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)
- **"Imagem ×2, vídeo ×2, hashtags ×0,6, idioma desconhecido ×0,05".** Esses números existem, mas no bloco com `applyBoosts = false` do Home Mixer e do CR-Mixer [2023] — [G23 RelevanceSearchUtil.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/util/earlybird/RelevanceSearchUtil.scala); [G23 FeatureBasedScoringFunction.java](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/java/com/twitter/search/earlybird/search/relevance/scoring/FeatureBasedScoringFunction.java)
- **"Link mata o alcance".**
  - Em 2023 há filtros de URL de concorrentes para posts de fora da rede e uma regra de spam para link não-mídia de autor com Tweepcred < 25 [2023] — [G23 OutOfNetworkCompetitorURLFilter.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/filter/OutOfNetworkCompetitorURLFilter.scala); [G23 SpamVectorScoringFunction.java](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/java/com/twitter/search/earlybird/search/relevance/scoring/SpamVectorScoringFunction.java)
  - Evidência empírica de 2020: menos links na timeline algorítmica — [Bandy & Diakopoulos 2021](https://doi.org/10.1145/3449152)
  - Posição oficial de 2025–2026: não há deboost; o alcance cai porque o navegador interno esconde os botões de engajamento — [Roboin 2025](https://roboin.io/article/en/2025/10/20/x-begins-testing-persistent-post-view-while-opening-links-on-ios/); [Roboin 2026](https://roboin.io/article/en/2026/04/13/x-denies-link-deboost-recommends-in-post-links/)
  - Em 2025 o código ganha o rótulo `open_link`, com peso não publicado [2025] — [G25 HomeGlobalParams.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/param/HomeGlobalParams.scala)
- **"Postar mais de N vezes por dia prejudica".**
  - No código de 2023, o mecanismo é o desconto de diversidade 0,5/0,25 dentro do mesmo feed [2023] — [G23 DiversityDiscountProvider.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/DiversityDiscountProvider.scala)
  - No Earlybird há o anti-gaming de 3 resultados por usuário para Tweepcred ≤ 65 [2023] — [G23 earlybird.thrift](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/thrift/com/twitter/search/earlybird/thrift/earlybird.thrift)
  - Em 2025, o decaimento passa a contar os tweets do autor que o usuário já viu [2025] — [G25 ImpressedAuthorDecayRescoringProvider.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/product/scored_tweets/scorer/ImpressedAuthorDecayRescoringProvider.scala)
  - Lado humano: em 1,2 milhão de usuários coreanos (51 dias, mais 22 entrevistas), "muitos tweets em pouco tempo" (burst) apareceu entre os principais motivos de unfollow, ao lado de temas desinteressantes e detalhes banais do dia a dia [2011] — [Kwak, Chun & Moon, "Fragile online relationship", CHI 2011 (registro KAIST)](https://dspace.kaist.ac.kr/handle/10203/168161); [slides SocInfo 2011](https://an.kaist.ac.kr/~sbmoon/talk/2011/111008-socinfo-unfollow.pdf)
- **"Blue = 4×/2×".** Verdade nos defaults do código de 2023 [2023] — [G23 VerifiedAuthorScalingScorer.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/VerifiedAuthorScalingScorer.scala). O scorer não aparece no código de 2025 [2025] — [G25 pasta de scorers](https://github.com/twitter/the-algorithm/tree/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer). Um estudo observacional de jan/2023 achou amplificação maior de posts de baixa credibilidade vindos de contas verificadas [2023] — [Corsi 2024, EPJ Data Science, doi:10.1140/epjds/s13688-024-00456-3](https://doi.org/10.1140/epjds/s13688-024-00456-3)
- **"Vídeo não importa (peso 0,005)".** O README define `video_playback50` como a probabilidade, para tweets com vídeo, de assistir metade. Pela lógica de calibração, peso pequeno indica evento comum entre quem vê vídeo, não irrelevância [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md). Em 2025 há vários rótulos de vídeo novos (`video_quality_watched`, `video_watch_time_ms`…) [2025] — [G25 HomeGlobalParams.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/param/HomeGlobalParams.scala)
- **"Seguir muita gente derruba a reputação".** Sustentado pelo código de 2023 para contas seguindo mais de 2.500 com ratio > 0,6 [2023] — [G23 Reputation.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/graph/batch/job/tweepcred/Reputation.scala)

### Inferências
- **27×.** A leitura correta é que, em abril de 2023, a maior parte do score de um post vinha da **chance prevista de virar conversa**, sobretudo conversa com o autor participando. Isso dá base técnica a "responder as replies no próprio post". Mas não dá para trocar 27 likes por 1 reply como câmbio, nem afirmar que a tabela vale em 2026.
- **Links.** Não existe base primária para um número fixo de "−X% de alcance". O mais defensável: link para fora tira o usuário da tela e reduz os sinais que o ranker usa, e domínios de concorrentes podiam ser filtrados fora da rede (2023).
- **Frequência.** O que o código pune é **sequência do mesmo autor no mesmo feed**. Cada post adicional compete com os seus anteriores pelo mesmo espectador, com retorno decrescente. Isso é diferente de uma penalidade à conta.

### Gaps
- Não achei fonte primária para os números de "links reduzem o alcance em 30–90%" que circulam. Parecem estimativas de praticantes.
- Não há estudo rigoroso que fixe um "N máximo de posts/dia" no X.

## 5. Ciência da difusão no Twitter: evidências mais fortes, tamanhos de efeito e ressalvas

### Takeaway
As evidências mais sólidas são estas:
- Novidade e emoção moral/hostilidade ao grupo rival aumentam o compartilhamento: +20% por palavra moral-emocional e +67% nas chances por termo sobre o "out-group".
- Informação falsa se espalha mais longe e mais rápido, empurrada por humanos.
- A maior parte da popularidade vem de um grande "broadcast", não de viralidade em cadeia.
- O ranking algorítmico do Twitter amplificou conteúdo político e hostil em relação ao feed cronológico.
- A influência social cria desigualdade e imprevisibilidade ("rich get richer" com sorte inicial).
- Imagens têm efeito positivo de "mera presença" no Twitter.

### Cited Findings

**Verdade × falsidade (Vosoughi, Roy & Aral)**
- ~126.000 histórias verificadas, de 2006 a 2017, tuitadas por ~3 milhões de pessoas mais de 4,5 milhões de vezes. A falsidade se espalhou "farther, faster, deeper, and more broadly than the truth" em todas as categorias, com efeito maior em política. Notícias falsas eram mais "novel" e provocaram medo, nojo e surpresa. Bots espalharam verdade e falsidade na mesma taxa, então quem impulsiona a diferença são humanos [2018] — [Science 359:1146, doi:10.1126/science.aap9559](https://doi.org/10.1126/science.aap9559)

**Viralidade estrutural (Goel, Anderson, Hofman & Watts)**
- Um bilhão de eventos de difusão no Twitter (notícias, vídeos, imagens, petições). Há "surprising structural diversity", mas a viralidade estrutural "is typically low, and remains so independent of size, suggesting that popularity is largely driven by the size of the largest broadcast" [2016] — [Management Science 62(1), doi:10.1287/mnsc.2015.2158](https://doi.org/10.1287/mnsc.2015.2158)

**Contágio moral-emocional (Brady et al.)**
- N = 563.312 tweets sobre controle de armas, casamento igualitário e clima. Cada palavra moral-emocional a mais aumentou a difusão em ~20%. O efeito foi mais forte **dentro** das redes liberais e conservadoras do que entre elas [2017] — [PNAS 114(28), doi:10.1073/pnas.1618923114](https://doi.org/10.1073/pnas.1618923114)

**Aprendizado de indignação (Brady et al.)**
- Dois estudos observacionais pré-registrados (7.331 usuários, 12,7 milhões de tweets) e dois experimentos (N = 240). Feedback social positivo (likes/RTs) para indignação aumenta a chance de expressar indignação de novo, como em aprendizado por reforço. Em redes ideologicamente extremas, as pessoas seguem mais a norma do grupo e são menos sensíveis ao feedback [2021] — [Science Advances 7(33), doi:10.1126/sciadv.abe5641](https://doi.org/10.1126/sciadv.abe5641)

**Animosidade ao out-group (Rathje, Van Bavel & van der Linden)**
- N = 2.730.215 posts de mídia e políticos, no Facebook e no Twitter. Cada termo sobre o out-group aumentou as chances de compartilhamento em **67%**. Posts sobre o out-group foram compartilhados cerca de 2× mais que posts sobre o in-group. O efeito foi ~4,8× o de linguagem de afeto negativo e ~6,7× o de linguagem moral-emocional [2021] — [PNAS 118(26), doi:10.1073/pnas.2024292118](https://doi.org/10.1073/pnas.2024292118)

**Amplificação algorítmica de política (Huszár et al., pesquisadores do Twitter)**
- Experimento randomizado de longo prazo: um grupo de controle de "nearly 2 million daily active accounts" recebeu feed cronológico reverso. Em 6 de 7 países, a direita mainstream teve mais amplificação algorítmica que a esquerda mainstream. Nos EUA, fontes de notícia de direita foram mais amplificadas. **Não** houve evidência de que extremos fossem mais amplificados que moderados [dados de 2020; publicado em 2022] — [PNAS 119(1), doi:10.1073/pnas.2025334119](https://doi.org/10.1073/pnas.2025334119)

**Engajamento × satisfação (Milli et al.)**
- Audit pré-registrado contra uma base cronológica. O ranking por engajamento do Twitter "amplifies emotionally charged, out-group hostile content", que os usuários dizem que os faz se sentir pior sobre o grupo rival. Os usuários **não preferem** os tweets políticos escolhidos pelo algoritmo. Um ranking por preferência declarada reduziria conteúdo raivoso, mas poderia reforçar conteúdo pró-atitudinal [audit em 2023; publicado em 2025] — [PNAS Nexus, doi:10.1093/pnasnexus/pgaf062](https://doi.org/10.1093/pnasnexus/pgaf062)

**Baixa credibilidade (Corsi)**
- ~2,7 milhões de posts sobre COVID e clima em jan/2023, 14 dias. Tweets com domínios de baixa credibilidade tiveram mais impressões no agregado. A diferença se concentra em tweets de alto engajamento de contas com muitos seguidores, e é maior em conteúdo tóxico, de viés à direita e de contas verificadas [2024] — [EPJ Data Science 13, doi:10.1140/epjds/s13688-024-00456-3](https://doi.org/10.1140/epjds/s13688-024-00456-3)

**Imagens**
- Li & Xie: posts de companhias aéreas e marcas de SUV no Twitter e no Instagram. Com correção de viés de seleção, a "mera presença" de imagem aumenta o engajamento no Twitter. Fotos de alta qualidade e profissionais ajudam nas duas redes. Rosto humano e combinação imagem–texto ajudam no Twitter, mas não no Instagram [2020; online em 2019] — [Journal of Marketing Research 57(1), doi:10.1177/0022243719881113](https://doi.org/10.1177/0022243719881113)
- Estudo interno do Twitter (prática/oficial, sem revisão por pares): Douglas Mason, mais de 2 milhões de tweets de contas verificadas em um mês. Foto: +35% de RTs; vídeo: +28%; citação: +19%; número: +17%; hashtag: +16% [2014] — [blog.twitter.com/2014/what-fuels-a-tweets-engagement](https://blog.twitter.com/2014/what-fuels-a-tweets-engagement) (números via [Associations Now](https://associationsnow.com/2014/03/study-youre-tweeting-add-photo-higher-engagement/))
- Suh et al.: 74 milhões de tweets. Entre as features de conteúdo, URLs e hashtags tinham forte relação com retweetabilidade. Seguidores, seguidos e idade da conta importavam. O número de tweets passados **não** previa retweetabilidade [2010] — [IEEE SocialCom 2010, doi:10.1109/socialcom.2010.33](https://doi.org/10.1109/socialcom.2010.33)

**Influência e estrutura**
- Cha et al.: indegree (seguidores) não indica influência medida em RTs ou menções. A influência "is not gained spontaneously or accidentally, but through concerted effort such as limiting tweets to a single topic" [2010] — [ICWSM 2010, doi:10.1609/icwsm.v4i1.14033](https://doi.org/10.1609/icwsm.v4i1.14033)
- Bakshy et al.: 1,6 milhão de usuários e 74 milhões de eventos de difusão (2009). As maiores cascatas vêm de quem já foi influente e tem muitos seguidores, mas prever qual usuário ou URL vai explodir é "relatively unreliable". "Ordinary influencers" costumam ser o melhor custo-benefício [2011] — [WSDM 2011, doi:10.1145/1935826.1935845](https://doi.org/10.1145/1935826.1935845)
- Kwak et al.: Twitter de 2009 (mais de 41 milhões de usuários em jul/2009). Rede de baixa reciprocidade, mais parecida com uma mídia do que com uma rede social [2010] — [WWW 2010, doi:10.1145/1772690.1772751](https://doi.org/10.1145/1772690.1772751)
- Weng et al.: um modelo de atenção limitada reproduz a enorme heterogeneidade de popularidade de memes no Twitter "without the need to assume different intrinsic values among ideas" [2012] — [Scientific Reports 2:335, doi:10.1038/srep00335](https://doi.org/10.1038/srep00335)
- Romero, Meeder & Kleinberg: hashtags de temas diferentes se espalham com mecânicas significativamente diferentes [2011] — [WWW 2011, doi:10.1145/1963405.1963503](https://doi.org/10.1145/1963405.1963503)

**Vantagem cumulativa (mecanismo)**
- Salganik, Dodds & Watts: mercado musical artificial com 14.341 participantes. Mais influência social aumentou "both inequality and unpredictability of success". As melhores músicas raramente iam mal, mas "any other result was possible" [2006] — [Science 311:854, doi:10.1126/science.1121066](https://doi.org/10.1126/science.1121066)
- Muchnik, Aral & Taylor: experimento num agregador social de notícias (não é o Twitter). Um upvote inicial aleatório aumentou em 32% a chance de voto positivo seguinte e elevou a nota final em 25% em média. Votos negativos manipulados foram corrigidos pelos usuários [2013] — [Science 341:647, doi:10.1126/science.1240466](https://doi.org/10.1126/science.1240466)
- van de Rijt et al.: experimentos de campo (financiamento, status, endosso, reputação). Sucesso inicial aleatório aumenta o sucesso seguinte, mas com **retornos decrescentes** [2014] — [PNAS 111(19), doi:10.1073/pnas.1316836111](https://doi.org/10.1073/pnas.1316836111)
- Su, Sharma & Goel (Twitter + Stanford): com o lançamento do "Who to Follow" em meados de 2010, todos ganharam seguidores, mas "the most popular users profited substantially more than average". Três motivos:
  - O algoritmo friend-of-friend recomenda proporcionalmente ao grau.
  - O crescimento natural é sublinear no grau.
  - As pessoas aceitam mais recomendações de contas populares.

  [2016] — [WWW 2016, doi:10.1145/2872427.2883040](https://doi.org/10.1145/2872427.2883040)

### Inferências
- Para uma conta que posta todo dia, a ciência aponta alavancas **de conteúdo**: novidade, emoção moral e números concretos tendem a ser mais compartilhados. As alavancas de hostilidade ao grupo rival também funcionam, mas são exatamente o que o X diz punir via negative feedback e o que usuários dizem não querer (Milli). Há trade-off entre alcance e sinais negativos.
- Goel mostra que um post grande quase sempre depende de **uma** conta grande que o difunde. Entrar no raio de broadcast de contas maiores (ser citado ou retweetado por elas) tende a importar mais do que "viralizar em cadeia".
- Salganik, Weng e Bakshy indicam que o resultado de um post isolado é muito ruidoso. Volume com consistência e avaliação por média faz mais sentido do que tirar conclusões de um único post.

### Gaps
- Quase toda a ciência de difusão usa dados de **2006–2020**, isto é, Twitter antes de Musk e antes do For You de 2023. Só Milli (2023) e Corsi (jan/2023) cobrem o começo da era X.
- Não achei estudo revisado por pares e recente (2024–2026) sobre vídeo nativo × imagem no X.
- O efeito de foto do estudo de 2014 é interno e correlacional (contas verificadas), sem controle de seleção.

## 6. O que faz contas pequenas crescerem: estudos rigorosos × anedotas de praticantes

### Takeaway
A evidência rigorosa é limitada e antiga, mas consistente:
- Seguidores novos chegam em **rajadas** quando um post é reshared.
- Reciprocidade e exposição via retweet são os maiores preditores de novos follows.
- Conteúdo informativo, foco temático e ausência de negatividade se associam a crescimento.
- Rajadas de posts e temas banais causam unfollow.
- Recomendações de quem seguir favorecem desproporcionalmente quem já é grande.

Não achei estudo rigoroso sobre "responder contas grandes" nem sobre um horário ou frequência ótimos universais.

### Cited Findings

**Rigorosos (revisados por pares)**
- Hutto, Yardi & Gilbert: 507 usuários e ~meio milhão de tweets, acompanhados por 15 meses com regressão binomial negativa autorregressiva. Conteúdo, comportamento social e estrutura de rede "should be given equal consideration" na previsão de novos seguidores [2013] — [CHI 2013, doi:10.1145/2470654.2470771](https://doi.org/10.1145/2470654.2470771)
- Resumo de imprensa do mesmo estudo (secundário): conteúdo informativo (links/notícias) atraiu muito mais seguidores que conteúdo pessoal, com "30 times more effective" na reportagem. Negatividade foi "the second most harmful factor". Abuso de hashtags prejudicou. Foco temático mais estreito e escrita melhor ajudaram. Burstiness e completude do perfil foram significativos, mas a direção não aparece no texto [2013] — [Popular Science, fev/2013](https://www.popsci.com/science/article/2013-02/more-twitter-followers-try-more-information-less-negativity/)
- Antoniades & Dovrolis: acompanhamento em tempo real de milhares de usuários. Follows causados por retweet são "much more likely than the exogenous creation of new followers". Os fatores mais significativos são a **reciprocidade** e o **número de retweets que um potencial seguidor recebe** ("the number of retweets that a potential new follower receives"), ou seja, exposições repetidas [2015] — [Computational Social Networks, doi:10.1186/s40649-015-0023-6](https://doi.org/10.1186/s40649-015-0023-6)
- Myers & Leskovec: dinâmica completa da rede do Twitter. Ganhos e perdas de seguidores seguem taxas estáveis "interrupted by sudden bursts". Cascatas de reshare "often create such sudden bursts of new connections". Um modelo consegue prever quais difusões geram rajadas [2014] — [WWW 2014, doi:10.1145/2566486.2568043](https://doi.org/10.1145/2566486.2568043)
- Kwak, Chun & Moon: 1,2 milhão de usuários coreanos em 51 dias. Unfollow é previsto por reciprocidade, duração da relação, quanto o seguido é informativo e sobreposição de laços. 43% dos usuários ativos deram unfollow ao menos uma vez. Nas entrevistas (n = 22), os motivos foram burst de tweets, temas desinteressantes e detalhes banais [2011] — [CHI 2011, registro KAIST](https://dspace.kaist.ac.kr/handle/10203/168161); [slides dos autores](https://an.kaist.ac.kr/~sbmoon/talk/2011/111008-socinfo-unfollow.pdf)
- Toubia & Stephen: experimento de campo que adicionou seguidores de forma exógena a usuários não comerciais. A "utilidade de imagem" (status) é maior que a intrínseca para a maioria, o que molda como a postagem reage a ganhar seguidores [2013] — [Marketing Science 32(3), doi:10.1287/mksc.2013.0773](https://doi.org/10.1287/mksc.2013.0773)
- Su, Sharma & Goel: o recomendador de quem seguir do Twitter gerou "rich get richer" [2016] — [WWW 2016, doi:10.1145/2872427.2883040](https://doi.org/10.1145/2872427.2883040)
- Cha et al.: influência vem de "concerted effort such as limiting tweets to a single topic" [2010] — [ICWSM 2010](https://doi.org/10.1609/icwsm.v4i1.14033)
- Horário: Spasojevic et al. (Klout) mostram que a probabilidade de reação depende de "location, daily and weekly behavior patterns and the visibility of the message". Propõem horários de postagem **personalizados** por audiência, e não uma hora universal [2015] — [KDD 2015, doi:10.1145/2783258.2788584](https://doi.org/10.1145/2783258.2788584)

**Mecanismo no código, ligado a crescimento (2023)**
- Para aparecer fora da rede, o post precisava de prova social de 2º grau: alguém que o espectador segue engajou com o post ou segue o autor [2023] — [Blog 2023](https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm)
- O RealGraph usa interações privadas (visitas ao perfil, cliques) para decidir quanto de cada autor entra no feed de quem já segue [2023] — [G23 interaction_graph/README.md](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/interaction_graph/README.md)
- O SimClusters "Known For" coloca cada produtor em **uma** comunidade, a partir da similaridade entre os seus seguidores [2023] — [G23 simclusters_v2/README.md](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/src/scala/com/twitter/simclusters_v2/README.md)

**Praticantes / anedotas (não rigoroso)**
- Teste de um único praticante: dobrar de 6 para 12 tweets agendados por dia teve efeito pequeno no crescimento de seguidores e cerca de +38% de RTs totais. Sem controle [data incerta] — [Social Media Today](https://www.socialmediatoday.com/content/what-happens-when-you-double-your-tweeting-frequency)
- Afirmações de que "contas de notícia que tuítam menos ganham mais seguidores", atribuídas a um estudo da Pew via veículo de PR, sem a fonte original confirmada — [PR Daily](https://www.prdaily.com/study-the-less-you-tweet-the-more-followers-you-get/)

### Inferências
- O que essa evidência permite para uma conta pequena que posta todo dia:
  1. **Foco temático estreito e consistente**. Ajuda o SimClusters a colocar a conta numa comunidade, e Cha e Hutto associam foco a influência e crescimento.
  2. **Conteúdo informativo e específico**, sem negatividade gratuita.
  3. **Conversar nas próprias replies**. Peso máximo no ranker de 2023, e reciprocidade é o maior preditor de follow em Antoniades.
  4. **Gerar reshares**. Seguidores chegam em rajadas após cascatas (Myers & Leskovec).
  5. **Evitar rajadas de posts muito próximos**. Desconto de diversidade no mesmo feed e motivo de unfollow (Kwak 2011).
- "Responder contas grandes" faz sentido por mecanismo, não por estudo: aumenta exposições e a chance de prova social de 2º grau e de RT por contas com grande broadcast (Goel). Não achei teste rigoroso disso.

### Gaps
- Não achei estudo causal revisado por pares sobre frequência de postagem × engajamento ou crescimento no Twitter/X.
- Não achei estudo rigoroso sobre o efeito de responder contas maiores, nem sobre "engagement pods/grupos".
- Os estudos de horário são personalizados (Spasojevic). Os "melhores horários" universais que circulam vêm de dados agregados de ferramentas, ou seja, de praticantes.

## 7. Sinais negativos, dwell time, bookmarks e "regret": por que o X pesa tanto o negativo

### Takeaway
Os pesos negativos enormes de 2023 (−74 e −369) se explicam principalmente pela calibração por raridade, que o próprio Twitter descreveu: eventos raros precisam de peso grande para contar. Há também uma motivação científica mais ampla:
- O engajamento revelado diverge da preferência declarada, e o ranking por engajamento amplifica o que usuários dizem não querer.
- Sinais de qualidade, pesquisas e tempo de permanência melhoram a retenção de longo prazo.

O código de 2025 incorpora dwell, bookmark, share e negative feedback forte/fraco como rótulos próprios.

### Cited Findings
- Calibração: os pesos foram definidos para que cada probabilidade ponderada "contributes a near-equal amount to the score" na média [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)
- Definição de `negative_feedback_v2`: "show less often" no tweet ou autor, block ou mute. `report` é clicar em Report. Os pesos são −74 e −369 [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)
- Efeito persistente do "see fewer": 14 dias filtrado, depois ×0,2 voltando a ×1,0 em 140 dias, estendido a conteúdo que outras contas marcadas curtiram ou retweetaram [2023] — [G23 FeedbackFatigueScorer.scala](https://github.com/twitter/the-algorithm/blob/ef4c5eb65e6e04fac4f0e1fa8bbeff56b75c1f98/home-mixer/server/src/main/scala/com/twitter/home_mixer/functional_component/scorer/FeedbackFatigueScorer.scala)
- Em 2023, já havia um sinal de dwell: `good_click_v2`, ficar ≥ 2 minutos na conversa, com peso 10 [2023] — [README do recap](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)
- Em 2025: `bookmark`, `dwell`/`dwell_0…4`, `tweet_detail_dwell`, `profile_dwelled`, `share`, `screenshot`, `strong_negative_feedback` e `weak_negative_feedback` viram pesos próprios, com valores não publicados [2025] — [G25 HomeGlobalParams.scala](https://github.com/twitter/the-algorithm/blob/c54bec0d4e029fe34926ef3258a86ccacc0d0182/home-mixer/server/src/main/scala/com/twitter/home_mixer/param/HomeGlobalParams.scala)
- Milli et al.: o ranking por engajamento amplifica conteúdo hostil que os usuários dizem que os faz sentir pior, e eles não preferem os tweets políticos escolhidos por ele. Preferências declaradas reduziriam esse conteúdo [2025] — [PNAS Nexus, doi:10.1093/pnasnexus/pgaf062](https://doi.org/10.1093/pnasnexus/pgaf062)
- Cunningham, Pandey, Sigerson, Stray, Allen, Iyer et al.: síntese de workshop com 18 participantes de indústria e academia, com 20 proposições. Métricas de qualidade e pesquisas por item "can improve long-term retention", mesmo correlacionando negativamente com engajamento de curto prazo [2024] — [arXiv:2402.06831](https://arxiv.org/abs/2402.06831)
- Kleinberg, Mullainathan & Raghavan: o "inversion problem". Recomendadores preveem cliques "but hope to identify preferences", e "people can click mindlessly" [2023/2024] — [Perspectives on Psychological Science, doi:10.1177/17456916231212138](https://doi.org/10.1177/17456916231212138)
- Yi et al. (Yahoo): dwell time por item como proxy de relevância e satisfação, normalizado por dispositivo e contexto. Ganhos offline e online ao incorporá-lo em learning-to-rank [2014] — [RecSys 2014, doi:10.1145/2645710.2645724](https://doi.org/10.1145/2645710.2645724)
- Brady et al.: feedback positivo reforça a expressão de indignação. O sistema de recompensas da plataforma molda o comportamento de quem posta [2021] — [Science Advances, doi:10.1126/sciadv.abe5641](https://doi.org/10.1126/sciadv.abe5641)

### Inferências
- Para quem posta todo dia, o risco assimétrico é real: um "show less often", mute ou block de um espectador reduz o alcance futuro **para aquele espectador** por meses, segundo o código de 2023. Também pesa muito na previsão para pessoas parecidas. Provocação que gera reply mas também mute pode ter saldo negativo.
- O caminho de 2023 para 2025 (dwell, bookmark, share como rótulos) bate com a literatura sobre ir além do engajamento: conteúdo que faz salvar e ler até o fim tende a ganhar peso em relação a curtida rápida. Os pesos de 2025 não são públicos, então isso é direção, não magnitude.

### Gaps
- Não achei estudo revisado por pares específico sobre **bookmarks/saves** como sinal de ranking no X.
- Não achei pesquisa pública de engenheiros do Twitter/X que justifique os valores −74 e −369 além da frase sobre calibração do README.
- O peso de `open_link` e dos rótulos de dwell em 2025 é desconhecido.
