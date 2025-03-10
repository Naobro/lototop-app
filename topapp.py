# topapp.py

import streamlit as st

def display_top():
    st.title("ロト予想アプリ")
    st.write("ここにTOPページの内容を表示")
    # 必要に応じてTOPページの詳細を追加

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

# サイトのリンク
st.header("各宝くじページへのリンク")
st.markdown("""
- [ロト6](loto6_top.py)
- [ロト7](loto7_top.py)
- [ミニロト（作成中）](miniloto_top.py)
- [ナンバーズ3](numbers3_top.py)
- [ナンバーズ4](numbers4_top.py)
""")

# その他のリンク
st.header("その他のセクション")
st.markdown("""
- [当選実績](#当選実績ページリンク)
- [予想と検証](#予想と検証ページリンク)
""")
