# lol_notifier.py  – “no-key” version
import os, json, re, html, time, requests

HEADERS = {"User-Agent": "Mozilla/5.0 (loss-notifier)"}   # spoof a real browser
STATE_FILE = "last_results.json"
FRIENDS = {
    "LinguetySpaghett": "LinguetySpaghett-YoBro",
    "Xraydady":         "Xraydady-9201",
    "lzsanji":          "lzsanji-WNDRN",
}

TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def telegram(txt):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": txt}, timeout=10).raise_for_status()

def load():  return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}
def save(x): json.dump(x, open(STATE_FILE, "w"))

NEXT_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)

def last_result(slug):
    url  = f"https://www.op.gg/summoners/na/{slug}?queue_type=SOLORANKED"
    raw  = requests.get(url, headers=HEADERS, timeout=10).text
    blob = NEXT_RE.search(raw)
    if not blob:
        raise RuntimeError("__NEXT_DATA__ not found – layout changed?")
    data = json.loads(html.unescape(blob.group(1)))

    # Path: props → pageProps → data → matches → games → games[0]
    game = (data["props"]["pageProps"]["data"]["matches"]
                ["games"]["games"][0])
    return "Victory" if game["stats"]["win"] else "Defeat"

def main():
    state = load()
    for name, slug in FRIENDS.items():
        try:
            result = last_result(slug)
            if state.get(name) != result and result == "Defeat":
                telegram(f"👎  {name} just lost a ranked game!")
            state[name] = result
            print(time.strftime("%F %T"), name, result)
            time.sleep(1)          # polite crawl
        except Exception as e:
            print("Error:", name, e)
    save(state)

if __name__ == "__main__":
    main()
