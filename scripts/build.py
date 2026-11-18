#!/usr/bin/env python3
"""Build filtered EN/RU playlists and iptv-org/epg channel lists.

Reads iptv-org language playlists and the iptv-org guides API, drops
channels marked "Not 24/7" or "Geo-blocked", prefixes groups with the
language, and writes for each language:
  out/<lang>.m3u              playlist with url-tvg pointing at the guide
  build/<lang>.channels.xml   input for `npm run grab` in iptv-org/epg
"""
import json
import re
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

BASE_URL = sys.argv[1].rstrip("/")  # e.g. https://user.github.io/tvbox-iptv
LANGS = {"en": ("eng", "EN"), "ru": ("rus", "RU")}
SITE_PREFERENCE = [
    "epg.iptvx.one", "tv.mail.ru", "i.mjh.nz", "tvtv.us", "tvguide.com",
    "freeview.co.uk", "sky.com", "mytelly.co.uk", "tvpassport.com",
    "distro.tv", "ontvtonight.com",
]
EXCLUDE_GROUPS = {"Religious", "Shop"}
OUT, BUILD = Path("out"), Path("build")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tvbox-iptv"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8")


def site_rank(guide):
    s = guide["site"]
    return SITE_PREFERENCE.index(s) if s in SITE_PREFERENCE else len(SITE_PREFERENCE)


def main():
    OUT.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    guides = {}
    for g in json.loads(fetch("https://iptv-org.github.io/api/guides.json")):
        if not g.get("site_id") or g["site_id"] == "#":
            continue
        guides.setdefault((g["channel"], g["feed"]), []).append(g)
        guides.setdefault((g["channel"], None), []).append(g)

    for code, (src, label) in LANGS.items():
        lines = fetch(f"https://iptv-org.github.io/iptv/languages/{src}.m3u").splitlines()
        playlist = [f'#EXTM3U url-tvg="{BASE_URL}/{code}.xml.gz"']
        channels, seen_urls, seen_ids = [], set(), set()
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.startswith("#EXTINF"):
                i += 1
                continue
            # collect option lines (#EXTVLCOPT etc.) up to the stream URL
            j, extra = i + 1, []
            while j < len(lines) and lines[j].startswith("#"):
                extra.append(lines[j])
                j += 1
            url = lines[j].strip() if j < len(lines) else ""
            i = j + 1
            name = line.rsplit(",", 1)[-1]
            if not url or url in seen_urls or "Not 24/7" in name or "Geo-blocked" in name:
                continue
            seen_urls.add(url)
            m = re.search(r'group-title="([^"]*)"', line)
            groups = (m.group(1) if m else "") or "Undefined"
            first = groups.split(";")[0]
            if first in EXCLUDE_GROUPS:
                continue
            new_group = f'group-title="{label} · {first}"'
            line = re.sub(r'group-title="[^"]*"', new_group, line) if m else line.replace(",", f" {new_group},", 1)
            playlist += [line, *extra, url]

            m = re.search(r'tvg-id="([^"]*)"', line)
            tvg_id = m.group(1) if m else ""
            if not tvg_id or tvg_id in seen_ids:
                continue
            ch, _, feed = tvg_id.partition("@")
            cands = guides.get((ch, feed or None)) or guides.get((ch, None))
            if not cands:
                continue
            seen_ids.add(tvg_id)
            g = min(cands, key=site_rank)
            channels.append(
                f'  <channel site={quoteattr(g["site"])} site_id={quoteattr(g["site_id"])} '
                f'lang={quoteattr(g["lang"])} xmltv_id={quoteattr(tvg_id)}>{escape(name)}</channel>'
            )

        (OUT / f"{code}.m3u").write_text("\n".join(playlist) + "\n", encoding="utf-8")
        (BUILD / f"{code}.channels.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n' + "\n".join(channels) + "\n</channels>\n",
            encoding="utf-8",
        )
        print(f"{code}: {sum(l.startswith("#EXTINF") for l in playlist)} streams, {len(channels)} channels with guide")


if __name__ == "__main__":
    main()
