# pages/member.py - 緊急対応版（通知なし）

import streamlit as st
import datetime
import hashlib

# ✅ ページ設定
st.set_page_config(page_title="🔐 NAOLoto 会員専用ページ", layout="wide")

st.title("🔐 NAOLoto月額サブスク 会員ページ")
st.markdown("月額会員様向けの限定ページです。以下に今月のパスワードをご入力ください。")

# ✅ 今月のパスワード生成
def generate_password():
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]

valid_password = generate_password()

# ✅ 管理者用確認（削除可）
st.markdown(f"🛠 **今月のパスワード（確認用）**: `{valid_password}`")

# ✅ 入力欄
input_password = st.text_input("🔑 パスワードを入力", type="password")

# ✅ チェック
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