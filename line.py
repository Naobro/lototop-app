import requests
import datetime
import hashlib
import os

# ✅ 環境変数からLINEアクセストークンを取得
ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# ✅ あなたのLINE User ID
USER_ID = "U65332dba1dd92fae81532e458c130a63"

# ✅ 今月のパスワード生成
def generate_password():
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]

# ✅ LINEにプッシュ送信
def send_push_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    print("送信ステータス:", response.status_code)
    print("レスポンス:", response.text)

# ✅ 実行
if __name__ == "__main__":
    password = generate_password()
    message = f"🔐 今月のNAOLoto会員パスワード：\n{password}"
    send_push_message(message)
