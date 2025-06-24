# line.py

import requests
import datetime
import hashlib

# 🔐 LINEチャネル アクセストークン（長期）
ACCESS_TOKEN = "+HMYlGC9ttjEo1MrJ8Wi4XmXpzJvss+3OpFdIn6LJhlGG26wxrzIUSPfpu7URIc8NkrEz6LR6dRW2geYSTDiVSZv3RpS/icR9OXDYokmaa/vgbcyeOLhjpZERlDWPkG77esxKwhtHFjtSkmxR6PTLQdB04t89/1O/w1cDnyilFU="

# 🔐 あなたのLINE userId（Webhookから取得したもの）
USER_ID = "U65332dba1dd92fae81532e458c130a63"

# ✅ パスワード生成
def generate_password():
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]

# ✅ あなた1人宛に通知を送信
def send_private_message(message):
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