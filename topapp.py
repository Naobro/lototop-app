import streamlit as st
import importlib

# サイドバーを消す設定
st.set_page_config(page_title="AI宝くじ分析・予想サイト", layout="wide", initial_sidebar_state="collapsed")

# サイトタイトルと紹介文
st.title("AI宝くじ分析・予想サイト")
st.markdown("""
このサイトでは、ロト6、ロト7、ミニロト、ナンバーズ3、ナンバーズ4の過去のデータを基にした分析や、AI予想を提供します。  
各ページでは、予想結果、ランキング、分析結果、過去の当選実績などを確認できます。
""")

# メインページで選ぶリンク
def page_selector():
    # プルダウンメニューでページを選択
    page = st.selectbox("どのページを表示しますか?", 
                        ["ロト6ページ", "ロト7ページ", "ミニロトページ", "ナンバーズ3ページ", "ナンバーズ4ページ"])

    if page == "ロト6ページ":
        display_page("pages.loto6_top")  # 'pages.loto6_top' を呼び出し
    elif page == "ロト7ページ":
        display_page("pages.loto7_top")
    elif page == "ミニロトページ":
        display_page("pages.miniloto_top")
    elif page == "ナンバーズ3ページ":
        display_page("pages.numbers3_top")
    elif page == "ナンバーズ4ページ":
        display_page("pages.numbers4_top")

# 各ページに遷移するための関数
def display_page(page_name):
    try:
        # ページをインポートして表示
        page = importlib.import_module(page_name)
        page.run()  # 各ページの run() 関数を呼び出す
    except ModuleNotFoundError:
        st.error(f"{page_name} が見つかりませんでした。")

# 実行する
page_selector()


import importlib

def page_selector():
    # 必要なページを呼び出す
    page = importlib.import_module("pages.loto6_top")  # 例: ロト6ページを呼び出し
    page.run()  # ここで`run()`を呼び出す

# この部分でページを表示するコードを記述
page_selector()
import importlib

def page_selector():
    try:
        # ページモジュールを動的にインポート
        page = importlib.import_module("pages.loto6_top")  # "pages.loto6_top"が正しいか確認
        page.run()  # ページのrun()メソッドを呼び出し
    except ModuleNotFoundError as e:
        print(f"Error importing page module: {e}")
