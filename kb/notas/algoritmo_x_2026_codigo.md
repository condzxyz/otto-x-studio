# Algoritmo "Para você" do X em 2026: ficha técnica lida no código (xai-org/x-algorithm)

Código lido no commit `17c96bf346df3d62b90f1bb01830d432dba74485` de 2026-10-14 03:41 UTC, o HEAD de `main` em 14/10/2026. O cabeçalho de `home-mixer/params/param.rs` diz "mirrored from config feature-switch defaults; last sync 2026-10-13T16:00:30Z". O repositório tem 48 commits, todos com a mensagem "Open-source X Recommendation Algorithm". Os principais são 2026-01-20 (aaa167b, primeira versão), 2026-05-15 (0bfc279), 2026-08-13 (47c1bcd, grande expansão) e, desde então, commits quase diários de sync de parâmetros. O histórico de valores citado abaixo saiu de `git log -p` desses arquivos. Nos links, B = `https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485`.

Legenda de confiança:
- **[CÓDIGO]**: lido no fonte.
- **[DOC-X]**: README ou doc oficial do repo, ou post oficial do X.
- **[IMPRENSA]**: cobertura de terceiros.
- **[INFERÊNCIA]**: dedução minha a partir do código.

---

## 1. Visão geral do pipeline: fontes de candidatos, hidratação, filtros, scorers, ranking e mistura

### Takeaway
O "Para você" é montado a cada requisição pelo `home-mixer`, em duas etapas:
1. **Post Pipeline** (`PhoenixCandidatePipeline`): busca candidatos no Thunder (rede, ou seja, quem o viewer segue), no Phoenix retrieval, no SimClusters e em posts populares. Depois hidrata, aplica cerca de 20 filtros, pontua com o transformer Phoenix (probabilidades por ação), soma os pesos e chama o serviço `vm-ranker`. O `vm-ranker` aplica diversidade de autor, desconto fora da rede e o slot de cold-start, e reordena por DPP (diversidade semântica). Por fim seleciona o top 50 e roda os filtros de visibilidade.
2. **Blending Pipeline** (`ForYouCandidatePipeline`): intercala anúncios, "Quem seguir" e prompts.

### Cited Findings
- [DOC-X] O feed combina posts "In-Network", vindos do `thunder/` (posts recentes de quem você segue, em memória), com "Out-of-Network", vindos do `phoenix/` retrieval e do `simclusters/`. O `popular_posts_source` adiciona uma lista compartilhada de posts populares. Tudo é ranqueado junto pelo mesmo modelo. — [README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [DOC-X] O diagrama oficial define 7 etapas: query hydration, candidate sources em paralelo, candidate hydration, pre-scoring filters, scoring, seleção (`TopKScoreSelector`) e post-selection filters (`VFFilter`, `DedupConversationFilter`). Na etapa de scoring rodam `PhoenixScorer`, depois `RankingScorer` (soma ponderada, "repeated-author decay, an out-of-network discount, a new-author boost") e depois `VMRanker`. — [README, Request Path](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] As fontes são instanciadas nesta ordem: `thunder_source`, `popular_posts_source`, `tweet_mixer_source`, `simclusters_source`, `phoenix_source`, `phoenix_topics_source`, `phoenix_moe_source`, `sid_source`, `cached_posts_source`. — [phoenix_candidate_pipeline.rs L356-366](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs#L356-L366)
- [CÓDIGO] Fontes ligadas por padrão: `EnablePhoenixSource=true` (até `PhoenixMaxResults=1000`, mais `PhoenixColdStartMaxResults=200`), `EnableSimclustersSource=true`, `EnablePopularPostsSource=true` (500) e Thunder com `ThunderMaxResults=1200`. Fontes desligadas: `EnableTweetMixerSource=false`, `EnableSidSource=false`, `EnablePhoenixMOESource=false` (`PhoenixMOEMaxResults=0`). — [param.rs L4-59, L640-651, L955-966](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs)
- [CÓDIGO] Hidratadores de candidato, em ordem: `InNetworkCandidateHydrator`, `BidirectionalFollowHydrator`, core data, `PhoenixReplyAncestorsHydrator`, `QuoteHydrator`, `MediaInfoHydrator`, `SubscriptionHydrator`, `GizmoduckCandidateHydrator` (dados do autor), `BlockedByHydrator`, `FilteredTopicsHydrator`, `LanguageCodeHydrator`, `EngagementCountsHydrator`, `SemanticIdHydrator`. — [phoenix_candidate_pipeline.rs L368-395](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs#L368-L395)
- [CÓDIGO] Os scorers da Post Pipeline são exatamente `vec![phoenix_scorer, vm_ranker]`. A soma ponderada, o cold-start e os multiplicadores rodam dentro do `VMRanker` (cálculo local) e do serviço `vm-ranker`. Não existe mais struct `RankingScorer`: o link do README aponta para `home-mixer/scorers/value_model.rs`, que só define `weights_for`/`weighted_score`. — [phoenix_candidate_pipeline.rs L457-458](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs#L457-L458); [scorers/value_model.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/value_model.rs)
- [CÓDIGO] O `VMRanker` calcula localmente o weighted score e a decisão de cold-start e envia ao `vm-ranker` um `RankRequest` com `compute_value_model: true` e `value_model_id: "dpp"`. Se a RPC falhar, serve os scores locais (fallback "rpc_error"). — [vm_ranker.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/vm_ranker.rs); [vm_ranker_request.rs L31-40](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/vm_ranker_request.rs#L31-L40)
- [CÓDIGO] O `vm-ranker` lê o mesmo arquivo de feature switches do home-mixer (`features/home-mixer/main/rust_home_mixer.yml`) via config-sync. Calcula `compute_value_scores` (soma ponderada, depois bônus de exploração, lift de cold-start e multiplicadores de diversidade e OON) e então aplica DPP. — [config_sync.rs L16](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/config_sync.rs#L16); [vm-ranker/scoring/mod.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/scoring/mod.rs); [config.rs L1 (FS_PATH)](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/config.rs#L1)
- [CÓDIGO] DPP: `DppEnabled=true`, `DppTheta=0.65` e `DppMaxSelectedRank=150`. O kernel combina qualidade `exp(alpha·score/max)`, com `alpha=θ/(2(1−θ))`, e cosseno entre embeddings dos posts. A seleção é gulosa ("dá um pouco de score em troca de menos similaridade entre vizinhos"). — [vm-ranker/params.rs L236-253](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs#L236-L253); [vm-ranker/dpp.rs L40-140](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/dpp.rs#L40-L140); [README, Ranking](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] Tamanhos: `TOP_K_CANDIDATES_TO_SELECT = 50` e `RESULT_SIZE = 35` posts por resposta. Posição fixa: `WHO_TO_FOLLOW_POSITION = 6`, `PROMPTS_POSITION = 0`, `FEED_SURVEY_POSITION = 12`. Anúncios usam `AdsBlenderType="multi_risk"`. — [config.rs L17-34](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/config.rs#L17-L34); [param.rs L793-798](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L793-L798)
- [CÓDIGO] Filtros pós-seleção: `VFFilter`, `AncillaryVFFilter`, `AncestorVideoFilter`, `DedupConversationFilter`, `VideoCarouselFilter`. — [phoenix_candidate_pipeline.rs L487-493](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs#L487-L493)
- [DOC-X] Caminho de rotulagem (fora da requisição):
  - Posts e mídia: `grox/` (classificadores de texto e mídia via LLM), `media-model-proxy/` e `clip/`.
  - Contas: `agatha/` (blocks e reports relativos a favoritos), `bdsm/` (comportamento inautêntico) e `user-cred-v2/` (PageRank).
  - Regras: `scarecrow/`, `botmaker/` e `abuse-enforcement-service/`.
  - Os rótulos alimentam `visibility-filtering/`, que responde ALLOW, NOTICE, INTERSTITIAL ou DROP.
  - [README, Labeling Path](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [DOC-X] "Ranking sets the order. Whether a post can be shown at all is decided separately, by visibility-filtering". — [README, Overview](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [DOC-X] Phoenix (modelo):
  - Retrieval é two-tower. Os candidatos são representados por "semantic IDs" (códigos residual-quantized de 6 níveis × 256, derivados do embedding multimodal do post) mais hash do autor.
  - Ranking é um transformer com "candidate isolation": candidatos não se enxergam entre si.
  - Entradas: hash de post e autor, SIDs, contexto (fuso, hora local, superfície, idade do post), dwell no histórico e features de perfil do viewer (país, idioma, localização, gênero, faixa etária, apps instalados).
  - [phoenix/README.md L99-125, L180-192](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/README.md)

### Inferences
- [INFERÊNCIA] Para uma conta pequena, há só dois caminhos de distribuição: Thunder, para quem já segue, e Phoenix retrieval ou SimClusters, para quem não segue. Popular posts saem de contas "most-followed active" e não se aplicam a uma conta pequena.
- [INFERÊNCIA] O conteúdo entra no ranking via semantic IDs multimodais. Posts do mesmo tema compartilham prefixos de SID, então consistência temática ajuda o retrieval a achar o público. O DPP, por outro lado, penaliza posts muito parecidos entre si dentro da mesma página.

### Gaps
- O código do lado `vm-ranker` que consome o payload experimental "debias/pacing" não aparece; os dois estão desligados por padrão.
- Não está publicado como o índice "HomeCold"/"ZeroFav" do Phoenix escolhe os posts (ver seção 7).

---

## 2. Pontuação: pesos do value model por ação prevista (positivas e negativas)

### Takeaway
Score = Σ(peso × P(ação) prevista), mais termos contínuos (tempo de dwell). Os pesos multiplicam **probabilidades previstas para aquele viewer**, não contagens brutas; o próprio repo diz isso em comentário. Pesos de produção espelhados em 13/10/2026:

| Ação | Peso |
|---|---|
| like | **0.66** (era 0.6 até o sync de 12/10 e 0.5 até 08/10) |
| reply | 5 (20 com mútuo; ver seção 3) |
| repost | 1 |
| quote | 5 |
| share | 2 |
| share via DM | 5 |
| copiar link | 20 |
| seguir autor | 4 |
| clique no perfil | 0 |
| abrir link | 0.2 |
| clique | 0.3 |
| expandir foto | 0.05 |
| abrir vídeo | 0.02 |
| VQV | 0 |
| dwell (binário) | 0.05 |
| dwell_time | 0.006 |
| click_dwell_time | 0.4 |
| not interested | **−52.272** |
| mute | −58.8 |
| block | −31.2 |
| report | −234 |
| not dwelled | −0.02 |

### Cited Findings
- [CÓDIGO] Pesos em `home-mixer/params/param.rs` no HEAD:
  - `FavoriteWeight 0.66` (L320)
  - `ReplyWeight 5.0` (L321)
  - `BidirectionalFollowReplyWeightBoost 15.0` (L323-327)
  - `BidirectionalFollowDwellWeightBoost 0.0` (L328-333)
  - `RetweetWeight 1.0` (L334)
  - `PhotoExpandWeight 0.05`
  - `VideoOpenWeight 0.02`
  - `ClickWeight 0.3` (L347)
  - `OpenLinkWeight 0.2` (L348)
  - `ProfileClickWeight 0.0`
  - `VqvWeight 0.0`
  - `ShareWeight 2.0` (L356)
  - `ShareViaDmWeight 5.0`
  - `ShareViaCopyLinkWeight 20.0`
  - `DwellWeight 0.05` (L369)
  - `QuoteWeight 5.0` (L370)
  - `QuotedClickWeight 0.05`
  - `QuotedVqvWeight 0.0`
  - `FollowAuthorWeight 4.0`
  - `PostUnexploredWeight 0.015`
  - `ReactWithVideoWeight 0.0`
  - `ContDwellTimeWeight 0.006`
  - `ContClickDwellTimeWeight 0.4`
  - `NotInterestedWeight −52.272` (L414-419)
  - `BlockAuthorWeight −31.2`
  - `MuteAuthorWeight −58.8`
  - `ReportWeight −234.0` (L432)
  - `NotDwelledWeight −0.02`
  - [param.rs L320-438](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L320-L438)
- [CÓDIGO] Comentário literal no código: "Each weight multiplies the *predicted* probability of that action (P(favorite), P(repost), …) or a continuous value e.g. watch time -- the weights do not multiply raw engagement counts." O mesmo comentário diz que é incorreto ler "one report cancels 468 likes" e que "the baseline probability of a Report is more than 1000x lower than a Like, so it's weighted more to allow the prediction to affect the final ranking at all." — [param.rs L291-319](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L291-L319); idêntico em [xai-value-model/scoring.rs L28-54](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L28-L54)
- [CÓDIGO] O mesmo comentário diz, sobre report e block em massa:
  - "reports from bad actors will primarily affect recommendations for users who are similar to the bad actors".
  - "it must take place on a post served in Home Timeline. Directly navigating to a post (i.e., coordinating via groupchat) has no ranking impact."
  - [param.rs L307-319](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L307-L319)
- [DOC-X] Nota de 14/08/2026 no README ("How weights work"): "The weights are a multiple on your own predicted probability of Liking, Reporting, etc, which is substantially driven by your own behavior." — [README, Notable Updates](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] Aritmética em `compute_weighted_score`:
  - Soma de `apply(score, weight)` para 29 termos, entre eles `video_continuation`, `user_video_continuation` e `profile_visit_secs`. Esses três têm peso 0 no home-mixer; no vm-ranker o default de código também é 0.
  - `vqv` só conta se `vqv_eligible`.
  - `post_unexplored` só conta para posts in-network (`post_unexplored_include_out_of_network=false`).
  - [xai-value-model/scoring.rs L69-139](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L69-L139); [scorers/value_model.rs L8-49](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/value_model.rs#L8-L49)
- [CÓDIGO] Offset de negativos (`offset_score`): score combinado ≥0 recebe `+0.001`. Score combinado <0 vira `(combinado + soma_negativa)/soma_total × 0.001`, ficando entre 0 e 0.001. — [scoring.rs L161-171](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L161-L171); `NEGATIVE_SCORES_OFFSET = 0.001` em [weights.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/weights.rs)
- [CÓDIGO] Histórico dos pesos espelhados, a partir de 13/08 (47c1bcd):
  - like 0.5 → 0.6 (commit [e1a0375](https://github.com/xai-org/x-algorithm/commit/e1a0375a903899984545c663bb0bccb3cdcdf046), 13/10, sync de 12/10) → 0.66 (commit [17c96bf](https://github.com/xai-org/x-algorithm/commit/17c96bf346df3d62b90f1bb01830d432dba74485), 14/10, sync de 13/10).
  - not interested −43.2 → −47.52 (commit [a707cc2](https://github.com/xai-org/x-algorithm/commit/a707cc27ba36d3fa79450c9cffcc48a82d080b02), 29/09) → −52.272 (17c96bf, 14/10).
  - click 0.4 → 0.3 e cont_click_dwell_time 0 → 0.4 (a707cc2, 29/09).
  - VQV 0.05 → 0; dwell 0 → 0.05; video_open 0.05 → 0.07 (commit [0d3cdd8](https://github.com/xai-org/x-algorithm/commit/0d3cdd806c405f04db7030f720b48687aa304061), 25/08). Depois video_open 0.07 → 0.02 (e1a0375, 13/10).
  - cont_dwell_time 0.004 → 0.006 (e1a0375).
  - post_unexplored 0.02 → 0.015 (commit [78460ca](https://github.com/xai-org/x-algorithm/commit/78460ca8b65c57ddd3a05f9217c8aaeba214b628), 07/10).
  - Sem mudança desde 13/08: reply 5, repost 1, quote 5, share 2, DM 5, copiar link 20, seguir autor 4, block −31.2, mute −58.8, report −234 e boost bidirecional 15.
  - Fonte: `git log -p home-mixer/params/param.rs`.
- [CÓDIGO] `vm-ranker/params.rs` tem defaults de código diferentes e desatualizados: `FavoriteWeight 0.5`, `NotInterestedWeight −47.52`, `VideoOpenWeight 0.07`, `ContDwellTimeWeight 0.004` e `PostUnexploredWeight 0.02`. O arquivo **não** tem o cabeçalho "mirrored from config". O `vm-ranker` lê os valores do mesmo YAML de feature switches via config-sync. — [vm-ranker/params.rs L1-130](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs); [ranking_config.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/ranking_config.rs)
- [CÓDIGO] Bookmark existe como rótulo de treino (`"IsBookmarked": ["ClientTweetBookmark"]`), mas **não há cabeça nem peso de bookmark** no value model (`PhoenixScores` não tem `bookmark`). — [phoenix/xrex/data/recsys/constants.py L38-40](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/xrex/data/recsys/constants.py#L38-L40); [xai-value-model/phoenix_scores.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/phoenix_scores.rs)
- [CÓDIGO] Há perturbação de pesos por usuário (`WeightPerturbationSigma`), com sigma default 0.0, ou seja, desligada. — [vm-ranker/params.rs L158](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs#L158); [weights.rs `perturbed`](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/weights.rs)
- [DOC-X] "many tunable values are read from a configuration system… we run cron scripts that set the defaults in this repository's code to be the primary production values". Também: "Our aim is for experiments running at a notable share of traffic — e.g. 10% or more — to be visible in this repository." — [README, Experiments and Configuration](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)

### Inferences
- [INFERÊNCIA] Pela comparação com o código, a nota de 14/08 do README que cita "468 vezes" usava like = 0.5 (234/0.5 = 468). Com like = 0.66, a razão report/like é ~355×. Mas o próprio X avisa que essa razão não significa "1 report cancela N likes".
- [INFERÊNCIA] No sync de 13/10, like e not-interested foram multiplicados por 1,1 juntos: 0.6→0.66 e −47.52→−52.272. Em 29/09, not-interested já tinha passado de −43.2 para −47.52 (×1,1). É um padrão de ajuste fino em produção. Esperar que esses dois números mudem de novo; não publicar valores sem a data do sync.
- [INFERÊNCIA] Pelo offset, um post cuja soma prevista fica negativa para aquele viewer vai para baixo de todos os posts com soma positiva. Isso acontece quando as negativas (not interested, mute, block, report) superam as positivas.
- [INFERÊNCIA] Os pesos mais altos por unidade de probabilidade são copiar link (20), reply (5, ou 20 entre mútuos), quote (5), DM (5) e seguir autor (4). Como as probabilidades-base diferem muito entre ações, o peso sozinho não diz qual ação "vale mais" no score final.

### Gaps
- A semântica exata de `post_unexplored` ("ServerTweetPostUnexplored") não está documentada.
- A unidade de `dwell_time` e `click_dwell_time` (presumivelmente segundos) não está explícita no código lido.

---

## 3. Boosts ligados a reply: follow mútuo e "autor responde de volta"

### Takeaway
O único boost de reply no código de 2026 soma **+15 ao peso de reply (5 → 20)** quando três condições valem ao mesmo tempo:
- o post é original (não é reply nem repost);
- o viewer segue o autor;
- o autor segue o viewer.

O boost multiplica P(o viewer responder). Não existe no código de 2026 um peso de "autor responde ao reply" (o famoso 75 de 2023).

### Cited Findings
- [CÓDIGO] `BidirectionalFollowReplyWeightBoost = 15.0`, `BidirectionalFollowDwellWeightBoost = 0.0` e `EnableBidirectionalFollowHydration = true`. — [param.rs L322-333, L713-718](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L322-L333)
- [CÓDIGO] `reply_weight_for`: se o boost ≠ 0 e `bidirectional_boost_eligible`, retorna `reply + boost`. — [xai-value-model/weights.rs L84-91](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/weights.rs#L84-L91)
- [CÓDIGO] `bidirectional_boost_eligible() = !is_reply && !is_retweet && is_mutual_follow_author`. — [xai-value-model/inputs.rs L20-22](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/inputs.rs#L20-L22)
- [CÓDIGO] `BidirectionalFollowHydrator` pega os autores dos candidatos que o viewer segue, chama `check_followed_by(viewer, autores)` e marca `is_mutual_follow_author`. Quote post conta como "original" porque não é reply nem retweet. — [docs/BIDIRECTIONAL_BOOST_CHANGE.md](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/docs/BIDIRECTIONAL_BOOST_CHANGE.md); [candidate_hydrators/bidirectional_follow_hydrator.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_hydrators/bidirectional_follow_hydrator.rs)
- [DOC-X] Linha do tempo oficial:
  - 10/07/2026: A/B com boost de 5, 10, 15 ou 20; a maioria ficou em 0.
  - 13/07/2026: lançamento amplo com 20.
  - 24/07/2026: valor mudado para 15, com o argumento: "the World Cup was happening yet some people weren't seeing as much discussion of it as they wanted, given many of the posts were from accounts they didn't follow".
  - Um boost de dwell também foi testado, mas "not shipped more broadly".
  - [docs/BIDIRECTIONAL_BOOST_CHANGE.md](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/docs/BIDIRECTIONAL_BOOST_CHANGE.md) (cita [post do Nikita Bier](https://x.com/nikitabier/status/2076747704248758617))
- [CÓDIGO] Busca no código de 2026 (`home-mixer`, `xai-value-model`, `vm-ranker`): não há termo "reply engaged by author" nem peso para o autor curtir ou responder o reply no value model. — [xai-value-model/weights.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/weights.rs)
- [CÓDIGO] No modelo separado de ranking de **respostas dentro da conversa** (reply ranking do Phoenix), existem features de posicionamento `focal_author_reply`, `fav_by_root_author`, `author_verified`, `grox_score` e `self_reply`. Isso vale para a ordem das respostas na thread, não para o "Para você". — [phoenix/crates/common/xai-recsys/src/reply.rs L32-68](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/crates/common/xai-recsys/src/reply.rs#L32-L68)
- [IMPRENSA] Blogs ainda repetem "author reply = 75× like", mas esse valor vem do release de 2023 (`reply_engaged_by_author 75.0`). — [the-algorithm-ml README (2023)](https://raw.githubusercontent.com/twitter/the-algorithm-ml/main/projects/home/recap/README.md); [byteiota](https://byteiota.com/x-algorithm-open-source/)

### Inferences
- [INFERÊNCIA] Para a @ottodoti, o boost só vale para viewers com quem a conta tem follow mútuo. Seguir de volta quem interage (com critério) aumenta o peso de reply nos posts originais da marca no feed dessas pessoas, de 5 para 20.
- [INFERÊNCIA] O fato de o autor curtir ou responder replies pode influenciar o ranking das respostas na conversa (features `fav_by_root_author`/`focal_author_reply`). No "Para você", o efeito só seria indireto, pelo aprendizado do modelo; não há peso explícito.

### Gaps
- Não verifiquei se o valor 15 vale para 100% dos usuários. O doc diz que em julho continuavam experimentos com 0, 5, 10 e 15 em parcelas variáveis; o default espelhado é 15.

---

## 4. Diversidade de autor (posts seguidos do mesmo autor)

### Takeaway
O multiplicador é `(1−floor)·decay^k + floor`, onde k é o número de posts do mesmo autor com score maior **no mesmo pool de candidatos da requisição**. Com decay 0.5 e floor 0.25:

| Post do autor no pool | Multiplicador |
|---|---|
| 1º | 1.0 |
| 2º | 0.625 |
| 3º | 0.4375 |
| 4º | 0.34375 |
| 5º | 0.296875 |
| limite | 0.25 |

Está **ligado** (`EnableAuthorDiversity=true`) no `vm-ranker`. No cálculo local do home-mixer está desligado; ele só é usado como fallback.

### Cited Findings
- [CÓDIGO] `diversity_multiplier(decay, floor, exponent) = (1.0 - floor) * decay.powf(exponent) + floor`. `author_pool_counts` ordena os candidatos por score e conta quantos do mesmo autor vieram antes. — [xai-value-model/scoring.rs L183-204](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L183-L204)
- [CÓDIGO] `EnableAuthorDiversity = true`, `AuthorDiversityDecay = 0.5` e `AuthorDiversityFloor = 0.25` em `vm-ranker/params.rs`, usados por `weights_from_params`. — [vm-ranker/params.rs L169-186](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs#L169-L186); [vm-ranker/scoring/value_model.rs L68-115](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/scoring/value_model.rs)
- [CÓDIGO] No home-mixer, `weights_for` fixa `enable_author_diversity: false`, `author_diversity_decay: 1.0` e `author_diversity_floor: 1.0`. Esse é o score local, usado no cold-start e no fallback da RPC. — [home-mixer/scorers/value_model.rs L45-47](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/value_model.rs#L45-L47)
- [CÓDIGO] Os mesmos valores (true/0.5/0.25) estavam no arquivo espelhado de produção `home-mixer/params/param.rs` até o sync de 2026-09-22. Foram removidos dali no commit [44d37eb](https://github.com/xai-org/x-algorithm/commit/44d37ebf87f2185b949cd37b710d410c2a77d21f) (24/09), quando `vm-ranker/params.rs` passou a concentrá-los (criado em [1b3fec2](https://github.com/xai-org/x-algorithm/commit/1b3fec20bc3fd9879bc3e9f3d9c42753cdc3fede), 23/09).
- [CÓDIGO] O teste `hand_computed_parity` confirma `diversity_second_from_author = (1.0 - 0.25) * 0.5 + 0.25` (= 0.625). — [scoring.rs, mod tests](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs)
- [DOC-X] "Author Diversity: each post after an author's first is multiplied by a decaying factor, down to a floor." — [README, Scoring and Ranking](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)

### Inferences
- [INFERÊNCIA] A penalidade vale dentro do lote de candidatos de uma mesma requisição de feed. Com 1 post por dia e AgeFilter de 48h, normalmente há no máximo 2 posts da marca elegíveis ao mesmo tempo, e o 2º recebe ×0.625 se aparecer no mesmo pool. Postar 3 ou 4 vezes no mesmo dia faz cada post extra competir com ×0.44 e ×0.34 para o mesmo viewer.
- [INFERÊNCIA] Esse multiplicador é aplicado depois do lift de cold-start (ver seção 6) e antes do DPP.

### Gaps
- `vm-ranker/params.rs` não é marcado como espelho de produção, e seus defaults de like e not-interested estão desatualizados. Por isso, 0.5/0.25 está **confirmado em produção até 22/09/2026**. Depois disso é provável que continue, mas não está confirmado.

---

## 5. Multiplicador fora da rede (OON)

### Takeaway
Posts de contas que o viewer não segue recebem **×0.75**. Replies e reposts de contas que o viewer segue também recebem ×0.75 (`EnableOonRescoreForInNetworkRepliesRetweets=true`). Em pedidos de tópico o fator é 0.5. Para "novos usuários" existe um fator de 0.00001, mas está desligado (threshold 0).

### Cited Findings
- [CÓDIGO] `OonWeightFactor = 0.75`, `TopicOonWeightFactor = 0.5`, `NewUserOonWeightFactor = 0.00001`, `NewUserAgeThresholdSecs = 0` e `EnableOonRescoreForInNetworkRepliesRetweets = true`. — [vm-ranker/params.rs L187-228](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs#L187-L228)
- [CÓDIGO] `oon_applies`: `in_network == Some(false)` → aplica. `Some(true)` → aplica só se a flag estiver ligada e o post for reply ou retweet. — [xai-value-model/scoring.rs L206-216](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L206-L216)
- [CÓDIGO] `scoring_context`: em `topic_request` usa `TopicOonWeightFactor`. Se o viewer tem conta mais nova que `NewUserAgeThresholdSecs` e segue ≥5 contas, usa `NewUserOonWeightFactor`. Caso contrário, `OonWeightFactor`. — [vm-ranker/scoring/value_model.rs L118-142](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/scoring/value_model.rs#L118-L142)
- [CÓDIGO] O teste `hand_computed_parity` usa `effective_oon_weight 0.75` e aplica ×0.75 a uma reply in-network ("reported_in_network_reply"). — [scoring.rs tests](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs)
- [DOC-X] "Out-of-Network Discount: posts from accounts the viewer does not follow are multiplied by a factor below 1, as are replies and reposts from accounts the viewer does follow." — [README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] Os valores estavam no espelho de produção até 22/09 (0.75 / 0.5 / true) e foram movidos para o vm-ranker em 24/09 (44d37eb).

### Inferences
- [INFERÊNCIA] Para quem não segue, um post da @ottodoti precisa ter score previsto ~33% maior (1/0.75) que um post de alguém que o viewer segue para empatar.
- [INFERÊNCIA] Reply da marca em post alheio não chega a quem não a segue (é filtrada; ver seção 8). Para seguidores, a reply chega com ×0.75 e só sob as condições do Thunder.

### Gaps
- Mesmo caso da seção 4: o valor está confirmado no espelho até 22/09/2026 e é provável, mas não confirmado, depois disso.

---

## 6. Slot de cold-start / exploração para contas pequenas ("new-author boost")

### Takeaway
Em cada requisição, no máximo **1 post** é "levantado" até o score do candidato na **16ª posição** (índice 15). Condições:
- post original (não reply, não repost; quote vale);
- autor com **≤50.000 seguidores**;
- post com **≤2h** de idade;
- **<200 views no Home**;
- post já entre os 97% melhores candidatos com score não-zero.

A escolha entre os elegíveis é por **Thompson sampling** sobre likes/views (prior Beta(0.75, 49.25)): ficam os 2 maiores sorteios e vence o de maior score do modelo. Todos os limites foram afrouxados ou mudados em 30/09/2026.

### Cited Findings
- [CÓDIGO] Parâmetros atuais:
  - `ColdStartImpressionThreshold = 200`
  - `ColdStartSlotMin = 15`, `ColdStartSlotMax = 16`
  - `ColdStartFollowerCap = 50000`
  - `ColdStartMaxPostAgeSecs = 7200`
  - `LowImpressionsMaxPositionRatio = 0.97`
  - `EnableViewerColdStart = true`
  - `EnableColdStartThompsonSampling = true`
  - `ColdStartBetaAlpha0 = 0.75`, `ColdStartBetaBeta0 = 49.25`
  - `ColdStartTsTopK = 2`
  - `ColdStartImpressionScale = 1.0`
  - [param.rs L489-562](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L489-L562)
- [CÓDIGO] `cold_start_base_eligible`: `in_reply_to_tweet_id.is_none() && retweeted_tweet_id.is_none() && author_followers_count <= follower_cap`. — [author_cold_start.rs L188-193](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs#L188-L193)
- [CÓDIGO] `apply_cold_start` também exige quatro coisas:
  - idade `<= max_post_age`;
  - `positions[i] < (0.97 × nº de candidatos com score≠0)`;
  - `view_count_on_home < 200`;
  - elegibilidade de corpus. No arm "Holdout" padrão, todos os autores são elegíveis.
  - [author_cold_start.rs L285-330](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs#L285-L330)
- [CÓDIGO] `cold_start_target`: sorteia `rank` em `slot_min..slot_max`, faixa exclusiva, ou seja, sempre 15 (16º lugar). O alvo é o score do 16º melhor candidato, e o post escolhido recebe `max(score próprio, alvo)`. — [author_cold_start.rs L216-226](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs#L216-L226)
- [CÓDIGO] `sample_reward`: `n = scale × view_count_on_home`, `x = min(fav_count, n)`, amostra de `Beta(α0 + x, β0 + (n − x))`. `pick_thompson` ordena pelos sorteios, pega os `top_k` (2) e devolve o de maior score do modelo. — [author_cold_start.rs L243-283](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs#L243-L283)
- [CÓDIGO] Teste `pick_thompson_top_k_one_prefers_uncertain_over_peaked_zero`: um post com 10.000 views e 0 likes perde para um post com 0 views, mesmo tendo score de modelo 10× maior. — [author_cold_start.rs L988-1007](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs#L988-L1007)
- [CÓDIGO] O cold-start é ignorado em pedidos de tópico (`is_topic_request`). — [author_cold_start.rs `apply_with_decisions`](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs)
- [CÓDIGO] O `vm-ranker` reaplica a decisão (`apply_cold_start_decisions`: `effective[index] = max(effective[index], ranked[rank])`) **antes** dos multiplicadores de diversidade e OON, que são calculados sobre os scores já ajustados. Depois vem o DPP. — [xai-value-model/scoring.rs L263-330](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L263-L330)
- [CÓDIGO] Histórico dos parâmetros:
  - Release de 13/08: limite de 1000 impressões, cap de 1000 seguidores, idade máxima de 24h (86400s), ratio 0.85, slot 15/16.
  - 14/08 ([c65aa17](https://github.com/xai-org/x-algorithm/commit/c65aa179db7bdd61e2c2821eac87f208a105c053)): parâmetros de Thompson adicionados, mas desligados, com TopK 5.
  - 25/08: TopK 5 → 2.
  - 17/09 ([42266f3](https://github.com/xai-org/x-algorithm/commit/42266f3e2be54d8a3c4d2228aac2e8f8d1c1f034)): idade 24h → 48h.
  - 30/09 ([77d431a](https://github.com/xai-org/x-algorithm/commit/77d431aabf409ca1c1eed9bec7e2183f7c914e23)): impressões 1000 → **200**, seguidores 1000 → **50.000**, idade 48h → **2h**, ratio 0.85 → 0.97, Thompson **ligado**, `PhoenixColdStartMaxResults` 0 → 200.
  - Fonte: `git log -p param.rs`.
- [CÓDIGO] Retrieval de cold-start no Phoenix: `PhoenixColdStartMaxResults = 200` é passado na chamada de retrieval. Os datasets `HomeCold` e `ZeroFav` viram os served types `ForYouPhoenixRetrievalCold` e `ForYouPhoenixRetrievalZeroFav`, e a métrica conta "zero_fav_retrieved". — [sources/phoenix_source.rs L120-165](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/sources/phoenix_source.rs#L120-L165); [param.rs L16-21](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L16-L21)
- [CÓDIGO] O índice de retrieval tem um processador "tail" que só indexa posts de autores com seguidores abaixo de `TAIL_MAX_AUTHOR_FOLLOWERS` (default CLI 1000) e `TAIL_MIN_FAV_COUNT` 0. — [phoenix-rankall/src/processor/sid_tail_processor.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix-rankall/src/processor/sid_tail_processor.rs); [phoenix-rankall/src/config/mod.rs L104-108](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix-rankall/src/config/mod.rs#L104-L108)
- [DOC-X] "New-Author Boost: posts from authors whose impressions are below a threshold are lifted toward a target position." — [README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] O tamanho da resposta é 35 posts (`RESULT_SIZE`), de um top-50 selecionado. — [config.rs L17-19](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/config.rs#L17-L19)

### Inferences
- [INFERÊNCIA] "Posição 16" é o **score-alvo** da 16ª posição antes dos multiplicadores. Para quem não segue a marca, o post levantado ainda leva ×0.75 depois do lift, e o DPP reordena em seguida. A posição final não é garantida; tende a ficar perto do meio da página de ~35 posts.
- [INFERÊNCIA] A janela útil é curta: as primeiras 2h, ou até 200 views no Home, o que vier antes. O sorteio favorece posts com taxa likes/views alta, ou poucas views (alta incerteza). O prior tem média 0.75/50 = 1,5% de likes por view no Home. Por exemplo, 6 likes em 100 views dá Beta(6.75, 143.25), média ~4,5%. Conseguir likes cedo, entre as primeiras views do Home, aumenta a chance de ganhar o slot.
- [INFERÊNCIA] O slot vale 1 post por requisição, e cada viewer faz várias requisições por dia, então o mesmo post pode ganhar o slot para muitos viewers diferentes. O post também precisa já ter chegado ao pool do viewer (via Thunder para seguidores, ou via retrieval Phoenix, inclusive os datasets cold/zero-fav, para não seguidores) e ter passado nos filtros.
- [INFERÊNCIA] Thread não ajuda aqui: replies não são elegíveis. Só o post raiz ou um quote compete.

### Gaps
- Como o índice `HomeCold`/`ZeroFav` do Phoenix seleciona posts não está publicado, e não achei onde o índice "tail" (<1000 seguidores) é consumido.
- Não está claro se `view_count_on_home` conta só impressões no Home ou inclui o "Seguindo". O nome sugere só Home.

---

## 7. Limites de idade do post

### Takeaway
Posts com mais de **48h** são removidos antes do ranking (`AgeFilter`). Para o slot de cold-start, o limite é 2h. Candidatos do SimClusters também têm máximo de 48h.

### Cited Findings
- [CÓDIGO] `pub const MAX_POST_AGE: u64 = 48 * 60 * 60;` e `AgeFilter::new(Duration::from_secs(params::MAX_POST_AGE))` como 3º filtro pré-score. A idade sai do snowflake do `tweet_id` (`duration_since_creation_opt`), e post sem idade calculável é removido (`unwrap_or(false)`). — [config.rs L40](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/config.rs#L40); [phoenix_candidate_pipeline.rs L400](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs#L400); [filters/age_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/age_filter.rs)
- [CÓDIGO] `SimclustersMaxCandidateAgeHours = 48` e `ColdStartMaxPostAgeSecs = 7200`. — [param.rs L634-639, L513-518](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L634-L639)
- [DOC-X] Tabela de filtros do README: "AgeFilter | Posts older than 48 hours". — [README, Filtering](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] O Phoenix usa "post age" como feature de contexto do candidato. — [phoenix/README.md L182-187](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/README.md)

### Inferences
- [INFERÊNCIA] Para o "Para você", a vida útil de um post é de no máximo 48h, com a janela de exploração concentrada nas primeiras 2h. Não use "repost reinicia o relógio" como fato: o dedup agrupa pelo id do original, e não confirmei qual id o `AgeFilter` usa para um repost (ver Gaps).

### Gaps
- Não está explícito se a idade de um candidato do tipo repost é calculada pelo id do repost ou do original (`AgeFilter` usa `c.tweet_id`).

---

## 8. Filtros relevantes: repost, dedup, quote, reply, autorrepost, conteúdo duplicado, links, mídia

### Takeaway
- Replies e reposts de contas que o viewer **não segue** são removidos (`OONRetweetReplyFilter`; replies OON do Phoenix estão desligadas).
- Reposts repetidos do mesmo post viram um só (`RetweetDeduplicationFilter`).
- Uma conversa mostra só 1 ramo, o de maior score (`DedupConversationFilter`).
- Posts já vistos ou servidos saem.
- Para links, só existe drop de URL maliciosa nas recomendações.
- Quote e reply de contas da lista eleitoral do TSE são removidos para quem não segue a conta listada.

### Cited Findings
- [CÓDIGO] Ordem dos filtros pré-score: `DropDuplicatesFilter`, `CoreDataHydrationFilter`, `AgeFilter`, `SelfTweetFilter`, `OONRetweetReplyFilter`, `OONNsfwSimclustersFilter`, `RetweetDeduplicationFilter`, `IneligibleSubscriptionFilter`, `PreviouslySeenPostsFilter`, `PreviouslySeenPostsBackupFilter`, `PreviouslyServedPostsFilter`, `ViewerMutedKeywordFilter`, `AuthorSocialgraphFilter`, `Brazil2026ElectionFilter`, `VideoFilter`, `TopicIdsFilter`, `NewUserMinEngagementFilter`, `InventoryHoldoutFilter`, `FavHoldoutFilter`. — [phoenix_candidate_pipeline.rs L397-426](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs#L397-L426)
- [CÓDIGO] `RetweetDeduplicationFilter`: `dedup_id = retweeted_tweet_id.unwrap_or(tweet_id)`. O primeiro candidato com esse id fica, os seguintes são removidos e as `retrieval_sources` são fundidas. Roda antes do score, então quem fica é o primeiro na ordem das fontes, não o de maior score. — [filters/retweet_deduplication_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/retweet_deduplication_filter.rs)
- [CÓDIGO] `DropDuplicatesFilter`: remove o mesmo `tweet_id` vindo de mais de uma fonte. — [filters/drop_duplicates_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/drop_duplicates_filter.rs)
- [CÓDIGO] `OONRetweetReplyFilter` remove:
  - candidato `in_network == Some(false)` que seja retweet;
  - candidato fora da rede que seja reply, exceto se `EnablePhoenixOonReplies` (default **false**) e for retrieval do Phoenix (opcionalmente só reply à raiz, `PhoenixOonRepliesRootOnly=false`);
  - qualquer reply com `ancestors` vazio.
  - [filters/oon_retweet_reply_filter.rs L15-27](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/oon_retweet_reply_filter.rs#L15-L27); [param.rs L73-84](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L73-L84)
- [CÓDIGO] O flag de replies OON do Phoenix foi adicionado em 03/10/2026 (b412112) e o "root only" em 13/10 (e1a0375). Ambos estão desligados por padrão. — `git log` de param.rs
- [CÓDIGO] Thunder (rede):
  - devolve até 50 posts originais, 30 replies e 100 vídeos por autor, varrendo os 500 mais recentes;
  - exclui reposts de posts do próprio viewer (`!(post.is_retweet && post.source_user_id == Some(request_user_id))`);
  - só inclui reply in-network se ela responde a um post original, ou se é reply-a-reply-do-original **dirigida a alguém que o viewer segue**.
  - [thunder/config.rs L1-12](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/thunder/config.rs); [thunder/posts/post_store.rs L338-359](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/thunder/posts/post_store.rs#L338-L359)
- [CÓDIGO] `SelfTweetFilter` remove do feed do viewer os posts do próprio viewer. — [filters/self_tweet_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/self_tweet_filter.rs)
- [CÓDIGO] `DedupConversationFilter` (pós-seleção): por conversation id (menor ancestral ou o id original), mantém só o candidato de maior `score`. — [filters/dedup_conversation_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/dedup_conversation_filter.rs)
- [CÓDIGO] Vistos e servidos: `PreviouslySeenPostsFilter` e a versão backup, mais `PreviouslyServedPostsFilter`, com `ExcludeServedTweetIdsDuration = 10` min e `ExcludeServedTweetIdsNumber = 100`. — [param.rs L990-1001](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L990-L1001); [README, Filtering](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] `Brazil2026ElectionFilter` remove o post se:
  - o autor estiver na lista (25 IDs no teste) e o viewer não seguir o autor;
  - o repost, o quote (`quoted_user_id`) ou qualquer `ancestor_users` (replies) envolver conta listada não seguida pelo viewer.
  - O comentário no código cita a obrigação legal de excluir "except in cases of paid boosting".
  - [filters/brazil_2026_election_filter.rs L84-98](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/brazil_2026_election_filter.rs#L84-L98); [phoenix_candidate_pipeline.rs L411-420](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs#L411-L420)
- [DOC-X] "as announced by X, in accordance with Brazilian electoral law, For You now runs `Brazil2026ElectionFilter`… (Account list updated October 13, 2026.)" — [README, Aug 14 update](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md) (cita [@XBR](https://x.com/XBR/status/2088341967864320507))
- [CÓDIGO] Filtros desligados por padrão:
  - `NewUserMinEngagementFilter`: para viewers novos, remove posts OON abaixo de um mínimo de engajamento. `EnableNewUserMinEngagementFilter=false`, threshold 0.
  - `InventoryHoldoutFilter`: `EnableInventoryHoldout=false`, 0%.
  - `FavHoldoutFilter`: `EnableFavHoldout=false`. Removeria uma % determinística de posts por número de likes, de 2% (>1 like) a 15% (>3000 likes).
  - [param.rs L725-760, L870-900](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L725-L760); [filters/fav_holdout_filter.rs L10-50](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/fav_holdout_filter.rs#L10-L50)
- [CÓDIGO] Visibilidade nas recomendações (`TIMELINE_HOME_RECOMMENDATIONS`): além das regras da timeline inclui, entre outras, `DO_NOT_AMPLIFY_DROP_UNDESIRABLE`, `MALICIOUS_URL_DROP_UNDESIRABLE`, `SPAM_HIGH_RECALL_DROP_UNDESIRABLE`, `BRAZIL_ELECTION_LEGAL_DROP_UNDESIRABLE`, `FOSNR_ABUSE_INSULTS_DROP_UNDESIRABLE` e rótulos de conta (`SPAM_HIGH_RECALL_USER_LABEL…`, `DO_NOT_AMPLIFY_USER_LABEL…`, `IMPERSONATION…`, `NSFW_*`). — [visibility-filtering/rules/levels.rs L60-123](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/visibility-filtering/rules/levels.rs#L60-L123)
- [DOC-X] "A further set of rules applies only when the post is a recommendation from an account the viewer does not follow… spam caught at high recall, for instance. The same post is allowed to a follower." `AncillaryVFFilter` remove posts cujo pai, quote ou repost foi dropado. — [README, Filtering](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)

### Inferences
- [INFERÊNCIA] Para alcançar quem não segue, os formatos que chegam são post original e quote. Reply e repost da marca nunca entram no "Para você" de não seguidores enquanto `EnablePhoenixOonReplies=false`.
- [INFERÊNCIA] Autorrepost tem pouco efeito: para seguidores o dedup junta original e repost, e um post já visto é removido. Para não seguidores o repost OON é filtrado.
- [INFERÊNCIA] Thread: o feed mostra só um item por conversa, o de maior score. Os demais posts da thread não somam aparições extras no "Para você".
- [INFERÊNCIA] Atenção para conteúdo de eleição: fazer quote ou reply de uma das 25 contas listadas tira o post do "Para você" de quem não segue a conta listada.

### Gaps
- A lista de URLs maliciosas e as regras completas de "Do Not Amplify" não estão todas publicadas. O README diz que "some botmaker rules" ficaram fora.

---

## 9. Componentes Grok/LLM (grox): spam em replies, limiares, entendimento de conteúdo

### Takeaway
- O `grox` pontua replies **em tempo real**. Se o autor do post respondido **ou** o autor da raiz da thread tem **>250.000 seguidores**, a reply vai para o fluxo "reply_ranking" com **Grok** (Grok 4 mini, com fallback Grok 4.1 fast).
- Se ambos têm ≤250k, vai para o fluxo "spam_comment" com **Gemma 4 26B**: um modelo específico de reply-spam quando a thread tem >125k, e o modelo genérico abaixo disso. Se a reply contém quote, usa o Grok completo.
- Score 0 aplica o rótulo `RiskyHighVizReply`, exceto para autor com user-cred ≥66, selo cinza ou usuário de teste.
- Há ainda o fluxo "coordinated_spam" para threads cuja raiz tem ≥180k seguidores.
- Para posts originais, o fluxo "banger_initial_screen" (Gemma) gera categorias de conteúdo e flags como `isHighQuality`/`isSpam`.

### Cited Findings
- [CÓDIGO] Constantes: `GROK_GEMMA_FOLLOWER_SPLIT = 250_000`, `GEMMA_REPLY_SPAM_MIN_FOLLOWERS = 125_000`, `RISKY_HIGH_VIZ_REPLY_EXEMPT_MIN_PAGE_RANK_SCORE = 66`, `GEMMA_2 = "oai-gemma4-26b-2"`, `GEMMA_REPLY_SPAM = "oai-gemma4-26b-reply-spam"`. — [grox/flows/reply_spam/constants.py L5-9](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/constants.py)
- [CÓDIGO] `TaskSpamFilter` (plano `spam_comment`) só é elegível se é reply, se o replier não é o Grok/Gork e não é o autor do post-alvo nem da raiz, e se **nenhum** dos dois (alvo e raiz) tem >250k seguidores. `TaskReplyRankingFilter` (plano `reply_ranking`) exige o oposto: alvo **ou** raiz com >250k, caso contrário pula com "low_blast_radius". — [task_filter.py L17-92, L185-240](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/task_filter.py)
- [CÓDIGO] `ReplyScorer` (reply_ranking): `model_name = "GROK"`, modelo `GROK_4_MINI_CRITICAL` com fallback `GROK_4_1_FAST_HEDGEHOG_CRITICAL`. O prompt vem do template `reply_scoring_system.j2`, que não foi publicado. — [classifier_reply_ranking.py L29-40](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/classifier_reply_ranking.py); [prompts.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/prompts.py)
- [CÓDIGO] `SimpleReplyScorer` (spam_comment): se a reply tem `quoted_post`, usa o `ReplyScorer` completo (Grok). Senão usa Gemma: o modelo reply-spam se `max(seguidores da raiz, seguidores do alvo) > 125_000`, e o genérico abaixo disso. O histograma de score vai de 0 a 3. — [classifier_simple_reply_scorer.py L33-66](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/classifier_simple_reply_scorer.py)
- [CÓDIGO] `TaskWriteReplyRankingManhattan`:
  - grava o score da reply, só se for menor que o já existente;
  - se `score == 0.0`, aplica `SafetyLabelType.RiskyHighVizReply`;
  - pula autores com `userCredScore >= 66` (ou `isHighPageRankUser`), com selo cinza ("grey badge") ou usuários de teste.
  - [task_write.py L38-80, L140-148](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/task_write.py)
- [CÓDIGO] `TaskCoordinatedSpamFilter`: exige reply com ≥2 níveis de profundidade e raiz com ≥180.000 seguidores. Pula autores high-PageRank-v2 ou com selo cinza. — [task_filter.py L95-180](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/task_filter.py)
- [CÓDIGO] O score do grox entra como feature `grox_score_x100` no modelo de ranking de **respostas da conversa** do Phoenix. — [phoenix/crates/common/xai-recsys/src/reply.rs L38, L64, L228-232](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/crates/common/xai-recsys/src/reply.rs)
- [CÓDIGO] `banger_initial_screen` (UPA):
  - Elegível para todo post que não é reply, de conta não protegida, com rate limit.
  - Um classificador Gemma (`oai-gemma4-26b-upa`) gera `ContentCategoryScore` (categorias/tópicos) e `TweetBoolMetadata` (`isHighQuality`, `isNsfw`, `isGore`, `isViolent`, `isSpam`, `isSoftNsfw`, `isAdult`).
  - Uma ação Strato pode aplicar rótulos ("grokUpaActionWithLabels").
  - [grox/flows/upa/plan_initial_banger.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/upa/plan_initial_banger.py); [upa/task_filter.py L12-48](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/upa/task_filter.py); [upa/models.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/upa/models.py); [upa/constants.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/upa/constants.py)
- [DOC-X] grox: "Classifiers for categories such as spam, adult content and violent media, plus numeric representations of a post's text and images". Os prompts do Grox (arquivos j2) estão entre o que "not currently published". — [README, Components / What's not in this repo](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)

### Inferences
- [INFERÊNCIA] A afirmação que circula ("Grok pontua replies em posts de contas >250k") está **parcialmente certa**. Acima de 250k (alvo ou raiz) é Grok. Abaixo, as replies também são pontuadas, só que por Gemma, e a reply com quote vai para o Grok mesmo em threads pequenas.
- [INFERÊNCIA] Para a @ottodoti, replies em contas grandes (>250k) passam pelo Grok. Reply genérica ou spam (score 0) leva o rótulo `RiskyHighVizReply`. Uma conta nova ou pequena dificilmente tem user-cred ≥66 para ser isenta.
- [INFERÊNCIA] Não achei no home-mixer leitura de `isHighQuality` ou de categorias do UPA para ranking. Pelo código publicado, o efeito do grox no "Para você" passa por rótulos de visibilidade, não por peso.

### Gaps
- Não está publicado como `RiskyHighVizReply` é aplicado na visibilidade. Ele aparece em regras do `abuse-enforcement-service` (testes com `SpamHighRecall` + `RiskyHighVizReply`), não em `visibility-filtering/rules`.
- Os prompts (j2) não foram publicados.
- O consumidor das anotações UPA (`isHighQuality`, categorias) não aparece no repo.

---

## 10. Premium/verificado: há peso no ranking? user-cred e sementes do PageRank

### Takeaway
Não há peso nem boost de Premium/verificado no value model ou no home-mixer. Premium aparece em dois lugares:
1. No `user-cred-v2`: as contas verificadas (azul, cinza, dourado, org e afiliado) formam o conjunto uniforme do vetor de teleporte do PageRank (50% do teleporte; os outros 50% vêm de engajamento).
2. No modelo de ranking de respostas da conversa, como feature `author_verified`.

O user-cred (0–100) serve para isenções anti-spam, como o limite ≥66 do rótulo de reply.

### Cited Findings
- [CÓDIGO] Busca por "verified/premium/is_blue" no `home-mixer` só encontra o log de anúncios (`CoreSubscriptionLevel::Premium`). Os pesos (`ValueModelWeights`) não têm termo de assinatura. — [side_effects/ads_injection_logging_side_effect.rs L162-163](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/side_effects/ads_injection_logging_side_effect.rs#L162-L163); [xai-value-model/weights.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/weights.rs)
- [CÓDIGO] `ValidUserInfo.isPremium = isBlueVerified || isGrayVerified || isGoldVerified || isVerifiedOrg || isVOAffiliate`. — [user-cred-v2/ValidUserInfo.scala L14-15](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/user-cred-v2/ValidUserInfo.scala)
- [CÓDIGO] `computeTeleportWeights`: o teleporte é `(1−β)·uniforme(premium, não "near zero") + β·engajamento`, com `engagement_teleport_beta = 0.5`. O engajamento são likes e retweets dos últimos 7 dias (`EngagementWindowDays = 7`), pesados pela massa anterior de quem engaja e excluindo pares de contas ligadas. `jump_prob = 0.2`, máximo de 50 iterações. — [UserCredV2App.scala L141-195](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/user-cred-v2/UserCredV2App.scala); [UserCredV2Config.scala L25-35](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/user-cred-v2/UserCredV2Config.scala)
- [CÓDIGO] Score: `165.2 + 7.07·ln(massa)`, limitado a [0, 100]. — [user-cred-v2/UserCredV2.scala L10-20](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/user-cred-v2/UserCredV2.scala)
- [DOC-X] "user-cred-v2/: Runs PageRank over the follow graph and engagement edges, and turns the resulting mass into a per-account score." — [README, Content Understanding](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] Usos do user-cred no código lido:
  - isenção do rótulo `RiskyHighVizReply` (≥66);
  - pular coordinated spam para high-PageRank ou selo cinza;
  - guardrail `pagerank_skipped` no `abuse-enforcement-service`.
  - [grox task_write.py L38-46](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/task_write.py); [task_filter.py L160-170](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/task_filter.py); [abuse-enforcement-service/service-lib/src/rules.rs L740-790](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/abuse-enforcement-service/service-lib/src/rules.rs)
- [CÓDIGO] O modelo de ranking de replies tem `author_verified` (categorias 1..4) como feature de posicionamento. — [phoenix/crates/common/xai-recsys/src/reply.rs L39, L65, L228](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/crates/common/xai-recsys/src/reply.rs)

### Inferences
- [INFERÊNCIA] Premium não multiplica o score no "Para você" pelo código publicado. Pode ajudar indiretamente:
  - a conta verificada recebe massa de teleporte no PageRank e tende a ter user-cred mais alto, o que pesa nas isenções anti-spam;
  - a reply de verificado pode ser ordenada de outro jeito dentro da conversa.

### Gaps
- Não confirmei se o Phoenix (For You) recebe alguma feature de verificação do **autor** do candidato. O README lista só features de perfil do viewer.

---

## 11. Links, vídeo, imagens e threads: tratamento diferenciado no código

### Takeaway
- **Links**: não há penalidade explícita de link no score. O link entra via P(abrir link)×0.2 e o modelo aprende o resto. Só a regra `MALICIOUS_URL` dropa nas recomendações. `has_url` aparece apenas num payload experimental "debias" desligado.
- **Vídeo**: VQV tem peso 0 e só vale para vídeo >10s. Abrir vídeo vale 0.02. O peso relevante de vídeo/conteúdo é tempo (`click_dwell_time` 0.4, `dwell_time` 0.006).
- **Imagem**: expandir foto vale 0.05.
- **Threads**: só 1 item por conversa no feed.

### Cited Findings
- [CÓDIGO] `OpenLinkWeight 0.2`, `PhotoExpandWeight 0.05`, `VideoOpenWeight 0.02`, `VqvWeight 0.0`, `QuotedVqvWeight 0.0`, `ContClickDwellTimeWeight 0.4`, `ContDwellTimeWeight 0.006`, `DwellWeight 0.05`, `NotDwelledWeight −0.02`, `MinVideoDurationMs 10_000`. — [param.rs L334-438, L588-593](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L334-L438)
- [CÓDIGO] `vqv_eligible`: vídeo com `min_video_duration_ms > 10_000` **e** viewer com menos de 10.000 seguidores (`MAX_FOLLOWERS_THRESHOLD = 10_000`, sobre `query.user_features.follower_count`). — [home-mixer/util/candidates_util.rs L4, L19-34](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/util/candidates_util.rs)
- [CÓDIGO] O payload "debias" para o vm-ranker inclui `has_video`, `max_video_duration_ms`, `has_photo`, `media_count`, `weighted_text_len`, `newline_count` e `has_url`, mas só é enviado se `VMRankerSendDebiasInputs` (default **false**). Na contagem de texto, a URL pesa 23 caracteres e o link de mídia anexada não conta como link externo. — [scorers/vm_ranker_debias_payload.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/vm_ranker_debias_payload.rs); [models/content_features.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/models/content_features.rs); [param.rs L477-488](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L477-L488)
- [CÓDIGO] Rótulos de treino ligados a link externo, sem peso no value model: `IsExternalLinkLongDwelled` e sessões de link `<3s/<5s/<10s/>3s…>60s`. — [phoenix/xrex/data/recsys/constants.py L86-121](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/xrex/data/recsys/constants.py)
- [CÓDIGO] `VideoFilter` e `AncestorVideoFilter` só atuam quando a requisição pede `exclude_videos`. O carrossel de vídeo está desligado (`EnableVideoCarousel=false`, posição 6 se ligado). — [filters/video_filter.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/filters/video_filter.rs); [param.rs L1053-1082](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L1053-L1082)
- [CÓDIGO] Thunder guarda até 100 posts de vídeo por autor, contra 50 originais (`MAX_VIDEO_POSTS_PER_AUTHOR = 100`). — [thunder/config.rs L5-8](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/thunder/config.rs)
- [CÓDIGO] `MALICIOUS_URL_DROP_UNDESIRABLE` está na lista `TIMELINE_HOME_RECOMMENDATIONS`. — [visibility-filtering/rules/levels.rs L111](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/visibility-filtering/rules/levels.rs#L111)
- [CÓDIGO] Threads: `DedupConversationFilter` mantém 1 por conversa. Replies não são elegíveis ao cold-start. Replies OON são filtradas. — ver seções 6 e 8
- [DOC-X] O retrieval e o ranking usam semantic IDs do embedding multimodal (texto e mídia) do post. — [phoenix/README.md L109-115](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/phoenix/README.md)

### Inferences
- [INFERÊNCIA] Não há no código publicado um "corte de alcance por link". O efeito de link é aprendido pelo modelo (ex.: o viewer não abre ou não fica no post) e, se houver, aparece via probabilidades, não via regra. Ainda vale testar com e sem link, mas o post não deve afirmar "o X penaliza link em X%".
- [INFERÊNCIA] Para vídeo, o código não premia "visualização de qualidade" (VQV peso 0). O que conta é o viewer abrir, clicar e passar tempo (`click_dwell_time` 0.4), além das ações normais.

### Gaps
- `VMRankerSendDebiasInputs=false`, e o propósito ou efeito do "debias" no vm-ranker não está no repo.

---

## 12. O que mudou em relação ao release de 2023 (twitter/the-algorithm), em resumo

### Takeaway
2023 usava o "heavy ranker" MaskNet com pesos como reply 13.5, reply engajado pelo autor 75, profile click "bom" 12, negative feedback −74 e report −369. Em 2026 o modelo é um transformer derivado do Grok-1 (Phoenix), com pesos bem diferentes:
- reply 5 (+15 entre mútuos);
- profile click 0;
- copiar link 20;
- report −234;
- sem termo de "autor responde".

O release de janeiro de 2026 não trazia os parâmetros. Os pesos só foram publicados em 13/08/2026.

### Cited Findings
- [DOC-X 2023] Pesos de 05/04/2023: fav 0.5, retweet 1.0, reply 13.5, good_profile_click 12.0, video_playback50 0.005, reply_engaged_by_author 75.0, good_click 11.0, good_click_v2 10.0, negative_feedback_v2 −74.0, report −369.0. Combinação `score = Σ peso × probabilidade`. — [twitter/the-algorithm-ml, projects/home/recap/README.md](https://raw.githubusercontent.com/twitter/the-algorithm-ml/main/projects/home/recap/README.md)
- [DOC-X] README de 20/01/2026: "We have eliminated every single hand-engineered feature and most heuristics from the system". O transformer é "ported from the Grok-1 open source release". — `git show aaa167b:README.md` ([commit aaa167b](https://github.com/xai-org/x-algorithm/commit/aaa167b3de8a674587c53545a43c90eaad360010))
- [CÓDIGO] No commit de janeiro (aaa167b, 79 arquivos), `weighted_scorer.rs`, `author_diversity_scorer.rs` e `oon_scorer.rs` importavam `crate::params`, mas o módulo `params` não estava na árvore, ou seja, os pesos não foram publicados. O release de 13/08 (47c1bcd) adicionou `param.rs` com 183 parâmetros. — `git ls-tree aaa167b`; [commit 47c1bcd](https://github.com/xai-org/x-algorithm/commit/47c1bcdadfe4911568fd6db4f8838b194325beab)
- [DOC-X] O release de 13/08/2026 adicionou parâmetros-chave (incluindo pesos), visibility filtering, os sistemas de rótulos (botmaker, scarecrow, agatha, bdsm, user-cred-v2, media-model-proxy, clip, abuse-enforcement), o código de treino do Phoenix e o SimClusters como fonte. — [README, August 13th, 2026](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)

### Inferences
- [INFERÊNCIA] Conselhos de 2023 que não valem mais no código de 2026: "reply que o autor responde = 75×", "profile click vale muito" (hoje 0) e "vídeo assistido 50%".

### Gaps
- O detalhamento de 2023 fica com outro pesquisador.

---

## 13. Declarações oficiais do X em 2026 e ressalvas

### Takeaway
O X publicou o código em 20/01/2026 (Musk prometeu atualizações a cada 4 semanas) e expandiu o repo em 13/08/2026, junto com a ferramenta "Under the Hood". O README traz ressalvas explícitas:
- pesos multiplicam probabilidades;
- defaults espelham produção via cron, mas há experimentos;
- prompts do Grox e algumas regras do botmaker não foram publicados.

### Cited Findings
- [DOC-X] @XBusiness, 13/08/2026: "Today X is taking a major step towards unprecedented transparency". O X expande o código aberto do ranking "Para você" e lança uma ferramenta que mostra rótulos que limitam visibilidade. — [Gigazine (cita o post)](https://gigazine.net/gsc_news/en/20260814-x-timeline-algorithm/); [post @XBusiness](https://x.com/XBusiness/status/2087956083813871960)
- [IMPRENSA] Sobre o Under the Hood:
  - piloto para um grupo aleatório de contas com mais de 1 ano;
  - exige ≥10 posts no mês anterior;
  - exporta um JSON, que o VP de Produto Keith Coleman (via TechCrunch) sugere entregar a uma IA junto com o repo.
  - [Gigazine](https://gigazine.net/gsc_news/en/20260814-x-timeline-algorithm/); [ProPakistani](https://propakistani.pk/2026/08/17/x-will-finally-tell-you-if-its-algorithm-is-limiting-your-reach/)
- [DOC-X] README: Under the Hood "available here" (`x.com/i/jf/under_the_hood`). Em 18/09/2026 passou a mostrar limitações por exigência legal e o país. — [README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [CÓDIGO] `EnableUnderTheHood = false` no home-mixer (default espelhado). — [param.rs L576-581](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L576-L581)
- [DOC-X] "What's not in this repo": "Grox prompts. E.g. the j2 files with the specific LLM prompts used in Grox" e "Some botmaker rules", omitidos "to reduce the risk of gaming". — [README](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [DOC-X] Ressalva sobre experimentos e defaults: o objetivo é que experimentos com ≥10% do tráfego fiquem visíveis no repo, e scripts de cron gravam os valores primários de produção no código. — [README, Experiments and Configuration](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/README.md)
- [IMPRENSA] Em 11/01/2026, Musk disse que publicaria o algoritmo em 7 dias e repetiria o release a cada 4 semanas com notas. — [IANS](https://ianslive.in/musk-to-open-new-x-algorithm-for-public-in-seven-days--20260111092623)
- [IMPRENSA] A cobertura de imprensa mistura valores de 2023 com os de 2026 e diverge sobre a completude dos pesos. — [byteiota](https://byteiota.com/x-algorithm-open-source/); [trendingtopics](https://www.trendingtopics.eu/x-open-sources-its-algorithm-and-reveals-what-it-takes-to-go-viral/)

### Inferences
- [INFERÊNCIA] O repo é atualizado quase todo dia (sync de parâmetros). Qualquer número publicado em post deve citar a data, como "pesos de 13/out/2026".

### Gaps
- Não acessei diretamente os posts no X (@XEng/@XOpenSource/@nikitabier). As citações vêm do repo e da imprensa.
- Não achei página da Central de Ajuda do X de 2026 que detalhe pesos.

---

## 14. Verificação de afirmações que circulam

### Takeaway
A maior parte está certa. Correções:
- like é **0.66** hoje, não 0.6;
- not interested é **−52.272**, não −47.52;
- o slot de cold-start é 1 por **requisição**, não por feed, e "posição 16" é o score-alvo antes do ×0.75 OON e do DPP;
- o Grok pontua replies quando o alvo **ou** a raiz tem >250k seguidores, e abaixo disso a Gemma também pontua;
- os valores de diversidade e OON estão confirmados no espelho de produção só até 22/09.

### Cited Findings
- like 0.6: **CORRIGIR para 0.66**. Era 0.6 no sync de 12/10 e virou 0.66 no sync de 13/10 (commit 17c96bf). — [param.rs L320](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L320)
- reply 5 (+15 se mútuo → 20): **CONFIRMADO**. Condição exata: post original, não reply nem repost, de autor com follow mútuo com o viewer. Esse valor de 15 vale desde 24/07 (foi 20 de 13/07 a 24/07). — [param.rs L321-327](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L321-L327); [inputs.rs L20-22](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/inputs.rs#L20-L22); [BIDIRECTIONAL_BOOST_CHANGE.md](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/docs/BIDIRECTIONAL_BOOST_CHANGE.md)
- Positivos repost 1, quote 5, share 2, DM 5, copiar link 20, seguir autor 4, profile click 0: **CONFIRMADOS**. — [param.rs L334-388](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L334-L388)
- not interested −47.52: **CORRIGIR para −52.272** (14/10). — [param.rs L414-419](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L414-L419)
- Negativos mute −58.8, block −31.2, report −234: **CONFIRMADOS**. — [param.rs L420-432](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L420-L432)
- Decay de autor 0.5 com floor 0.25 (2º 0.625×, 3º 0.44×, 4º 0.34×): **CONFIRMADO** no código do vm-ranker, ligado por padrão. Os valores exatos são 0.625, 0.4375 e 0.34375. Ressalva: confirmado no espelho de produção até 22/09/2026. — [vm-ranker/params.rs L169-186](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs#L169-L186); [scoring.rs L183-185](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/xai-value-model/scoring.rs#L183-L185)
- OON 0.75×: **CONFIRMADO**, com dois acréscimos: vale também para replies e reposts de contas seguidas, e é 0.5 em pedidos de tópico. Mesma ressalva de data. — [vm-ranker/params.rs L187-216](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/vm-ranker/params.rs#L187-L216)
- Cold-start: **CONFIRMADO com precisões**:
  - 1 lift por **requisição**;
  - alvo = score do 16º candidato (`ColdStartSlotMin 15`/`Max 16`);
  - originais (quote conta) de autores com **≤50k**, post **≤2h** (7200s), **<200** views no Home;
  - deve estar nos 97% melhores com score não-zero;
  - Thompson sampling Beta(0.75+likes, 49.25+views−likes), top-2 sorteios e desempate pelo score do modelo.
  - Esses valores valem desde 30/09/2026.
  - [param.rs L489-556](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/param.rs#L489-L556); [author_cold_start.rs](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/scorers/author_cold_start.rs)
- Posts >48h excluídos: **CONFIRMADO** (`MAX_POST_AGE = 48h`). — [config.rs L40](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/home-mixer/params/config.rs#L40)
- Grok pontua replies em posts de contas >250k: **PARCIAL**.
  - O Grok entra quando o autor do post-alvo **ou** da raiz tem >250k.
  - Abaixo disso, a Gemma 4 26B pontua (modelo de reply-spam acima de 125k), e replies com quote vão para o Grok de qualquer forma.
  - Score 0 → rótulo `RiskyHighVizReply`.
  - [constants.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/constants.py); [task_filter.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/task_filter.py); [classifier_simple_reply_scorer.py](https://github.com/xai-org/x-algorithm/blob/17c96bf346df3d62b90f1bb01830d432dba74485/grox/flows/reply_spam/classifier_simple_reply_scorer.py)

### Inferences
- [INFERÊNCIA] Sugiro que a ficha de posts diários use os números acima sempre com o rótulo "commit de 14/10/2026", porque like e not-interested mudaram duas vezes em duas semanas.

### Gaps
- Os valores de produção de diversidade e OON depois de 22/09/2026 não são verificáveis no repo, porque `vm-ranker/params.rs` não é marcado como espelho.
