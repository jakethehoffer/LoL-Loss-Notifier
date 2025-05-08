import os, json, time
import requests
from bs4 import BeautifulSoup

FORCE_ALERT = False

# ── CONFIG ───────────────────────────────────────────────────────────
FRIENDS = {
    "LinguetySpaghett": "https://op.gg/summoners/na/LinguetySpaghett-YoBro?queue_type=SOLORANKED",
    "Xraydady":        "https://op.gg/summoners/na/Xraydady-9201?queue_type=SOLORANKED",
    "lzsanji":          "https://op.gg/lol/summoners/na/lzsanji-WNDRN?queue_type=SOLORANKED"
    # add more friends here as "Name": "Full-URL"
}
STATE_FILE = "last_results.json"
# ─────────────────────────────────────────────────────────────────────

# Pull your bot creds from environment variables
TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
print("DEBUG: Telegram token starts with:", TOKEN[:8], "…")
print("DEBUG: Telegram chat_id starts with:", CHAT_ID[:5])

def send_telegram_message(text):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    resp    = requests.post(url, data=payload, timeout=10)
    print("DEBUG: Telegram API response:", resp.status_code, resp.text)
    return resp.ok

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_last_result(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Find the <strong> inside the first <button class="cursor-default">
    btn_strong = soup.select_one("main button.cursor-default strong")
    if btn_strong:
        return btn_strong.get_text(strip=True)

    # 2) Fallback: look for any <strong> literally equal to 'Victory' or 'Defeat'
    strong = soup.find(
        "strong",
        string=lambda s: s and s.strip() in ("Victory", "Defeat")
    )
    if strong:
        return strong.get_text(strip=True)

    # 3) If we still didn’t find it, return None (and you’ll see an error in your logs)
    return None


def main():
    state = load_state()

    for name, url in FRIENDS.items():
        try:
            current = get_last_result(url)
            last = state.get(name)

            # ── DEBUG/TEST NOTIFICATION LOGIC ─────────────────────
            notify = False
            if FORCE_ALERT:
                notify = True
            elif last and current == "Defeat" and last != current:
                notify = True

            if notify:
                msg = f"👎 {name} just lost a ranked game!"
                print(f"DEBUG: Sending alert for {name}")
                ok = send_telegram_message(msg)
                print("DEBUG: send_telegram_message returned", ok)
            # ───────────────────────────────────────────────────────

            state[name] = current
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {name}: {current}")

        except Exception as e:
            print(f"Error checking {name}: {e}")

    save_state(state)

if __name__ == "__main__":
    main()
