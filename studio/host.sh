#!/usr/bin/env bash
# Publica arquivos no repositório e imprime a URL raw de cada um (o Otto baixa a mídia por HTTPS).
# Uso: studio/host.sh media/2026-10-15/0930.png [media/2026-10-15/1630.mp4 kb/historico.jsonl ...]
# Saída: uma linha "URL CÓDIGO_HTTP" por arquivo. Só use a URL no Otto se o código for 200.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1
remote="$(git config --get remote.origin.url)"
slug="$(echo "$remote" | sed -E 's#\.git$##' | grep -oE '[^/:]+/[^/]+$')"
branch="$(git rev-parse --abbrev-ref HEAD)"

git add -- "$@"
git -c user.name="otto-studio" -c user.email="otto-studio@users.noreply.github.com" \
  commit -q -m "mídia $(date -u +%Y-%m-%d): $(basename "$1")" -- "$@" >/dev/null 2>&1 || true

if ! git push -q origin "HEAD:$branch" 2>/dev/null; then
  # sem permissão no branch atual (ou divergiu): tenta rebase e, se não der, usa um branch só de mídia
  if ! (git pull -q --rebase origin "$branch" 2>/dev/null && git push -q origin "HEAD:$branch" 2>/dev/null); then
    branch="claude/otto-media-$(date -u +%Y%m%d)"
    git push -q origin "HEAD:refs/heads/$branch" || { echo "ERRO: push falhou" >&2; exit 1; }
  fi
fi

for f in "$@"; do
  url="https://raw.githubusercontent.com/${slug}/${branch}/${f}"
  code=000
  for i in 1 2 3 4 5 6 7 8; do
    code="$(curl -s -o /dev/null -w '%{http_code}' -I "$url" || echo 000)"
    [ "$code" = "200" ] && break
    sleep 5
  done
  echo "$url $code"
done
