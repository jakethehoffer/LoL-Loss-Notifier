import os, json, time
import requests
from bs4 import BeautifulSoup
from telegram import Bot

FORCE_TEST_DEFEAT = True

# ── CONFIG ───────────────────────────────────────────────────────────
FRIENDS = {
    "LinguetySpaghett": "https://op.gg/summoners/na/LinguetySpaghett-YoBro?queue_type=SOLORANKED",
    "Xraydady":        "https://op.gg/summoners/na/Xraydady-9201?queue_type=SOLORANKED",
    # add more friends here as "Name": "Full-URL"
}
STATE_FILE = "last_results.json"
# ─────────────────────────────────────────────────────────────────────

# Pull your bot creds from environment variables
TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

bot = Bot(token=TOKEN)

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
    if FORCE_TEST_DEFEAT:
        return "Defeat"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    strong = soup.find("strong", text=lambda t: t in ("Victory","Defeat"))
    return strong.text.strip() if strong else None

def main():
    state = load_state()

    for name, url in FRIENDS.items():
        try:
            current = get_last_result(url)
            last    = state.get(name)

            if last and current == "Defeat" and last != "Defeat":
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"👎 {name} just lost a ranked game!"
                )

            state[name] = current
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {name}: {current}")

        except Exception as e:
            print(f"Error checking {name}: {e}")

    save_state(state)

if __name__ == "__main__":
    main()
