#!/usr/bin/env python3
"""Renderiza um card (PNG) ou um vídeo curto (MP4) a partir de um spec JSON.

Uso:
  python3 studio/render.py specs/exemplo-card.json media/2026-10-15/card.png
  python3 studio/render.py specs/exemplo-video.json media/2026-10-15/video.mp4
  python3 studio/render.py spec.json out.mp4 --frames 0,2.5,6   # só prévias PNG dos instantes

Imprime um JSON com dimensões, duração, tamanho e avisos (texto apertado etc.).
"""
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
STAGE = (HERE / "stage.html").as_uri()


def launch(p):
    """Abre o Chromium do Playwright; na nuvem, cai para o Chromium pré-instalado em /opt/pw-browsers."""
    try:
        return p.chromium.launch()
    except Exception as first:
        for exe in sorted(glob.glob("/opt/pw-browsers/chromium*/chrome-linux*/chrome"), reverse=True) + \
                   sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell*/chrome-*/headless_shell"), reverse=True):
            try:
                return p.chromium.launch(executable_path=exe)
            except Exception:
                continue
        raise first


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)
    spec_path, out = Path(args[0]), Path(args[1])
    frames = None
    if "--frames" in args:
        frames = [float(x) for x in args[args.index("--frames") + 1].split(",")]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": 1920, "height": 1920}, device_scale_factor=1)
        page.goto(STAGE)
        info = page.evaluate("spec => window.render(spec)", spec)
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(150)
        info = page.evaluate("spec => window.render(spec)", spec)  # de novo, já com as fontes medidas
        page.set_viewport_size({"width": info["w"], "height": info["h"]})
        stage = page.locator("#stage")

        if spec.get("kind") != "video":
            page.evaluate("t => window.setTime(t)", 1e9)
            stage.screenshot(path=str(out), type="png")
        elif frames:
            for t in frames:
                page.evaluate("t => window.setTime(t)", t)
                stage.screenshot(path=str(out.with_name(f"{out.stem}-t{t:05.2f}.png")), type="png")
        else:
            fps = int(info["fps"])
            n = int(round(info["total"] * fps))
            ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
            cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "17",
                   "-profile:v", "high", "-movflags", "+faststart", "-r", str(fps), str(out)]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            for i in range(n):
                page.evaluate("t => window.setTime(t)", i / fps)
                proc.stdin.write(stage.screenshot(type="png"))
            proc.stdin.close()
            if proc.wait() != 0:
                raise SystemExit("ffmpeg falhou")
            # capa = quadro 0
            page.evaluate("t => window.setTime(t)", 0)
            stage.screenshot(path=str(out.with_suffix(".capa.png")), type="png")
        browser.close()

    result = {"out": str(out), "w": info["w"], "h": info["h"], "warnings": info["warnings"]}
    if out.exists():
        result["bytes"] = out.stat().st_size
        limit = 5 * 1024 * 1024 if out.suffix == ".png" else 512 * 1024 * 1024
        if result["bytes"] > limit:
            result["warnings"].append(f"arquivo acima do limite do X ({limit // 1024 // 1024} MB)")
    if spec.get("kind") == "video":
        result["seconds"] = round(info["total"], 2)
        if info["total"] > 15.5:
            result["warnings"].append("vídeo acima de 15 s: encurte as cenas")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
