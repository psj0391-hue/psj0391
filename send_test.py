import requests

TOKEN   = "8644297254:AAEELquvVCrU7g7e7IOdGC9a4GaMQohI8eU"
CHAT_ID = "7782694176"
VIDEO   = r"C:\Users\happy\Documents\GitHub\psj0391\BOTS\instagram_bot\shorts\output\reels.mp4"

with open(VIDEO, "rb") as f:
    res = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendVideo",
        data={
            "chat_id": CHAT_ID,
            "caption": "🎬 UNH 26년 1분기 실적 릴스\n인트로 → 실적 → 주가 → 사업 → 아웃트로",
            "supports_streaming": True
        },
        files={"video": f},
        timeout=60
    )
print("✅ 전송 완료!" if res.json().get("ok") else f"❌ 실패: {res.json()}")
