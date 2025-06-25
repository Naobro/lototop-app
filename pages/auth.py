# auth.py
import streamlit as st
import datetime
import hashlib

def generate_password():
    """年月を元に毎月変わるパスワードを生成"""
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:6]  # 月替わりパスワード（例：先頭6桁）

def check_password():
    """認証状態をセッションで保持し、パスワードが正しいか判定"""
    
    def password_entered():
        if st.session_state["password_input"] == generate_password():
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.text_input("🔑 パスワードを入力してください", type="password", on_change=password_entered, key="password_input")
        st.warning("※正しいパスワードを入力してください")
        st.stop()