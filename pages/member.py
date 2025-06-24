import streamlit as st
import datetime
import hashlib

# ✅ ページ設定
st.set_page_config(page_title="🔐 NAOLoto 会員専用ページ", layout="wide")
st.title("🔐 NAOLoto 月額サブスク 会員ページ")
st.markdown("月額会員様向けの予想ページリンク集です。パスワードを入力してください。")

# ✅ パスワード入力欄
input_password = st.text_input("🔑 パスワードを入力", type="password")

# ✅ line.py と同じパスワード生成ロジック（10桁ハッシュ）
def generate_password():
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]

correct_password = generate_password()

# ✅ 認証チェック
if input_password:
    if input_password == correct_password:
        st.success("✅ 認証成功！メンバー専用リンクを表示します。")

        st.markdown("### 🎯 各予想ページリンク")
        st.markdown("#### 🔵 [ロト6 予想ページ](https://naoloto-win.streamlit.app/loto6_top)")
        st.markdown("#### 🔵 [ロト7 予想ページ](https://naoloto-win.streamlit.app/loto7_top)")
        st.markdown("#### 🔵 [ミニロト 予想ページ](https://naoloto-win.streamlit.app/miniloto_top)")
        st.markdown("#### 🔵 [ナンバーズ4 予想ページ](https://naoloto-win.streamlit.app/numbers4_top)")
        st.markdown("#### 🔵 [ナンバーズ3 予想ページ](https://naoloto-win.streamlit.app/numbers3_top)")

        st.markdown("---")
        st.markdown("📌 予想は毎週更新予定です。当選保証はありません。参考情報としてご活用ください。")
    else:
        st.error("❌ パスワードが正しくありません。")