# line.py

import requests
import datetime
import hashlib

# あなたの長期チャネルアクセストークン
ACCESS_TOKEN = "あなたのトークン"

# あなたの LINE User ID（Webhook.site で取得済の userId）
USER_ID = "U65332dba1dd92fae81532e458c130a63"  # ←例です。あなたのIDに必ず差し替えて

def generate_password():
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]

def send_push_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": USER_ID,
        "messages": [{
            "type": "text",
            "text": message
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    print("送信ステータス:", response.status_code)
    print("レスポンス:", response.text)