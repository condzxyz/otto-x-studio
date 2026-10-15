# Formato dos specs

Um spec é um JSON que o `studio/render.py` transforma em PNG (card) ou MP4 (vídeo). Exemplos prontos em `specs/exemplos/`.

```bash
python3 studio/render.py specs/2026-10-15/card-0930.json media/2026-10-15/card-0930.png
python3 studio/render.py specs/2026-10-15/video-1630.json media/2026-10-15/video-1630.mp4
python3 studio/render.py spec.json prévia.mp4 --frames 0,3,8   # só os quadros, para conferir
```

O render imprime um JSON. Se `warnings` não vier vazio (texto apertado, transbordando ou vídeo acima de 15 s), encurte o texto e renderize de novo.

## Campos comuns

| Campo | Valores |
|---|---|
| `kind` | `card` ou `video` |
| `format` | card: `4x5` (padrão, 1080×1350), `16x9` (1600×900), `1x1` (1080×1080). O vídeo é sempre 1920×1080 |
| `theme` | `paper` (fundo claro) ou `ink` (fundo escuro) |
| `seed` | número inteiro; muda a posição dos anéis decorativos (varie) |
| `kicker` | rótulo da pílula no topo, curto ("algoritmo do x · 2026") |
| `tag` | texto pequeno no canto superior direito (data, "01/05", nome do caso) |
| `source` | fonte no rodapé. Use ` · ` entre blocos e `\n` para quebrar linha |

Marcação dentro dos textos: `*trecho*` vira itálico serifado (use 1 vez por card), `==trecho==` vira marca-texto lime, `\n` quebra linha.

## Layouts de card

- `title`: `title`, `sub`
- `stat`: `title` (rótulo pequeno acima), `value` (ex.: `"0,66"`, `"50.000"`, `"324"`; no vídeo, conta de 0 até o valor), `unit` (opcional, em itálico), `label`, `note`, `chip`
- `bars`: `title`, `items` [{`label`, `value` (número), `display` (opcional), `hi` (lime)}], `scale` (`linear`, `sqrt`, `log`), `note`. Valor negativo vira barra vermelha
- `steps`: `title`, `items` [{`t`, `d`}] (3 a 5 itens)
- `compare`: `title`, `cols` [{`head`, `title`, `items`, `win` ou `lose`}] (2 colunas), `note`
- `code`: `title`, `code` (trecho real, copiado do repositório), `start` (nº da 1ª linha), `highlight` [nºs das linhas], `path`
- `timeline`: `title`, `items` [{`when`, `what`, `d`}] (3 a 5), `note`
- `flow`: `title`, `nodes` [{`k`, `t`, `d`, `hi`}] (3 a 5), `vertical` (opcional), `note`
- `quote`: `quote` (citação literal, no idioma original), `who`, `role`
- `end` (só vídeo): `title`, `sub`. Mostra o logo grande do Otto

## Vídeo

```json
{"kind": "video", "theme": "ink", "fps": 30, "kicker": "...", "tag": "...", "source": "...",
 "scenes": [
   {"layout": "title", "dur": 2.8, "title": "...", "sub": "..."},
   {"layout": "stat", "dur": 2.5, "value": "200", "unit": "views", "label": "..."},
   {"layout": "end", "dur": 3.0, "title": "...", "sub": "..."}
 ]}
```

- Cada cena aceita os campos do layout dela. `dur` em segundos; as cenas se sobrepõem 0,4 s no crossfade.
- Total entre 11 e 15 s (3 a 5 cenas). A 1ª cena é a capa (quadro 0) e aparece pronta: ela tem que se explicar sozinha.
- Termine com `end` quando fizer sentido.
