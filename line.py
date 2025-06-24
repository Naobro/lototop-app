# line_notify.py

import requests
import datetime
import hashlib

# 🔐 LINEチャネル アクセストークン（長期）をここに記載
ACCESS_TOKEN = "+HMYlGC9ttjEo1MrJ8Wi4XmXpzJvss+3OpFdIn6LJhlGG26wxrzIUSPfpu7URIc8NkrEz6LR6dRW2geYSTDiVSZv3RpS/icR9OXDYokmaa/vgbcyeOLhjpZERlDWPkG77esxKwhtHFjtSkmxR6PTLQdB04t89/1O/w1cDnyilFU="

# ✅ パスワード生成（毎月変動）
def generate_password():
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]

# ✅ LINE通知を送信
def send_broadcast_message(message):
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{
            "type": "text",
            "text": message
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    print("送信ステータス:", response.status_code)
    print("レスポンス:", response.text)