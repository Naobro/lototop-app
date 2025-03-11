import streamlit as st
import importlib

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
        display_page("loto6_top")
    elif page == "ロト7ページ":
        display_page("loto7_top")
    elif page == "ミニロトページ":
        display_page("miniloto_top")
    elif page == "ナンバーズ3ページ":
        display_page("numbers3_top")
    elif page == "ナンバーズ4ページ":
        display_page("numbers4_top")

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
