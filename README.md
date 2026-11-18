# tvbox-iptv

Daily-built English and Russian IPTV playlists with a matching TV guide,
for Kodi's PVR IPTV Simple Client (or any player that reads M3U + XMLTV).

Sources: [iptv-org/iptv](https://github.com/iptv-org/iptv) playlists and
[iptv-org/epg](https://github.com/iptv-org/epg) grabbers. Channels marked
"Not 24/7" or "Geo-blocked", and religious and shopping channels, are left out.
Groups are prefixed with the language (`EN · News`, `RU · Movies`).

| File | What |
|---|---|
| `en.m3u`, `ru.m3u` | playlists, `url-tvg` points at the guide |
| `en.xml.gz`, `ru.xml.gz` | XMLTV guide, 2 days |

Published on GitHub Pages by `.github/workflows/build.yml` every day at 00:30 UTC.
Run it by hand from the Actions tab (`workflow_dispatch`).

The playlists only link to streams that broadcasters publish openly; nothing
is hosted here.
