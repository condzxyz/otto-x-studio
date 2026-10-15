# Mídia no X (imagens e vídeo) para uma conta de marca minimalista: specs, algoritmo, evidência e design

Notas de pesquisa de 14/10/2026. Os specs foram lidos direto nas páginas oficiais nessa data (help.x.com, docs.x.com, business.x.com) e o algoritmo direto no GitHub `xai-org/x-algorithm` (commit `17c96bf`, 14/10/2026). "ADS" marca o que vale só para anúncio e "ORGÂNICO" o que vale para post normal.

---

## 1. Specs técnicos 2026 e como a mídia aparece na timeline (para o design não ser cortado)

### Takeaway
Uma imagem única com proporção entre 2:1 e 3:4 aparece inteira na timeline. Isso inclui 16:9, 1:1 e 4:5, e o composer mostra a prévia real. Para posts com várias imagens o X não documenta o recorte, e as fontes de terceiros se contradizem: vale testar no composer. Vídeo sem Premium vai até 140 s e 512 MB. Com Premium vai até 4 h e 16 GB. Vídeo roda automaticamente e mudo, e as legendas automáticas aparecem sozinhas na timeline do app. O X não documenta capa personalizada para vídeo orgânico (só para anúncio), então o quadro inicial precisa funcionar como capa.

### Cited Findings

**Imagens (ORGÂNICO)**
- Formatos aceitos: GIF, JPEG e PNG. "We DO NOT accept BMP, TIFF". Foto até 5 MB. GIF animado até 5 MB no celular e 15 MB na web. A foto é "automatically scaled" para a visualização expandida. — [help.x.com, How to post photos or GIFs (acessado 14/10/2026)](https://help.x.com/en/using-x/posting-gifs-and-pictures)
- **Regra de recorte de imagem única:** "When you Post a single photo, images with standard aspect ratios (between 2:1 and 3:4) will display in full… what you see in the Post composer is what you'll get on X." — [help.x.com, posting-gifs-and-pictures](https://help.x.com/en/using-x/posting-gifs-and-pictures)
- Histórico: desde 2018 o Twitter recortava com um algoritmo de saliência. Em maio de 2021 passou a mostrar inteiras as fotos de proporção padrão no iOS e no Android, "without the saliency algorithm crop", e lançou "a true preview of the image in the Tweet composer". — [X Engineering Blog, 19/05/2021](https://blog.x.com/engineering/en_us/topics/insights/2021/sharing-learnings-about-our-image-cropping-algorithm)
- Foto e GIF não contam no limite de caracteres. Dá para reordenar as fotos segurando e arrastando quando há 2 ou mais. — [help.x.com, posting-gifs-and-pictures](https://help.x.com/en/using-x/posting-gifs-and-pictures)
- API (docs.x.com): imagem em JPG, PNG, GIF ou WEBP, até 5 MB. GIF animado até 15 MB, resolução máxima 1280×1080, até 350 quadros e no máximo 300 milhões de pixels (largura × altura × quadros). — [docs.x.com, Media best practices (sem data na página; acessado 14/10/2026)](https://docs.x.com/x-api/media/quickstart/best-practices)
- **Grade com várias imagens: nada oficial.** Os guias de terceiros se contradizem. Uns dizem 2 imagens em 7:8 lado a lado, 3 imagens em 7:8 + dois blocos 4:7 e 4 imagens numa grade 2×2 (há quem diga 2:1 por bloco). Todos dizem que o recorte é centralizado. — [resumo de busca: posteverywhere.ai](https://posteverywhere.ai/blog/x-twitter-aspect-ratios), [postfa.st](https://postfa.st/sizes/x/posts), [viraly.io](https://viraly.io/blog/twitter-x-image-size-guide). O guia da HeyOrca (17/02/2026) fala em até 4 imagens de 5 MB cada e recomenda 1200×675 (16:9). No mesmo texto também afirma que a timeline mostra "1.91:1", o que se contradiz, e não cita nenhuma documentação do X. — [HeyOrca](https://www.heyorca.com/blog/x-twitter-media-specs-best-practices-2026)

**Vídeo (ORGÂNICO, help center)**
- Sem Premium: "videos up to 140 seconds long with a maximum file size of 512MB". Com Premium (ou planos Plus/Premium/Super/Ultra): vídeos de até 4 h, em 1080p até 2 h e em 720p entre 2 h e 4 h, com no máximo 16 GB. — [help.x.com, How to share and watch videos (acessado 14/10/2026)](https://help.x.com/en/using-x/x-videos)
- Limites de upload pela web (FAQ): resolução mínima 32×32, máxima "1920 x 1200 (and 1200 x 1900)", proporção de 1:2.39 a 2.39:1 inclusive, "Maximum frame rate: 40 fps", "Maximum bitrate: 25 Mbps". — [help.x.com, x-videos](https://help.x.com/en/using-x/x-videos)
- Autoplay: "In timelines, Moments, the Explore tab… native videos and GIFs will autoplay". Quem assiste pode desligar (celular+Wi-Fi, só Wi-Fi ou nunca). — [help.x.com, x-videos](https://help.x.com/en/using-x/x-videos)
- Legendas: "On iOS and Android, captions are shown automatically when videos are viewed in your timeline". Na web aparece um botão "CC". O texto vem de "Speech-to-text… using Microsoft Azure Cognitive Services". "Not all videos will have captions". — [help.x.com, x-videos](https://help.x.com/en/using-x/x-videos)
- Timestamps: até 50 por post e só com 1 vídeo anexado. Por enquanto só são clicáveis no iOS. — [help.x.com, x-videos](https://help.x.com/en/using-x/x-videos)
- Download: desde 25/07/2023 o vídeo pode ser baixado por assinantes Premium, a não ser que o autor desligue "Allow video to be downloaded" no composer. Essa opção não muda depois de postar. — [help.x.com, x-videos](https://help.x.com/en/using-x/x-videos)

**Vídeo (API, docs.x.com), que é o que vale para upload via ferramenta como o Otto**
- Recomendado: H264 High Profile, áudio AAC-LC (sem HE-AAC) mono ou estéreo com pelo menos 128 kbps, vídeo com pelo menos 5.000 kbps, YUV 4:2:0, varredura progressiva, sem open GOP, 30 ou 60 fps e "must be 60 FPS or less". Resoluções recomendadas: 1280×720, 720×1280 e 720×720. As dimensões precisam ficar entre 32×32 e 1280×1024. Proporção recomendada 16:9 e 1:1, sempre entre 1:3 e 3:1. — [docs.x.com, Media best practices](https://docs.x.com/x-api/media/quickstart/best-practices)
- Duração e tamanho pela API: contas comuns de 0,5 s a 20 min e até 8 GB. Premium/verificado até 125 min e 16 GB. Em DM, 140 s e 512 MB (comum) ou 10 min e 1 GB (Premium). Um post recusado pela duração devolve 403 mesmo depois do finalize. A API tem uma categoria `subtitles`, mas a página não detalha o SRT. — [docs.x.com, Media best practices](https://docs.x.com/x-api/media/quickstart/best-practices)
- **Conflito entre as fontes oficiais:** o help center diz 40 fps no máximo, a API e os anúncios dizem 60 fps. O help diz 140 s para quem não é Premium, a API diz 20 min. O help aceita 1920×1200, a API fala em "1280×1024". — [help.x.com](https://help.x.com/en/using-x/x-videos) vs. [docs.x.com](https://docs.x.com/x-api/media/quickstart/best-practices)

**Anúncios (ADS, business/help "X Ads creative specs", acessado 14/10/2026)**
- Image Ads: PNG ou JPEG, até 5 MB, e "GIFs uploaded will render as a static image". Proporções: 1:1 (1080×1080), 1.91:1 (2064×1080), 16:9 (1920×1080), 9:16 (1080×1920). As novas são 4:5 (1440×1800) e 2:3 (1080×1620). — [X Ads creative specs](https://help.x.com/en/business-and-advertising/creative-ad-specifications)
- Video Ads: MP4 ou MOV, até 1 GB ("strongly recommend… under 30 MB"). Recomenda até 15 s e aceita até 2:20. Bitrate de 6.000 a 10.000k em 1080p e de 5.000 a 8.000k em 720p. Frame rate de 29,97 ou 30 fps (aceita até 60). Logo "persistent in the upper left hand corner". Legendas ou texto na tela "strongly recommended". **Thumbnail** em PNG ou JPEG, até 5 MB e na mesma proporção do vídeo. **"Videos will loop if the video length is under 60 seconds."** — [X Ads creative specs](https://help.x.com/en/business-and-advertising/creative-ad-specifications)
- Vertical Video Ads (Immersive Media Viewer): resolução de 720×1280 a 1080×1920, 9:16 recomendado, até 60 fps, até 25 Mbps (alvo de 5 a 10 Mbps), menos de 15 s recomendado. — [X Ads creative specs](https://help.x.com/en/business-and-advertising/creative-ad-specifications)
- Amplify Pre-roll: 1:1 "will always render as square on desktop and mobile". "This and 9:16 (vertical) will take up the same amount of real estate, which is more than 16:9." Amplify Sponsorships: "if the height exceeds the width, the video will be cropped to 1:1 in the feed". — [X Ads creative specs](https://help.x.com/en/business-and-advertising/creative-ad-specifications)
- Creative best practices (ADS): "Use 16:9 or 1:1 aspect ratios for images and videos and ensure any text or imagery is easy to see on mobile". O X diz que "80% of our audience use X on their mobile devices". — [business.x.com, Creative best practices](https://business.x.com/en/advertising/creative-best-practices)

### Inferences
- Para imagem única orgânica, as proporções seguras são 16:9 (1920×1080 ou 1600×900), 1:1 (1080×1080 ou 1200×1200) e **4:5 (1080×1350)**. O 4:5 equivale a 0,8, dentro da faixa 2:1–3:4 (0,75 a 2,0), então aparece inteiro e ocupa mais altura no celular. Já 9:16 (0,5625) e 2:3 (0,667) ficam fora da faixa e devem ser recortados na imagem orgânica.
- Para vídeo, um export que respeita as três fontes oficiais ao mesmo tempo é 1920×1080 ou 1080×1080, H.264 High, yuv420p, **30 fps** (dentro do limite de 40 fps do help), AAC-LC 128k+ e 6 a 10 Mbps. Exportar a 60 fps contraria o FAQ da web. Como a API fala em "1280×1024", vale testar um upload em 1080p pelo pipeline do Otto antes de padronizar.
- Para grades de várias imagens: centralizar o conteúdo e deixar uma margem de segurança grande (~10–12% em cada lado). Para card de dado, é melhor usar **uma imagem só** e conferir no composer, que mostra a prévia real.
- Sem capa personalizada documentada no orgânico, o primeiro quadro do vídeo deve ser desenhado como capa: título legível e sem tela preta. Ou seja: quadro 0 = capa.

### Gaps
- Não achei documentação oficial de como o X recorta grades de 2, 3 ou 4 imagens no celular e no desktop em 2026. Os números de terceiros não batem entre si.
- Não consegui abrir o FAQ "Do videos automatically loop on X?" do help center, porque o acordeão não expandiu. O loop só está confirmado para ADS com menos de 60 s.
- Não confirmei se o vídeo orgânico permite escolher capa no app (iOS, Android ou web). Também não achei o limite oficial de imagens por post: "até 4" vem de terceiros.
- As páginas do help center não têm data de atualização. A data aqui é a do acesso (14/10/2026).

---

## 2. O algoritmo open-source de 2026 (xai-org/x-algorithm) e os sinais de mídia

### Takeaway
Sim, o ranking do "For You" prevê ações ligadas a mídia: photo expand, video open, video quality view (VQV), dwell, dwell time, click dwell time e video continuation. Cada uma entra numa soma ponderada. Nos **valores padrão do código**, porém, VQV e video continuation estão com peso 0. O que ganha peso real é o tempo de leitura depois do clique (`cont_click_dwell_time` 0,4) e as ações sociais: repost por link copiado 20, reply, quote e DM 5, follow 4. Os vídeos só entram no carrossel de vídeo se forem verticais. O alerta importante é que os pesos de produção podem ser sobrescritos por um arquivo de configuração que não é público.

### Cited Findings
- A fórmula é "Final Score = Σ (weight_i × P(action_i))". As ações previstas listadas: "Clicks: post · profile · link · **photo expand · video open** · quoted post". "Attention: **video quality view · dwell · dwell time · click dwell time · video continuation seconds** · profile visit seconds". "Negative: not interested · mute author · block author · report · not dwelled". — [README.md (commit 17c96bf, 14/10/2026)](https://github.com/xai-org/x-algorithm/blob/main/README.md)
- O README avisa que os pesos multiplicam a **probabilidade prevista** de o usuário fazer a ação (ou um valor contínuo previsto, como dwell time), e não contagens brutas. Por isso "1 report cancels out 468 likes" é uma leitura errada. — [README.md](https://github.com/xai-org/x-algorithm/blob/main/README.md)
- Pesos padrão em `param.rs` (commit 17c96bf, 14/10/2026). Mídia e atenção: `photo_expand` **0.05**, `video_open` **0.02**, `vqv` **0.0**, `quoted_vqv` 0.0, `react_with_video` 0.0, `dwell` **0.05**, `cont_dwell_time` **0.006**, `cont_click_dwell_time` **0.4**, `not_dwelled` **−0.02**. Para comparar: favorite 0.66, reply 5.0, retweet 1.0, quote 5.0, share 2.0, share_via_dm 5.0, share_via_copy_link 20.0, follow_author 4.0, click 0.3, open_link 0.2, profile_click 0.0, not_interested −52.272, block −31.2, mute −58.8, report −234.0. — [home-mixer/params/param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)
- `video_continuation`, `user_video_continuation` e `profile_visit_secs` estão fixos em 0.0 no `weights_for`. — [home-mixer/scorers/value_model.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/scorers/value_model.rs)
- **Elegibilidade do VQV:** o peso de VQV só vale se `vqv_eligible`. Isso exige vídeo com `min_video_duration_ms > 10_000` (`MinVideoDurationMs` padrão 10.000 ms, ou seja, **mais de 10 s**) e `query.user_features.follower_count < 10_000` (`MAX_FOLLOWERS_THRESHOLD`). Fora disso o peso de VQV vira 0. — [home-mixer/util/candidates_util.rs (commit 44d37eb, 24/09/2026)](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/util/candidates_util.rs); [xai-value-model/scoring.rs (commit e1a0375, 13/10/2026)](https://github.com/xai-org/x-algorithm/blob/main/xai-value-model/scoring.rs)
- Os pesos são lidos como "feature switches", com nome (ex.: `rust_home_mixer_vqv_weight`) e valor padrão no código. O arquivo de configuração de produção fica em `/usr/local/config/features/home-mixer/main/rust_home_mixer.yml`, que não está no repositório. — [home-mixer/params/config.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/config.rs); [param.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs)
- **Carrossel de vídeo:** só entram vídeos com `video_aspect_ratio < 1.0` (largura/altura, ou seja, vídeo vertical). O carrossel junta de 3 a 5 vídeos, ordenados pelo `video_open` previsto, com deduplicação por autor e por semantic ID e com um parâmetro de "fatigue minutes". — [home-mixer/util/video_carousel.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/util/video_carousel.rs); [home-mixer/params/config.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/config.rs) (`VIDEO_CAROUSEL_MIN_VIDEOS = 3`, `MAX = 5`)
- O `VideoFilter` tira posts com vídeo quando a requisição pede para excluir vídeo (`query.exclude_videos`). — [home-mixer/filters/video_filter.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/filters/video_filter.rs)
- Posts com mais de 48 h não entram (`MAX_POST_AGE = 48*60*60`). — [config.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/config.rs)
- Os modelos de mídia do repositório (`media-model-proxy/`, `clip/`, `grox/`) servem para classificação de segurança e embeddings: adulto, violência, símbolos de ódio, assunto e "matching against known media". — [README.md](https://github.com/xai-org/x-algorithm/blob/main/README.md)

### Inferences
- Nos valores padrão, um post com imagem ganha um termo pequeno de photo expand (0.05 × P). O que deve pesar mais é a imagem segurar a atenção (dwell e click dwell) e provocar compartilhamento, reply, quote e follow. Um card "denso mas legível", que faz a pessoa parar, abrir e mandar para alguém, combina com a fórmula. Um visual decorativo não ganha nada só por existir.
- O VQV tem peso padrão 0 e só vale para vídeo de mais de 10 s, então o código público não dá um bônus claro a vídeo em si. Se a produção usar peso de VQV acima de 0, clipes de **11–15 s** cumprem o limite de 10 s e continuam dentro dos 15 s que o X recomenda para anúncio. Isso é especulação, porque o peso real não é público.
- O critério dos 10 mil seguidores lê `query.user_features`, que parece ser o usuário que pede o feed (quem assiste), e não o autor. Pela leitura literal, o VQV só pesaria para quem assiste e tem menos de 10 mil seguidores. Isso precisa ser confirmado com mais código.
- O carrossel de vídeo é uma superfície a mais que só aceita vertical (proporção abaixo de 1.0). 16:9 e 1:1 ficam fora, e 4:5 ou 9:16 entram. Um corte vertical de um explicativo pode pegar esse espaço extra.

### Gaps
- Os pesos de produção (o arquivo `rust_home_mixer.yml`) não estão públicos. O código só mostra os valores padrão.
- Não está documentado o que é exatamente um "video quality view" (quantos segundos ou que porcentagem assistida), nem a unidade de `dwell_time` e `click_dwell_time` (presumo segundos, mas não confirmei).
- Não verifiquei se o modelo Phoenix usa embeddings da imagem no ranking (multimodal). Há `multimodal_retrieval.rs` e `xai-recsys-mm-server`, mas não li esses arquivos.

---

## 3. Evidência 2024–2026: texto × imagem × vídeo × várias imagens no X

### Takeaway
No X, o vídeo **não** tem a vantagem padrão que tem em outras redes. Nos maiores conjuntos de dados de 2024–2026, texto e imagem empatam ou ganham do vídeo em taxa de engajamento. Por impressão, imagem/GIF engaja cerca de 1,9× mais que vídeo (dados da Ordinal). Texto puro tem a média de impressões mais alta. Os estudos acadêmicos mostram que imagem aumenta os retweets em relação a texto puro. Quase nenhum estudo separa os resultados por tamanho de conta.

### Cited Findings
- **Buffer, State of Social Engagement 2026** (mais de 52 milhões de posts e mais de 200 mil contas em 7 redes, de jan/2024 a dez/2025). Mediana de engajamento no X por formato: **texto 3,56%, imagem 3,40%, vídeo 2,96%, link 2,25%**. Não há número para carrossel ou várias imagens, nem o tamanho da amostra por formato. ER = interações / seguidores. A amostra é só de usuários do Buffer. — [Buffer (resources)](https://buffer.com/resources/state-of-social-media-engagement-2026/); escopo em [Buffer (insights)](https://buffer.com/insights/state-of-social-media-engagement-2026)
- Buffer, Premium × comum (18,8 milhões de posts no X): a partir de ~jan/2025 o engajamento do Premium subiu e o das contas comuns caiu. Nos meses mais recentes, a mediana das contas comuns "reached 0%". O engajamento geral do X subiu cerca de 44% (1,96% → 2,83%), mas o próprio analista do Buffer diz que isso "likely reflect[s] changes in the user base or metric definitions". — [Buffer (resources)](https://buffer.com/resources/state-of-social-media-engagement-2026/)
- **Ordinal** (87.528 posts no X, jan/2024 a mai/2026, ER = (likes + RTs + replies + bookmarks) / impressões). Por formato (ER e impressões médias): thread 1,89% e 27.508; **imagem/GIF 0,99% e 13.053**; enquete 0,89% e 3.634; **carrossel 0,72% e 12.335**; link 0,68% e 9.573; **texto 0,67% e 46.731**; **vídeo 0,53% e 30.684**. Não informa como selecionou a amostra, não faz teste de significância e não separa por tamanho de conta. — [Ordinal](https://www.tryordinal.com/blog/twitter-analytics). Inconsistência: em outro trecho a mesma fonte dá 35.975 impressões médias para texto e 18.334 para mídia — [resumo via busca](https://www.tryordinal.com/blog/twitter-analytics)
- **Socialinsider, benchmarks 2026** (70 milhões de posts em TikTok, IG, FB e X, jan/2024 a dez/2025). ER do X por seguidor (só likes + RTs) caiu de 0,15% para 0,12%. Views por post passaram de 1.430 para 2.979. Não traz recorte por formato nem por faixa de seguidores. — [Socialinsider (16/01/2026, atualizado até o 2º tri de 2026)](https://www.socialinsider.io/blog/twitter-benchmarks/)
- **Metricool, estudo 2026** (1.123.528 posts no X de 15.116 contas). De 2024 para 2025, posts por semana +8%, impressões −5%, interações +12% e engajamento +19%. Sem recorte por formato nas partes que acessei. — [Metricool, release do estudo 2026](https://metricool.com/press-release-2026-social-media-study/) (números vindos do resumo de busca)
- **Adilo** (~3.200 posts no X de 2025): ER médio de 2,09% para posts com imagem, acima de vídeo e anúncio. Texto puro também superou vídeo. Amostra pequena e metodologia diferente. — [Adilo (via resumo de busca)](https://adilo.com/blog/?p=20988)
- **Acadêmico, Li & Xie (Journal of Marketing Research, fev/2020, vol. 57, n. 1)**: mais de 34 mil tweets sobre companhias aéreas e SUVs (Twitter e Instagram). Imagens aumentam o engajamento, e qualidade, cor, presença humana e encaixe entre imagem e texto mudam o efeito. O número "+119% de retweets" só aparece em fonte secundária e não verifiquei. O artigo ganhou o prêmio Weitz-Winer-O'Dell de 2025 e tem mais de 400 citações. — [AMA](https://www.ama.org/press-releases/yiyi-li-and-ying-xie-win-2025-weitz-winer-odell-award/); [Baylor Keller Center](https://kellercenter.hankamer.baylor.edu/news/story/2021/using-images-increase-social-media-engagement)
- **Acadêmico, Mondal et al. (Exploration of Digital Health Technologies, 28/11/2023)**: 656.992 tweets com #SciComm de 176.863 usuários, de 28/05/2020 a 28/05/2021. Texto puro teve em média 0,7 retweet e tweet com imagem 4,4 (cerca de 6,3×, "529%"). Imagem + link deu +350%, então o efeito não soma. É um estudo observacional, sem tamanho de efeito nem intervalo de confiança. — [Mondal et al. 2023](https://www.explorationpub.com/Journals/edht/Article/10115)
- O X diz, em material de anúncio, que "97% of people focus on visuals on X". — [business.x.com, Creative best practices](https://business.x.com/en/advertising/creative-best-practices)

### Inferences
- Para uma marca que posta todo dia, imagem estática bem feita parece o formato de melhor custo-benefício no X: engajamento por impressão perto do texto ou acima dele, e bem acima do vídeo. Vídeo faz sentido quando o movimento explica algo, como um processo ou uma animação de dado, e não como padrão.
- Vídeo tem engajamento por impressão baixo, mas impressões médias altas na Ordinal. Pode render alcance sem render interação. Não dá para isolar causa, porque não sabemos que contas postam vídeo.
- A separação Premium × comum no Buffer sugere que o tamanho e o tipo de conta pesam mais que o formato. O Premium deve ser tratado como uma variável à parte.

### Gaps
- Não encontrei dados de 2024–2026 de Sprout Social, Hootsuite ou Tweet Hunter com recorte por formato no X, nem tamanhos de amostra. Também não achei recorte de formato × tamanho de conta (nano, micro, macro) específico do X.
- Nenhuma fonte separa "uma imagem" de "várias imagens" além do "carrossel" da Ordinal (0,72%), e ela não define se isso é um álbum orgânico de várias imagens.
- Todos os estudos são observacionais. Nenhum é um A/B controlado de formato no X.

---

## 4. Autoplay mudo: primeiros segundos, texto na tela, duração ideal, loop

### Takeaway
Os dados próprios do X (estudo neurocientífico de 2016 e as boas práticas atuais de anúncio) apontam para o mesmo lado. **Os 3 primeiros segundos funcionam sem som.** Movimento e mensagem devem aparecer logo no começo. Texto na tela aumenta a chance de a pessoa ver o vídeo e terminar de ver. **Até 15 s** é o ideal para lembrança e conclusão. Vídeo de anúncio com menos de 60 s roda em loop.

### Cited Findings
- Estudo Twitter + Omnicom + Neuro-Insight (127 participantes de 18 a 49 anos, set/2016, 17 vídeos de marcas OMG e mais 3, 130 horas de uso):
  - "Shorter videos of 15 seconds or less are more likely than videos of 30 seconds to drive memory encoding."
  - "The first three seconds of video doesn't need audio… personal relevance and memory encoding were at the same level whether sound was on or off". Quem assiste o vídeo inteiro com som tem todas as métricas maiores, e o diálogo pesa mais que a música.
  - Um arco de história logo no início deixa o vídeo **58%** mais propenso a ser visto além de 3 s. Conteúdo do momento: +32% além de 3 s e +11% de conclusão. Pessoas nos 3 primeiros segundos: +133% de intensidade emocional.
  - "Videos with text are **11%** more likely to be viewed and generate **28%** higher completion rates."
  - O autoplay na timeline gerou memória um pouco maior que o vídeo em tela cheia. O primeiro vídeo visto na sessão teve +22% em todas as métricas.
  — [marketing.x.com, Lis Cowie, 06/06/2017](https://marketing.x.com/en/insights/how-to-create-video-with-thumb-stopping-power-on-twitter)
- Boas práticas atuais (ADS): "Keep videos under 15 seconds for higher completion rates", "Show movement in the first few seconds", "Add captions or text overlays for sound-off viewing", "Include your branding within the first 3 seconds". — [business.x.com, Creative best practices (© 2026)](https://business.x.com/en/advertising/creative-best-practices)
- A página Vertical Video Ads recomenda "Place your most important visual at the three second mark" e 15 s como duração ideal. A página X Ads 101 diz que vídeos de 6 a 15 s com legenda e marca em destaque performam melhor (via resumo de busca). — [Vertical Video Ads](https://business.x.com/en/products/vertical-video-ads); [Campaigns 101](https://business.x.com/en/help/campaign-setup/campaigns-101)
- Loop (ADS): "Videos will loop if the video length is under 60 seconds." — [X Ads creative specs](https://help.x.com/en/business-and-advertising/creative-ad-specifications)
- Legendas automáticas: aparecem sozinhas na timeline do iOS e do Android, mas nem todo vídeo tem. — [help.x.com, x-videos](https://help.x.com/en/using-x/x-videos)
- No algoritmo, VQV só vale para vídeo com mais de 10 s. Ver a seção 2. — [candidates_util.rs](https://github.com/xai-org/x-algorithm/blob/main/home-mixer/util/candidates_util.rs)

### Inferences
- Uma receita para explicativo mudo no X: **0–1 s**, a afirmação principal já escrita na tela (o quadro 0 é a capa); **1–3 s**, primeiro movimento que mostra o mecanismo; **3–12 s**, desenvolvimento com 1 ideia por tela; final que emenda no começo para o loop. Duração-alvo de **11–15 s**: passa dos 10 s do VQV e fica dentro dos 15 s do X. Legenda queimada no vídeo, sem depender da legenda automática, porque nem todo vídeo recebe.
- Parece valer mais escrever o texto como manchete do que transcrever a fala, já que a maioria vê os 3 primeiros segundos sem som.

### Gaps
- Os números do X sobre vídeo são de 2016–2017 (pesquisa de anúncio, amostra pequena e neuromarketing). Não achei estudo de 2024–2026 sobre duração ideal de explicativo orgânico no X.
- Não confirmei se o vídeo orgânico roda em loop nem até que duração.
- Não achei dado sobre a porcentagem de visualizações com som no X em 2026.

---

## 5. Princípios de design para visuais explicativos minimalistas e profissionais (sem "cara de IA")

### Takeaway
A base editorial é tinta só para o dado (Tufte), o menos design possível (Rams) e grade com tipografia objetiva alinhada à esquerda (estilo suíço). A "cara de IA" vem de escolhas padrão que convergem: Inter, Roboto, Open Sans e Lato, gradiente roxo sobre branco, fundo chapado. Para evitar, escolha uma fonte com personalidade e use com decisão, faça contraste forte de peso e tamanho, use uma cor de destaque só e uma escala tipográfica rígida. Para o X, pense primeiro na leitura no celular.

### Cited Findings
- **Tufte, data-ink ratio:** é a razão entre a tinta que mostra o dado e a tinta total do gráfico. Chartjunk é o elemento que não informa nada e distrai. Ele separa a tinta que não é dado (grades, eixos, legendas, decoração) e defende apagá-la "dentro do razoável". O "Big Duck" é o gráfico em que o estilo engole o dado. O 3D em dado 2D é uma distorção. — [data.europa.eu, Data visualisation guide](https://data.europa.eu/apps/data-visualisation-guide/chart-junk-and-data-ink-origins); [NN/g, clutter in charts](https://www.nngroup.com/articles/clutter-charts/); [síntese acadêmica](https://mikem-radicalresearch.quarto.pub/environmental-data-visualization/chartJunk.html)
- **Dieter Rams, os 10 princípios:** inovador, útil, estético, compreensível, discreto, honesto, duradouro, detalhado até o fim, ambientalmente correto e "as little design as possible" (ligado ao "less but better"). — [Vitsœ, Good design](https://vitsoe.com/us/about/good-design); [lista reproduzida](https://archive.davidairey.com/?p=1060)
- **Estilo Tipográfico Internacional (suíço):** começa pela grade, "most legible and harmonious means for structuring information". Usa layout assimétrico, sem serifa (Helvetica, Univers, Akzidenz-Grotesk), texto alinhado à esquerda com a direita irregular, foto objetiva em vez de ilustração, e preza simplicidade, clareza, legibilidade e objetividade. Ernst Keller: "the solution to the design problem should emerge from its content". Referência: Josef Müller-Brockmann. — [Wikipedia, International Typographic Style](https://en.wikipedia.org/wiki/International_Typographic_Style)
- **"Cara de IA" (Anthropic, 12/11/2025):** sem orientação, LLMs convergem para um "high-probability center" ("distributional convergence"). O texto aponta como genéricos Inter, Roboto, Open Sans, Lato, Arial e fontes do sistema, além de "purple gradients on white backgrounds" e fundo chapado. Mesmo com aviso, o modelo ainda cai em Space Grotesk. Alternativas sugeridas: JetBrains Mono e Fira Code (estética de código); Playfair Display, Crimson Pro e Newsreader (editorial); IBM Plex e Source Sans 3 (técnico); Bricolage Grotesque. Para combinar fontes: alto contraste (display com mono, serifa com geométrica), pesos extremos ("100/200 vs 800/900"), saltos de tamanho de "3x+" e "one distinctive font" usada com decisão. — [Claude blog, Improving frontend design through Skills](https://www.claude.com/blog/improving-frontend-design-through-skills)
- **Vercel Geist (sistema de referência):** a escala tipográfica é fechada e aplicada por classes (headings de 72 a 14; Label para uma linha, com o Label 14 como "Most common text style"; Copy para várias linhas, com o 14 como o mais usado e o 24/20/18 para hero e citação). Tem variantes mono (Label 14/13/12-mono, Copy 13-mono para código inline). — [vercel.com/geist/typography](https://vercel.com/geist/typography)
- **Direção do próprio X para criativos:** a imagem precisa ter "a clear connection between your imagery and your ad copy", e texto e imagem devem ser "easy to see on mobile". — [business.x.com, Creative best practices](https://business.x.com/en/advertising/creative-best-practices)
- **Evidência de imagem no X:** qualidade, cor, presença humana e encaixe entre imagem e texto mudam o engajamento (Li & Xie, JMR 2020). — [AMA](https://www.ama.org/press-releases/yiyi-li-and-ying-xie-win-2025-weitz-winer-odell-award/)
- **Contraste (WCAG 2.2):** texto normal precisa de pelo menos 4,5:1 e texto grande de 3:1 (SC 1.4.3). Elementos gráficos necessários para entender o conteúdo, como linhas e barras de gráfico, precisam de 3:1 (SC 1.4.11). — [W3C, Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html); [W3C, Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

### Inferences
Um sistema de design proposto para os cards da marca. É síntese minha a partir das fontes acima, não consenso medido.
- **Formatos:** card de dado ou diagrama em **4:5 (1080×1350)**, para ocupar mais altura no celular sem recorte, ou **16:9 (1920×1080)** para gráfico largo e trecho de código. Lista de passos em 4:5. Nunca 9:16 em imagem.
- **Grade:** 12 colunas ou um módulo de 8 px, margem de segurança de **≥ 64 px** (~6%) em 1080 de largura, título sempre no mesmo lugar, alinhado à esquerda com a direita irregular (estilo suíço).
- **Tipografia:** 1 família com personalidade mais 1 mono. Exemplos fora da lista "genérica": IBM Plex Sans + Plex Mono, Söhne/GT America (pagas), Newsreader para manchete editorial, Geist + Geist Mono, JetBrains Mono para código. No celular, o corpo fica em ≥ 32 px numa arte de 1080 e o número principal em 120–200 px, com contraste de peso forte (300 × 700+).
- **Cor:** fundo neutro quente ou quase-preto, texto ≥ 4,5:1 e **uma cor de destaque** só, usada para o dado que importa (estilo Tufte e Economist). Sem gradiente, sem 3D, sem ícone decorativo.
- **Data-ink:** tirar grade de fundo, bordas e legenda separada. Rotular direto na série, uma ideia por card, fonte do dado no rodapé em texto pequeno (credibilidade editorial).
- **Código:** trecho curto (≤ 12 linhas), mono a ≥ 28 px em 1080, destaque de sintaxe com 2 ou 3 cores no máximo.
- **Consistência diária:** o mesmo template todo dia vira assinatura reconhecível, e o que muda é só o conteúdo. Isso vai junto com a regra de variar hook e números no texto.

### Gaps
- Não achei um estudo sistemático de como as contas grandes do X apresentam cards de dado. Isso precisaria de um levantamento manual de perfis (ex.: contas de dados e finanças, Stripe, Linear, Vercel).
- Não consegui abrir o guia de erros de gráfico da The Economist ("Mistakes, we've drawn a few", Sarah Leo, 2019) porque o fetch foi bloqueado. Ele e o FT Visual Vocabulary seriam boas referências complementares.
- Não verifiquei os guias de marca da Linear, da Stripe Press nem os slides de keynote da Apple. Ficaram como referência estética sem citação direta.
- Não há evidência medida de que "evitar Inter" melhore alcance ou engajamento no X. O argumento é de percepção de marca.

---

## 6. Alt text no X: como adicionar e qual o impacto

### Takeaway
No X, o alt text é colocado **por imagem**, pelo botão "+Alt", com até **1.000 caracteres**. Não existe para vídeo. Quase ninguém usa: só 0,06% a 0,1% das imagens tinham descrição em 2019–2022. O único teste A/B público no X mostra uma pequena vantagem para posts com alt text (+5% de impressões, +15% de engajamentos), mas sem teste de significância. O código do ranking não usa alt text como sinal. O motivo principal continua sendo acessibilidade.

### Cited Findings
- Como adicionar: no iOS e no Android, toque em **"+Alt"** na imagem, escreva e toque em Done. Na web, abra a prévia da miniatura com Enter. "The limit is 1000 characters." "You can add a description to each image in a post." "Image descriptions cannot be added to videos." Depois de postar, a descrição não fica visível, mas leitores de tela têm acesso. — [help.x.com, How to make images accessible (acessado 14/10/2026)](https://help.x.com/en/using-x/picture-descriptions)
- O X lançou o selo visível "ALT" em 07/04/2022. — [Accessible Social](https://accessible-social.com/images-and-visuals/a-b-test)
- Uso: no estudo da CMU com 1,09 milhão de tweets com imagem, só 0,1% tinham descrição. Nas fotos originais, 0,06%. Mesmo quem tinha o recurso ligado só descreveu cerca de metade das imagens. — [Gleason et al., WWW 2019, "It's almost like they're trying to hide it"](https://ri.cmu.edu/?p=121342) (dados via resumo de busca). O próprio X/Twitter disse em 2022 que ".06% of images on Twitter are accessible". — [Can I Play That, 19/05/2022](https://caniplaythat.com/2022/05/19/twitter-reveals-alternative-text-statistics-06-of-images-on-twitter-are-accessible/)
- Num estudo de tweets com alto engajamento, cerca de 91% tinham imagem ou vídeo, e menos de 1% das imagens tinha alt text. — [IFIP, "Honestly I Never Really Thought About Adding a Description"](https://dl.ifip.org/hal-04331583v1)
- **Teste A/B (Accessible Social, de jun/2021 a abr/2022, posts na conta da Sprout Social):** dois tweets quase iguais por dia às 10h ET, um com alt text e outro sem, alternando a ordem a cada mês. Com alt: 370.317 impressões, 8.509 engajamentos, ER médio de 2,3%. Sem alt: 352.989 impressões, 7.400 engajamentos, 2,1%. Sem teste de significância, com uma pequena parte impulsionada e com o risco de os seguidores perceberem o teste. — [Accessible Social, A Year-Long Alt Text A/B Test](https://accessible-social.com/images-and-visuals/a-b-test)
- No repositório do algoritmo, `alt_text` só aparece em `visibility-filtering/hydration/tweet_source.rs` e `botmaker/.../FeaturesOfTweet.java`, que são sistemas de segurança e filtragem, não os scorers de ranking. — [busca de código no GitHub, xai-org/x-algorithm (14/10/2026)](https://github.com/xai-org/x-algorithm)

### Inferences
- Colocar alt text em todo card custa pouco. Um modelo para card de dado: "Gráfico: [o quê], [período]. Principal: [número e direção]. Fonte: [x]." Fica bem abaixo de 1.000 caracteres e repete o dado para leitores de tela. Em vídeo não dá para pôr alt text, então o texto do post precisa descrever o essencial, e a legenda queimada ajuda.
- O ganho de alcance medido é pequeno e não tem significância comprovada. Melhor apresentar alt text como acessibilidade e qualidade de marca, não como hack de alcance.

### Gaps
- Não achei estudo de 2024–2026 sobre o efeito de alt text em alcance no X. Também não há evidência de que o X use alt text como sinal de busca ou de ranking.
- Não confirmei se dá para pôr alt text via API (`media/metadata/create`) na versão atual da docs.x.com nem qual o limite lá. A página de best practices não fala disso. É relevante para posts agendados pelo Otto.
