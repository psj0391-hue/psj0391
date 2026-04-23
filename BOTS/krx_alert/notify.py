import os
import sys
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def send(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print("[WARN] 텔레그램 토큰/채팅ID 미설정")
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
