import os, json, time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

FORCE_ALERT = False

# ── CONFIG ───────────────────────────────────────────────────────────
FRIENDS = {
    "LinguetySpaghett": "https://op.gg/summoners/na/LinguetySpaghett-YoBro?queue_type=SOLORANKED",
    "Xraydady":        "https://op.gg/summoners/na/Xraydady-9201?queue_type=SOLORANKED",
    "lzsanji":          "https://op.gg/lol/summoners/na/lzsanji-WNDRN?queue_type=SOLORANKED"
    # add more friends here as "Name": "Full-URL"
}
STATE_FILE = "last_results.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

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
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Try the common op.gg “GameResult” div
    div = soup.find("div", class_="GameResult")
    if div and div.text.strip():
        return div.text.strip()

    # Fallback: look for a <strong>Victory</strong> or <strong>Defeat</strong>
    strong = soup.find("strong", text=lambda t: t in ("Victory", "Defeat"))
    if strong:
        return strong.text.strip()

    raise ValueError(f"Could not find a recent game result on {url}")


def main():
    opts = webdriver.ChromeOptions()
    # point at the Chromium binary
    opts.binary_location = "/usr/bin/chromium-browser"
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    # tell Selenium where chromedriver lives (installed by apt)
    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=opts)

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
    driver.quit()


if __name__ == "__main__":
    main()
