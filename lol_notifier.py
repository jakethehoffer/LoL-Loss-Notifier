#!/usr/bin/env python3
"""
LoL Loss Notifier – Cloudflare-proof version (no API key, no Selenium).
Runs fine in GitHub Actions.

Author: you
"""

import os, json, time, re, html, cloudscraper, requests

# ── Telegram credentials (set as repo secrets) ─────────────────────────
TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# ── Friends to track (slug = part of the OP.GG URL after /summoners/na/) ─
FRIENDS = {
    "LinguetySpaghett": "LinguetySpaghett-YoBro",
    "Xraydady":         "Xraydady-9201",
    "lzsanji":          "lzsanji-WNDRN",
}

STATE_FILE = "last_results.json"

# ── Cloudflare-aware scraper ───────────────────────────────────────────
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False},
    delay=5,              # seconds to wait between challenge retries
    requestTimeout=15,
)
scraper.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
})

NEXT_RE = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S
)

# ── helpers ────────────────────────────────────────────────────────────
def send_telegram(msg: str) -> None:
    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10,
    )
    resp.raise_for_status()

def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_last_result(slug: str) -> str:
    """Return 'Victory' or 'Defeat' for the player’s most recent Solo-queue game."""
    url  = f"https://www.op.gg/summoners/na/{slug}?queue_type=SOLORANKED"
    html_raw = scraper.get(url).text
    m = NEXT_RE.search(html_raw)
    if not m:
        raise RuntimeError("__NEXT_DATA__ tag not found (blocked or layout changed)")
    data = json.loads(html.unescape(m.group(1)))
    game = (data["props"]["pageProps"]["data"]["matches"]
                 ["games"]["games"][0])
    return "Victory" if game["stats"]["win"] else "Defeat"

# ── main ───────────────────────────────────────────────────────────────
def main() -> None:
    state = load_state()

    for name, slug in FRIENDS.items():
        try:
            current = get_last_result(slug)
            last    = state.get(name)

            if current == "Defeat" and current != last:
                send_telegram(f"👎  {name} just lost a ranked solo-queue game!")
                print(f"{time.strftime('%F %T')}  Alert sent for {name}")

            state[name] = current
            print(f"{time.strftime('%F %T')}  {name}: {current}")
            time.sleep(1)    # be polite to OP.GG
        except Exception as e:
            print(f"Error: {name} – {e}")

    save_state(state)

if __name__ == "__main__":
    main()
