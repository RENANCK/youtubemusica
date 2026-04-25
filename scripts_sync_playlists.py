#!/usr/bin/env python3
"""Sincroniza os IDs de playlists do YouTube Music para blocos no player.html.

Uso:
  python3 scripts_sync_playlists.py

Requisitos:
  pip install yt-dlp
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError
except Exception:
    print(
        "Erro: pacote 'yt_dlp' não encontrado. Instale com: python3 -m pip install yt-dlp",
        file=sys.stderr,
    )
    raise

DEFAULT_PLAYLISTS = {
    "brasilidades": "https://music.youtube.com/playlist?list=PLqYo-fJmxbHl20n1YJmga6Yg27y_5tvBI",
    "erotic": "https://music.youtube.com/playlist?list=PLqYo-fJmxbHm580KDevxg_wZRXE6yBYhL",
    "pop_neon": "https://music.youtube.com/playlist?list=PLqYo-fJmxbHlMae0vYqjhmXPNFlTuZ7kK",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Atualiza blocos de playlists em player.html")
    parser.add_argument(
        "--player-html",
        type=Path,
        default=Path(__file__).resolve().parent / "player.html",
        help="Caminho do player.html que será atualizado.",
    )
    return parser.parse_args()


def fetch_video_ids(playlist_url: str) -> list[str]:
    opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "noplaylist": False,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

    entries = info.get("entries") or []
    ids: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if not entry:
            continue
        vid = entry.get("id")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        ids.append(vid)
    return ids


def render_array_block(key: str, playlist_url: str, ids: list[str], indent: str = "      ") -> str:
    lines = [
        f"{indent}{key}: [",
        f"{indent}  // Playlist origem: {playlist_url}",
    ]
    for vid in ids:
        lines.append(f'{indent}  "{vid}",')
    lines.append(f"{indent}],")
    return "\n".join(lines)


def replace_key_array(content: str, key: str, new_block: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*\[.*?^\s*\],\s*$", re.MULTILINE | re.DOTALL)
    updated, count = pattern.subn(new_block, content, count=1)
    if count != 1:
        raise ValueError(f"Não foi possível encontrar bloco único para a chave '{key}' em player.html")
    return updated


def main() -> int:
    args = parse_args()
    player_html = args.player_html

    if not player_html.exists():
        print(f"Erro: arquivo não encontrado: {player_html}", file=sys.stderr)
        return 1

    content = player_html.read_text(encoding="utf-8")

    try:
        for key, url in DEFAULT_PLAYLISTS.items():
            print(f"Extraindo IDs: {key} ...")
            ids = fetch_video_ids(url)
            print(f"  -> {len(ids)} músicas")
            new_block = render_array_block(key, url, ids)
            content = replace_key_array(content, key, new_block)
    except DownloadError as exc:
        print("Erro de rede/proxy ao acessar YouTube. Tente novamente em uma conexão sem bloqueio.", file=sys.stderr)
        print(f"Detalhe: {exc}", file=sys.stderr)
        return 2

    player_html.write_text(content, encoding="utf-8")
    print(f"Concluído: {player_html} atualizado com IDs das playlists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
