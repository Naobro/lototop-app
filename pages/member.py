import streamlit as st
import datetime
import hashlib

# ✅ ページ設定
st.set_page_config(page_title="🔐 NAOLoto 会員専用ページ", layout="wide")

st.title("🔐 NAOLoto月額サブスク 会員ページ")
st.markdown("月額会員様向けの限定ページです。以下に今月のパスワードをご入力ください。")

# ✅ 入力欄
input_password = st.text_input("🔑 パスワードを入力", type="password")

# ✅ 今月のパスワードを動的に生成（例：年月 + ハッシュの一部）
def generate_password():
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]  # 最初の10文字のみを使用

# ✅ 正解パスワード
valid_password = generate_password()

# ✅ チェック
if input_password == valid_password:
    st.success("✅ 認証成功！以下の予想ページにアクセスできます。")

    st.markdown("### 🔗 各予想ページへ")
    st.markdown("""
    **コンテンツ内容：**
    - 当選番号  
    - 直近24回の当選番号  
    - 出現傾向・パターン分析  
    - 各位の出現回数TOP5  
    - 各数字の出現回数TOP5  
    - ABC分類  
    - 基本予想  
    """)

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