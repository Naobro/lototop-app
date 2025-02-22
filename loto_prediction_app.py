import streamlit as st
import pandas as pd
import os
from PIL import Image

# ✅ データ読み込み関数
def load_data(filename):
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(data_folder, filename)
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding='cp932')
    else:
        st.error(f"❌ データファイルが見つかりません: {file_path}")
        return None

# ✅ ヘッダー画像表示関数
def display_header():
    image_path = os.path.join(os.path.dirname(__file__), "header.png")
    if os.path.exists(image_path):
        header_image = Image.open(image_path)
        st.image(header_image, use_container_width=True)
    else:
        st.warning(f"⚠️ ヘッダー画像が見つかりません: {image_path}")

# ✅ ランキングテーブル表示
def display_ranking(df):
    st.dataframe(df)

# ✅ 分布分析関数
def display_distribution(df, lottery_type):
    distribution = {}
    ranges = {
        "ロト6": [(1, 9), (10, 19), (20, 29), (30, 43)],
        "ロト7": [(1, 9), (10, 19), (20, 29), (30, 37)],
        "ミニロト": [(1, 9), (10, 19), (20, 31)]
    }
    
    if lottery_type in ranges:
        for start, end in ranges[lottery_type]:
            count = df.apply(lambda row: sum(start <= num <= end for num in row), axis=1).sum()
            distribution[f"{start}-{end}"] = count
        st.write("### 📊 分布分析")
        st.json(distribution)

# ✅ ページごとのコンテンツ表示
def display_page(lottery_name, filename):
    st.header(f"🎯 {lottery_name} 分析ページ")
    df = load_data(filename)

    if df is not None:
        if st.toggle("📅 前回の当選番号を表示"):
            st.write(df.iloc[-1])

        if st.toggle("📅 直近24回の当選番号を表示"):
            st.write(df.tail(24))

        view_option = st.selectbox("🔢 表示データを選択", ["直近24回", "直近50回", "全回数"])
        if view_option == "直近24回":
            display_ranking(df.tail(24))
        elif view_option == "直近50回":
            display_ranking(df.tail(50))
        else:
            display_ranking(df)

        display_distribution(df, lottery_name)

# ✅ メイン関数
def main():
    st.set_page_config(page_title="ロト・ナンバーズ AI予想サイト", layout="wide")
    display_header()

    st.title("🎯 ロト・ナンバーズ AI予想サイト")
    st.write("🔍 各種ロト・ナンバーズの詳細なデータ分析とAI予想を提供します。")

    page = st.selectbox("🗂️ 分析ページを選択", ["ロト6", "ロト7", "ミニロト", "ナンバーズ3", "ナンバーズ4"])
    file_mapping = {
        "ロト6": "loto6_50.csv",
        "ロト7": "loto7_50.csv",
        "ミニロト": "miniloto_50.csv",
        "ナンバーズ3": "numbers3_50.csv",
        "ナンバーズ4": "numbers4_50.csv"
    }

    display_page(page, file_mapping[page])

    st.success("✅ ページが正常に読み込まれました！")

if __name__ == "__main__":
    main()
