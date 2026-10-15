# otto-x-studio

Base de conhecimento e estúdio visual dos posts do [@ottodoti](https://x.com/ottodoti) no X.

Uma routine do Claude na nuvem lê este repositório toda manhã. Ela pesquisa, escreve 3 posts no Otto, gera a imagem ou o vídeo de cada um com o estúdio e agenda no Otto.

## O que tem aqui

| Pasta | Conteúdo |
|---|---|
| `kb/estudo-algoritmo-x.md` | Estudo de out/2026: o algoritmo do X (código aberto de 2026 × 2023), a ciência de difusão, casos de build in public, táticas com evidência, mitos e números que mudam |
| `kb/notas/` | As notas de pesquisa por trás do estudo, com todas as fontes |
| `kb/regras.md` | Regras editoriais da conta |
| `kb/calendario.md` | Grade de horários, pilar de cada dia e banco de ângulos |
| `kb/historico.jsonl` | Uma linha por post agendado pela routine (tema, fatos, layout), para não repetir |
| `studio/` | `stage.html` (templates na identidade do Otto), `render.py` (PNG e MP4 via Playwright + ffmpeg), `host.sh` (publica a mídia e devolve a URL) |
| `specs/` | Formato dos specs e exemplos |
| `media/AAAA-MM-DD/` | Imagens e vídeos de cada dia |

## Rodar o estúdio

```bash
python3 -m pip install playwright pillow
python3 -m playwright install chromium
python3 studio/render.py specs/exemplos/stat.json /tmp/stat.png
python3 studio/render.py specs/exemplos/video.json /tmp/video.mp4
```

Fontes: Inter Tight, JetBrains Mono e Instrument Serif (SIL Open Font License), servidas localmente de `studio/fonts/`.
