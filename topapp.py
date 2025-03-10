import streamlit as st
import requests

# ヘッダー画像のパス
header_image_url = "https://raw.githubusercontent.com/Naobro/lototop-app/main/header.png"

# ヘッダー画像を表示
st.image(header_image_url, use_container_width=True)

# サイトタイトルと紹介文
st.title("AI宝くじ分析・予想サイト")
st.markdown("""
このサイトでは、ロト6、ロト7、ミニロト、ナンバーズ3、ナンバーズ4の過去のデータを基にした分析や、AI予想を提供します。  
各ページでは、予想結果、ランキング、分析結果、過去の当選実績などを確認できます。
""")

import streamlit as st
import os

# サイトの紹介ページ（トップページ）
def top_page():
    st.title("AI宝くじ分析・予想サイト")
    st.write("ここにトップページの内容を表示します。")
    
    # 各ページへのリンク
    st.markdown("[ロト6ページへ](loto6_top.py)")  # ロト6ページへのリンク
    st.markdown("[ロト7ページへ](loto7_top.py)")  # ロト7ページへのリンク
    st.markdown("[ミニロトページへ](miniloto_top.py)")  # ミニロトページへのリンク
    st.markdown("[ナンバーズ3ページへ](numbers3_top.py)")  # ナンバーズ3ページへのリンク
    st.markdown("[ナンバーズ4ページへ](numbers4_top.py)")  # ナンバーズ4ページへのリンク

# ドロップダウンメニューでページを選択する
def page_selector():
    page = st.selectbox("どのページを表示しますか?", 
                        ["トップページ", "ロト6ページ", "ロト7ページ", "ミニロトページ", "ナンバーズ3ページ", "ナンバーズ4ページ"])

    if page == "トップページ":
        top_page()
    elif page == "ロト6ページ":
        st.write("ロト6予想の詳細ページへリンクします。")
        st.markdown("[ロト6ページへ](loto6_top.py)")  # `loto6_top.py`ファイルのリンク
    elif page == "ロト7ページ":
        st.write("ロト7予想の詳細ページへリンクします。")
        st.markdown("[ロト7ページへ](loto7_top.py)")  # `loto7_top.py`ファイルのリンク
    elif page == "ミニロトページ":
        st.write("ミニロト予想の詳細ページへリンクします。")
        st.markdown("[ミニロトページへ](miniloto_top.py)")  # `miniloto_top.py`ファイルのリンク
    elif page == "ナンバーズ3ページ":
        st.write("ナンバーズ3予想の詳細ページへリンクします。")
        st.markdown("[ナンバーズ3ページへ](numbers3_top.py)")  # `numbers3_top.py`ファイルのリンク
    elif page == "ナンバーズ4ページ":
        st.write("ナンバーズ4予想の詳細ページへリンクします。")
        st.markdown("[ナンバーズ4ページへ](numbers4_top.py)")  # `numbers4_top.py`ファイルのリンク

# 実行する
page_selector()

# その他のリンク
st.header("その他のセクション")
st.markdown("""
- [当選実績](#当選実績ページリンク)
- [予想と検証](#予想と検証ページリンク)
""")
