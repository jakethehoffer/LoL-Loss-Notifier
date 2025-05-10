#!/usr/bin/env python3
"""
LoL Loss Notifier – Cloudflare-proof (no API key, no Selenium)
"""

import os, json, time, re, html, cloudscraper, requests

TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

FRIENDS = {
    "LinguetySpaghett": "LinguetySpaghett-YoBro",
    "Xraydady":         "Xraydady-9201",
    "lzsanji":          "lzsanji-WNDRN",
}

STATE_FILE = "last_results.json"

# ── Cloudflare-aware scraper (remove requestTimeout) ──────────────────
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False},
    delay=5,                       # seconds to wait between challenge retries
)
scraper.request_timeout = 15       # optional global timeout
scraper.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
})

NEXT_RE = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S
)

# ── helpers ───────────────────────────────────────────────────────────
def telegram(text: str) -> None:
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=10,
    )
    r.raise_for_status()

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(s: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(s, f)

def last_result(slug: str) -> str:
    url  = f"https://www.op.gg/summoners/na/{slug}?queue_type=SOLORANKED"
    raw  = scraper.get(url).text
    match = NEXT_RE.search(raw)
    if not match:
        raise RuntimeError("__NEXT_DATA__ tag not found (blocked or layout changed)")
    data = json.loads(html.unescape(match.group(1)))
    game = (data["props"]["pageProps"]["data"]["matches"]
                 ["games"]["games"][0])
    return "Victory" if game["stats"]["win"] else "Defeat"

# ── main loop ─────────────────────────────────────────────────────────
def main() -> None:
    state = load_state()

    for name, slug in FRIENDS.items():
        try:
            current = last_result(slug)
            last    = state.get(name)

            if current == "Defeat" and current != last:
                telegram(f"👎  {name} just lost a ranked solo-queue game!")
                print(f"{time.strftime('%F %T')}  Alert sent for {name}")

            state[name] = current
            print(f"{time.strftime('%F %T')}  {name}: {current}")
            time.sleep(1)  # polite crawling
        except Exception as e:
            print(f"Error: {name} – {e}")

    save_state(state)

if __name__ == "__main__":
    main()
