# topapp.py

import streamlit as st

# サイトタイトルと紹介文
st.title("AI宝くじ分析・予想サイト")
st.markdown("""
このサイトでは、ロト6、ロト7、ミニロト、ナンバーズ3、ナンバーズ4の過去のデータを基にした分析や、AI予想を提供します。  
各ページでは、予想結果、ランキング、分析結果、過去の当選実績などを確認できます。
""")

# ページを選択するドロップダウンメニュー
def page_selector():
    page = st.selectbox("どのページを表示しますか?", 
                        ["トップページ", "ロト6ページ", "ロト7ページ", "ミニロトページ", "ナンバーズ3ページ", "ナンバーズ4ページ"])

    if page == "トップページ":
        top_page()
    elif page == "ロト6ページ":
        display_loto6_page()
    elif page == "ロト7ページ":
        display_loto7_page()
    elif page == "ミニロトページ":
        display_miniloto_page()
    elif page == "ナンバーズ3ページ":
        display_numbers3_page()
    elif page == "ナンバーズ4ページ":
        display_numbers4_page()

# 各ページに遷移するための関数
def display_loto6_page():
    st.title("ロト6 AI予想")
    st.write("ロト6予想ページの詳細内容をここに表示します。")

def display_loto7_page():
    st.title("ロト7 AI予想")
    st.write("ロト7予想ページの詳細内容をここに表示します。")

def display_miniloto_page():
    st.title("ミニロト AI予想")
    st.write("ミニロト予想ページの詳細内容をここに表示します。")

def display_numbers3_page():
    st.title("ナンバーズ3 AI予想")
    st.write("ナンバーズ3予想ページの詳細内容をここに表示します。")

def display_numbers4_page():
    st.title("ナンバーズ4 AI予想")
    st.write("ナンバーズ4予想ページの詳細内容をここに表示します。")

# トップページ
def top_page():
    st.title("AI宝くじ分析・予想サイト")
    st.write("ここにトップページの内容を表示します。")
    
    # ページリンク（Streamlit内のリンク）
    st.markdown("[ロト6ページへ](#ロト6ページ)")  # ロト6ページへのリンク
    st.markdown("[ロト7ページへ](#ロト7ページ)")  # ロト7ページへのリンク
    st.markdown("[ミニロトページへ](#ミニロトページ)")  # ミニロトページへのリンク
    st.markdown("[ナンバーズ3ページへ](#ナンバーズ3ページ)")  # ナンバーズ3ページへのリンク
    st.markdown("[ナンバーズ4ページへ](#ナンバーズ4ページ)")  # ナンバーズ4ページへのリンク

# 実行する
page_selector()
