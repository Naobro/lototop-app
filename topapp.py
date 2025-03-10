
# topapp.py の内容
import streamlit as st

def display_top():
    st.title("ロト予想アプリ")
    st.write("ここにTOPページの内容を表示")
    # 必要に応じてTOPページの詳細を追加


import streamlit as st

def display_top():
    st.title("ロト予想アプリ")
    st.write("ここにTOPページの内容を表示")
    # さらにTOPページの詳細なコードを追加します

import streamlit as st
import os

# ヘッダー画像のパス
header_image_path = "https://raw.githubusercontent.com/Naobro/lototop-app/header.png"

# 画像ファイルが存在するか確認
if os.path.exists(header_image_path):
    st.image(header_image_path, use_container_width=True)  # use_container_widthを使用して画像を表示
else:
    st.error("ヘッダー画像が見つかりません。ファイルパスを確認してください。")


# サイトタイトルと紹介文
st.title("AI宝くじ分析・予想サイト")
st.markdown("""
このサイトでは、ロト6、ロト7、ミニロト、ナンバーズ3、ナンバーズ4の過去のデータを基にした分析や、AI予想を提供します。  
各ページでは、予想結果、ランキング、分析結果、過去の当選実績などを確認できます。
""")

# サイトのリンク
st.header("各宝くじページへのリンク")
st.markdown("""
- [ロト6](#ロト6ページリンク)
- [ロト7](#ロト7ページリンク)
- [ミニロト（作成中）](#ミニロトページリンク)
- [ナンバーズ3](#ナンバーズ3ページリンク)
- [ナンバーズ4](#ナンバーズ4ページリンク)
""")

# その他のリンク
st.header("その他のセクション")
st.markdown("""
- [当選実績](#当選実績ページリンク)
- [予想と検証](#予想と検証ページリンク)
""")