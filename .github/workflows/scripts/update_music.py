"""Updates the music section of README.md with top tracks and recently played, from Last.fm.

Environment variables (set as GitHub repo secrets):
  LASTFM_API_KEY, LASTFM_USER
Uses only the Python standard library.
"""
import json
import os
import re
import urllib.parse
import urllib.request

API_KEY = os.environ["LASTFM_API_KEY"]
USER = os.environ["LASTFM_USER"]

README = "README.md"
START, END = "<!--MUSIC:START-->", "<!--MUSIC:END-->"
LIMIT = 5
# 7day | 1month | 3month | 6month | 12month | overall
PERIOD = "1month"
PERIOD_LABEL = {"7day": "last 7 days", "1month": "last month", "3month": "last 3 months",
                "6month": "last 6 months", "12month": "last year", "overall": "all time"}[PERIOD]
PLACEHOLDER = "2a96cbd8b46e442fc41c2b86b821562f"  # Last.fm's grey "no image" star


def lastfm(method, **params):
    query = urllib.parse.urlencode(
        {"method": method, "user": USER, "api_key": API_KEY, "format": "json", **params}
    )
    req = urllib.request.Request(
        f"https://ws.audioscrobbler.com/2.0/?{query}",
        headers={"User-Agent": "github-profile-readme-updater"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "error" in data:
        raise RuntimeError(f"Last.fm error {data['error']}: {data.get('message')}")
    return data


def as_list(x):
    return x if isinstance(x, list) else [x]


def esc(text):
    return text.replace("|", "\\|")


def top_table(tracks):
    rows = ["| # | Track | Artist | Plays |", "|:-:|:--|:--|:-:|"]
    for i, t in enumerate(tracks, 1):
        rows.append(
            f"| {i} | [{esc(t['name'])}]({t['url']}) | {esc(t['artist']['name'])} | {t['playcount']} |"
        )
    return "\n".join(rows)


def recent_table(tracks):
    rows = ["| | Track | Artist |", "|:-:|:--|:--|"]
    for t in tracks:
        imgs = [i["#text"] for i in t.get("image", []) if i.get("#text") and PLACEHOLDER not in i["#text"]]
        cover = f'<img src="{imgs[0]}" width="40" height="40"/>' if imgs else "🎵"
        live = " 🟢 *now playing*" if t.get("@attr", {}).get("nowplaying") == "true" else ""
        rows.append(
            f"| {cover} | [{esc(t['name'])}]({t['url']}){live} | {esc(t['artist']['#text'])} |"
        )
    return "\n".join(rows)


def main():
    top = as_list(lastfm("user.gettoptracks", period=PERIOD, limit=LIMIT)["toptracks"]["track"] or [])
    raw = as_list(lastfm("user.getrecenttracks", limit=20)["recenttracks"]["track"] or [])

    seen, recent = set(), []
    for t in raw:
        key = (t["name"], t["artist"]["#text"])
        if key not in seen:
            seen.add(key)
            recent.append(t)
        if len(recent) == LIMIT:
            break

    if not top and not recent:
        print("No listening data yet; leaving README unchanged")
        return

    block = (
        f"{START}\n"
        '<table>\n<tr>\n<td valign="top" width="50%">\n\n'
        f"#### 🔥 Top tracks ({PERIOD_LABEL})\n\n"
        f"{top_table(top) if top else '*Nothing scrobbled yet.*'}\n\n"
        '</td>\n<td valign="top" width="50%">\n\n'
        "#### 🕒 Recently played\n\n"
        f"{recent_table(recent) if recent else '*Nothing scrobbled yet.*'}\n\n"
        "</td>\n</tr>\n</table>\n"
        f"{END}"
    )

    with open(README, encoding="utf-8") as f:
        content = f.read()
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, content, flags=re.S)
    if new != content:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
