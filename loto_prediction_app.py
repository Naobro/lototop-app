import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# 📸 ヘッダー画像の最適表示
def display_header():
    header_image = Image.open("ロト・ナンバーズ AIで予想.png")
    st.image(header_image, use_column_width=True)

# 📊 ロトデータのランキング表作成
def create_ranking_table(df, title):
    df_sorted = df.value_counts().reset_index()
    df_sorted.columns = ["数字", "出現回数"]
    df_sorted.index += 1
    st.subheader(title)
    st.table(df_sorted)

# 🧩 A・B・C・Dグループ分け
def group_display(group_dict):
    for group, numbers in group_dict.items():
        st.write(f"### {group} グループ: {', '.join(map(str, numbers))}")

# 🚀 メインアプリ
def main():
    st.set_page_config(page_title="ロト・ナンバーズ AI予想", layout="wide")
    
    display_header()
    st.title("✨ ロト・ナンバーズ AI予想サイト ✨")

    # 📂 CSVデータ読み込み
    loto6_df = pd.read_csv("data/loto6.csv")
    loto7_df = pd.read_csv("data/loto7.csv")
    mini_loto_df = pd.read_csv("data/mini_loto.csv")
    numbers3_df = pd.read_csv("data/numbers3.csv")
    numbers4_df = pd.read_csv("data/numbers4.csv")

    # 📈 ランキング表
    st.header("🔢 よく出ている数字ランキング")
    col1, col2, col3 = st.columns(3)
    with col1:
        create_ranking_table(loto6_df, "ロト6 直近24回")
    with col2:
        create_ranking_table(loto7_df, "ロト7 直近50回")
    with col3:
        create_ranking_table(mini_loto_df, "ミニロト 全回")

    # 🎯 ナンバーズランキング
    st.header("🎲 ナンバーズランキング")
    col4, col5 = st.columns(2)
    with col4:
        create_ranking_table(numbers3_df, "ナンバーズ3 直近24回")
    with col5:
        create_ranking_table(numbers4_df, "ナンバーズ4 直近50回")

    # 🧮 A・B・C・D グループ分け
    st.header("🧩 ロト6・ロト7・ミニロト 出現率グループ分け")
    group_dict = {
        "A": [15, 18, 19, 23, 9, 34, 4, 8, 11, 30],
        "B": [12, 31, 1, 22, 29, 36, 3, 13, 14],
        "C": [7, 16, 20, 25, 28, 35],
        "D": [2, 5, 6, 10, 17, 21, 24, 26, 27, 32, 33, 37]
    }
    group_display(group_dict)

    st.success("✅ サイトが正常に更新されました！ 🎉")

if __name__ == "__main__":
    main()
