# topapp.py

import streamlit as st

def display_top():
    st.title("ロト予想アプリ")
    st.write("ここにTOPページの内容を表示")
    # 必要に応じてTOPページの詳細を追加
import streamlit as st
import requests

# GitHub から Python ファイルを読み込む
url = "https://raw.githubusercontent.com/Naobro/lototop-app/main/loto6_top.py"
response = requests.get(url)

# ファイルが正しく読み込めた場合
if response.status_code == 200:
    code = response.text
    st.code(code, language='python')  # Streamlit でコードを表示
else:
    st.error("ページが見つかりません")

import streamlit as st

# ヘッダー画像のパス
header_image_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/header.png"  # 正しいURLに修正

# ヘッダー画像を表示
st.image(header_image_path, use_container_width=True)

# サイトタイトルと紹介文
st.title("AI宝くじ分析・予想サイト")
st.markdown("""
このサイトでは、ロト6、ロト7、ミニロト、ナンバーズ3、ナンバーズ4の過去のデータを基にした分析や、AI予想を提供します。  
各ページでは、予想結果、ランキング、分析結果、過去の当選実績などを確認できます。
""")

import streamlit as st

# トップページ
def top_page():
    st.title("AI宝くじ分析・予想サイト")
    st.write("ここにトップページの内容を表示します。")
    st.markdown("[ロト6ページへ](https://raw.githubusercontent.com/Naobro/lototop-app/main/loto6_top.py)")  # ロト6ページへのリンク
    st.markdown("[ロト7ページへ](https://raw.githubusercontent.com/Naobro/lototop-app/main/loto7_top.py)")  # ロト7ページへのリンク
    st.markdown("[ミニロトページへ](https://raw.githubusercontent.com/Naobro/lototop-app/main/miniloto_top.py)")  # ミニロトページへのリンク
    st.markdown("[ナンバーズ3ページへ](https://raw.githubusercontent.com/Naobro/lototop-app/main/numbers3_top.py)")  # ナンバーズ3ページへのリンク
    st.markdown("[ナンバーズ4ページへ](https://raw.githubusercontent.com/Naobro/lototop-app/main/numbers4_top.py)")  # ナンバーズ4ページへのリンク

# ページを選択するドロップダウンメニュー
def page_selector():
    page = st.selectbox("どのページを表示しますか？", 
                        ["トップページ", "ロト6ページ", "ロト7ページ", "ミニロトページ", "ナンバーズ3ページ", "ナンバーズ4ページ"])

    if page == "トップページ":
        top_page()
    elif page == "ロト6ページ":
        st.write("ロト6予想の詳細ページへリンクします。")
        st.markdown("[ロト6ページへ](https://github.com/Naobro/lototop-app/blob/main/loto6_top.py)")
    elif page == "ロト7ページ":
        st.write("ロト7予想の詳細ページへリンクします。")
        st.markdown("[ロト7ページへ](https://github.com/Naobro/lototop-app/blob/main/loto7_top.py)")
    elif page == "ミニロトページ":
        st.write("ミニロト予想の詳細ページへリンクします。")
        st.markdown("[ミニロトページへ](https://github.com/Naobro/lototop-app/blob/main/miniloto_top.py)")
    elif page == "ナンバーズ3ページ":
        st.write("ナンバーズ3予想の詳細ページへリンクします。")
        st.markdown("[ナンバーズ3ページへ](https://github.com/Naobro/lototop-app/blob/main/numbers3_top.py)")
    elif page == "ナンバーズ4ページ":
        st.write("ナンバーズ4予想の詳細ページへリンクします。")
        st.markdown("[ナンバーズ4ページへ](https://github.com/Naobro/lototop-app/blob/main/numbers4_top.py)")

# 実行する
page_selector()
# その他のリンク
st.header("その他のセクション")
st.markdown("""
- [当選実績](#当選実績ページリンク)
- [予想と検証](#予想と検証ページリンク)
""")
