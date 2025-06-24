import requests
import datetime
import hashlib

# ✅ あなたの長期チャネルアクセストークンをここに貼り付け
ACCESS_TOKEN = "+HMYlGC9ttjEo1MrJ8Wi4XmXpzJvss+3OpFdIn6LJhlGG26wxrzIUSPfpu7URIc8NkrEz6LR6dRW2geYSTDiVSZv3RpS/icR9OXDYokmaa/vgbcyeOLhjpZERlDWPkG77esxKwhtHFjtSkmxR6PTLQdB04t89/1O/w1cDnyilFU="

# ✅ あなたのLINE User ID（Webhook.siteで取得したもの）
USER_ID = "U65332dba1dd92fae81532e458c130a63"

# ✅ 今月のパスワードを自動生成（member.pyと同一ロジック）
def generate_password():
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]  # member.pyもこれと揃える

# ✅ LINEにプッシュ送信する関数
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

# ✅ 実行時処理
if __name__ == "__main__":
    password = generate_password()
    message = f"🔐 今月のNAOLoto会員パスワード：\n{password}"
    send_push_message(message)