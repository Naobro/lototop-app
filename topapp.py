import streamlit as st

# サイトタイトルと紹介文
st.title("AI宝くじ分析・予想サイト")
st.markdown("""
このサイトでは、ロト6、ロト7、ミニロト、ナンバーズ3、ナンバーズ4の過去のデータを基にした分析や、AI予想を提供します。  
各ページでは、予想結果、ランキング、分析結果、過去の当選実績などを確認できます。
""")

import streamlit as st

st.title("AI宝くじ分析・予想サイト")
st.markdown("""
このサイトでは、ロト6、ロト7、ミニロト、ナンバーズ3、ナンバーズ4の過去のデータを基にした分析や、AI予想を提供します。  
各ページでは、予想結果、ランキング、分析結果、過去の当選実績などを確認できます。
""")

page = st.selectbox("どのページを表示しますか?", 
                    ["選択してください", "ロト6", "ロト7", "ミニロト", "ナンバーズ3", "ナンバーズ4"])

if page == "ロト6":
    st.switch_page("pages/loto6_top.py")
elif page == "ロト7":
    st.switch_page("pages/loto7_top.py")
elif page == "ミニロト":
    st.switch_page("pages/miniloto_top.py")
elif page == "ナンバーズ3":
    st.switch_page("pages/numbers3_top.py")
elif page == "ナンバーズ4":
    st.switch_page("pages/numbers4_top.py")
def display_numbers3_page():
    st.title("ナンバーズ3 AI予想")
    st.write("ナンバーズ3予想ページの詳細内容をここに表示します。")

def display_numbers4_page():
    st.title("ナンバーズ4 AI予想")
    st.write("ナンバーズ4予想ページの詳細内容をここに表示します。")

# 実行する
page_selector()