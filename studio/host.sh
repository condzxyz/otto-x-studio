#!/usr/bin/env bash
# Publica arquivos de mídia no repositório e imprime a URL raw de cada um (o Otto baixa por HTTPS).
# Uso: studio/host.sh media/2026-10-15/card-0930.png [outro.mp4 ...]
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
branch="$(git rev-parse --abbrev-ref HEAD)"
remote="$(git config --get remote.origin.url)"
slug="$(echo "$remote" | sed -E 's#^(https://[^/]*github.com/|git@github.com:)##; s#^.*/git/##; s#\.git$##' | grep -oE '[^/]+/[^/]+$')"
git add "$@"
git -c user.name="otto-studio" -c user.email="otto-studio@users.noreply.github.com" commit -q -m "mídia $(date -u +%Y-%m-%d): $(basename "$1")" -- "$@" || true
git push -q origin "HEAD:$branch"
for f in "$@"; do
  url="https://raw.githubusercontent.com/${slug}/${branch}/${f}"
  for i in 1 2 3 4 5 6; do
    code="$(curl -s -o /dev/null -w '%{http_code}' -I "$url" || true)"
    [ "$code" = "200" ] && break
    sleep 5
  done
  echo "$url $code"
done
