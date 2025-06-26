# auth.py
import streamlit as st
import datetime
import hashlib

def generate_password():
    """年月を元に毎月自動で変わるパスワードを生成（10文字）"""
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]  # ← 🔁 ここを6 → 10 に変更

def check_password():
    """パスワードを確認し、認証成功なら通過。失敗なら警告と停止。"""
    correct_password = generate_password()
    input_password = st.text_input("🔑 パスワードを入力", type="password")

    if input_password != correct_password:
        st.warning("パスワードが違います。")
        st.stop()

    st.success("✅ 認証成功しました")