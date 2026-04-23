import requests
token = "8644297254:AAEELquvVCrU7g7e7IOdGC9a4GaMQohI8eU"
res = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
data = res.json()
if data.get("result"):
    for u in data["result"]:
        msg = u.get("message", {})
        chat = msg.get("chat", {})
        cid = chat.get("id")
        name = chat.get("first_name", "") + " " + chat.get("username", "")
        print(f"Chat ID: {cid}  이름: {name.strip()}")
else:
    print("메시지 없음 - 텔레그램에서 봇에게 먼저 메시지를 보내주세요")
