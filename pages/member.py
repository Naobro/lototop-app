# pages/member.py

import streamlit as st
import datetime
import sys
import os

# line.py をインポートするためのパス設定
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from line import generate_password, send_push_message

st.set_page_config(page_title="🔐 NAOLoto 会員専用ページ", layout="wide")
st.title("🔐 NAOLoto月額サブスク 会員ページ")
st.markdown("月額会員様向けの限定ページです。以下に今月のパスワードをご入力ください。")

# 今月のパスワード生成
valid_password = generate_password()

# 🔐 管理者用 LINE通知ボタン（あなた1人宛）
if st.sidebar.button("📩 LINEにパスワードを送信（管理者用）"):
    msg = f"🔐【NAOLoto】今月の会員パスワード：{valid_password}"
    send_push_message(msg)
    st.sidebar.success("✅ あなたのLINEに送信しました")

# 入力欄
input_password = st.text_input("🔑 パスワードを入力", type="password")

# パスワード判定
if input_password == valid_password:
    st.success("✅ 認証成功！以下の予想ページにアクセスできます。")
    st.markdown("### 🔗 各予想ページへ")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/loto6_top.py", label="🔵 ロト6")
        st.page_link("pages/loto7_top.py", label="🟣 ロト7")
    with col2:
        st.page_link("pages/miniloto_top.py", label="🟢 ミニロト")
        st.page_link("pages/numbers3_top.py", label="🟡 ナンバーズ3")
    with col3:
        st.page_link("pages/numbers4_top.py", label="🟠 ナンバーズ4")
else:
    if input_password:
        st.error("❌ パスワードが正しくありません。")