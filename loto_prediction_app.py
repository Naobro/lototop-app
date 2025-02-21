import streamlit as st
from PIL import Image
import os
import pandas as pd

def display_header():
    """
    ✅ ヘッダー画像を表示（PC・スマホ両方に対応した最適化表示）
    """
    image_path = os.path.join(os.path.dirname(__file__), "header.png")
    header_image = Image.open(image_path)
    st.image(header_image, use_column_width=True)

def load_data(file_path):
    """
    ✅ CSVファイルからデータを読み込みDataFrameを返す
    """
    return pd.read_csv(file_path)

def display_ranking(df, title):
    """
    ✅ ランキング表を表示
    """
    st.subheader(title)
    st.dataframe(df)

def group_by_frequency(df, title):
    """
    ✅ 出現率上位からA・B・C・Dグループに分割して表示
    """
    st.subheader(title)
    total_numbers = len(df)
    group_size = total_numbers // 4
    groups = ['A', 'B', 'C', 'D']
    for i, group in enumerate(groups):
        start = i * group_size
        end = None if i == 3 else (i + 1) * group_size
        st.write(f"### グループ {group}")
        st.dataframe(df.iloc[start:end])

def main():
    """
    ✅ Streamlitアプリのメイン関数
    """
    st.set_page_config(page_title="ロト・ナンバーズ AI予想", layout="wide")
    display_header()

    st.title("ロト・ナンバーズ AI予想サイト")

    # ✅ データの読み込み
    loto6_24 = load_data("data/loto6_24.csv")
    loto6_50 = load_data("data/loto6_50.csv")
    loto6_all = load_data("data/loto6_all.csv")

    loto7_24 = load_data("data/loto7_24.csv")
    loto7_50 = load_data("data/loto7_50.csv")
    loto7_all = load_data("data/loto7_all.csv")

    mini_24 = load_data("data/mini_24.csv")
    mini_50 = load_data("data/mini_50.csv")
    mini_all = load_data("data/mini_all.csv")

    numbers3_24 = load_data("data/numbers3_24.csv")
    numbers3_50 = load_data("data/numbers3_50.csv")

    numbers4_24 = load_data("data/numbers4_24.csv")
    numbers4_50 = load_data("data/numbers4_50.csv")

    # ✅ ランキング表表示
    st.header("ロト6・ロト7・ミニロト ランキング表")
    display_ranking(loto6_24, "ロト6: 直近24回")
    display_ranking(loto6_50, "ロト6: 直近50回")
    display_ranking(loto6_all, "ロト6: 全回")

    display_ranking(loto7_24, "ロト7: 直近24回")
    display_ranking(loto7_50, "ロト7: 直近50回")
    display_ranking(loto7_all, "ロト7: 全回")

    display_ranking(mini_24, "ミニロト: 直近24回")
    display_ranking(mini_50, "ミニロト: 直近50回")
    display_ranking(mini_all, "ミニロト: 全回")

    st.header("ナンバーズ3・ナンバーズ4 ランキング表")
    display_ranking(numbers3_24, "ナンバーズ3: 直近24回")
    display_ranking(numbers3_50, "ナンバーズ3: 直近50回")

    display_ranking(numbers4_24, "ナンバーズ4: 直近24回")
    display_ranking(numbers4_50, "ナンバーズ4: 直近50回")

    # ✅ 出現率グループ分け表示
    st.header("ロト6・ロト7・ミニロト 出現率グループ分け")
    group_by_frequency(loto6_24, "ロト6: 出現率グループ (直近24回)")
    group_by_frequency(loto7_24, "ロト7: 出現率グループ (直近24回)")
    group_by_frequency(mini_24, "ミニロト: 出現率グループ (直近24回)")

if __name__ == "__main__":
    main()
