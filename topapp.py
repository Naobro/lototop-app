import streamlit as st
import importlib

# サイドバーを消す設定
st.set_page_config(page_title="AI宝くじ分析・予想サイト", layout="wide", initial_sidebar_state="collapsed")

# ヘッダー画像を表示
header_image = "header.png"  # ヘッダー画像のファイル名（ローカルにある場合）
st.image(header_image, use_column_width=True)

# サイトタイトルと紹介文
st.title("AI宝くじ分析・予想サイト")
st.markdown("""
このサイトでは、ロト6、ロト7、ミニロト、ナンバーズ3、ナンバーズ4の過去のデータを基にした分析や、AI予想を提供します。  
各ページでは、予想結果、ランキング、分析結果、過去の当選実績などを確認できます。
""")

# ページ選択用のセレクトボックスを作成
page = st.selectbox("ページを選択してください", ["ロト6", "ロト7", "ミニロト", "ナンバーズ3", "ナンバーズ4"])

# ページに応じて表示内容を変更
if page == "ロト6":
    import pages.loto6_top as loto6
    loto6.show_page()  # loto6_top.py にあるshow_page()関数を呼び出し

elif page == "ロト7":
    import pages.loto7_top as loto7
    loto7.show_page()  # loto7_top.py にあるshow_page()関数を呼び出し

elif page == "ミニロト":
    import pages.miniloto_top as miniloto
    miniloto.show_page()  # miniloto_top.py にあるshow_page()関数を呼び出し

elif page == "ナンバーズ3":
    import pages.numbers3_top as numbers3
    numbers3.show_page()  # numbers3_top.py にあるshow_page()関数を呼び出し

elif page == "ナンバーズ4":
    import pages.numbers4_top as numbers4
    numbers4.show_page()  # numbers4_top.py にあるshow_page()関数を呼び出し
