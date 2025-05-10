#!/usr/bin/env python3
import os, json, sys
import requests
from datetime import datetime, timezone

from opgg.v2.opgg import OPGG
from opgg.v2.params import Region        # opgg.py ≥2.0.0

# --- CONFIG ------------------------------------------------------------------
FRIENDS = {
    # "DisplayName": (Region, "gameName", "tagLine")
    "LinguetySpaghett": ("NA", "LinguetySpaghett", "YoBro"),
    "Xraydady":        ("NA", "Xraydady",        "9201"),
    "lzsanji":         ("NA", "lzsanji",         "WNDRN"),
}
STATE_FILE = "last_games.json"
FORCE_ALERT = False            # set True to test alerts unconditionally
# -----------------------------------------------------------------------------


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as fp:
        return json.load(fp)


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as fp:
        json.dump(state, fp, indent=2)


def telegram_send(text: str) -> None:
    token   = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url     = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    resp.raise_for_status()     # blow up if Telegram rejected it


def get_latest_ranked_game(account_tuple):
    region, name, tag = account_tuple
    opgg   = OPGG()                      # one client per run is enough
    summoner = opgg.get_summoner(f"{name}#{tag}", Region[region])
    last_match = summoner.matches[0]     # already sorted newest-first
    return {
        "gameId":  last_match.id,
        "isWin":   last_match.result == "Victory",
        "champ":   last_match.champion_name,
        "time":    last_match.played_at.isoformat(),
        "queue":   last_match.queue_type,
    }


def main():
    state = load_state()
    alerted = False

    for friend, acct in FRIENDS.items():
        try:
            info = get_latest_ranked_game(acct)
        except Exception as e:
            print(f"[{friend}] scrape failed: {e}", file=sys.stderr)
            continue

        prev_id = state.get(friend, {}).get("gameId")
        if info["gameId"] == prev_id and not FORCE_ALERT:
            continue                             # nothing new

        state[friend] = info                     # update cache

        if not info["isWin"]:                    # loss detected
            msg = (f"*{friend}* just **LOST** a Solo-Q game "
                   f"as {info['champ']} @ {info['time'][:19]} UTC")
            telegram_send(msg)
            alerted = True

    save_state(state)
    if alerted:
        print("Alerts sent.")
    else:
        print("No new losses.")


if __name__ == "__main__":
    main()
