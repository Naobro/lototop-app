import streamlit as st
import pandas as pd
import os
from PIL import Image

# ✅ データ読み込み関数 (エンコーディング対応)
def load_data(filename):
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(data_folder, filename)
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path, encoding='utf-8')  # ✅ UTF-8で読み込み
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding='cp932')  # ✅ CP932で再試行
    else:
        st.error(f"❌ データファイルが見つかりません: {file_path}")
        return None

# ✅ ヘッダー画像表示関数
def display_header():
    image_path = os.path.join(os.path.dirname(__file__), "header.png")
    if os.path.exists(image_path):
        header_image = Image.open(image_path)
        st.image(header_image, use_container_width=True)  # ✅ use_container_widthに修正
    else:
        st.warning(f"⚠️ ヘッダー画像が見つかりません: {image_path}")

# ✅ ランキングテーブル表示
def display_ranking(title, df):
    if df is not None:
        st.subheader(title)
        st.dataframe(df)
    else:
        st.warning(f"⚠️ {title} のデータがありません。")

# ✅ メイン関数
def main():
    st.set_page_config(page_title="ロト・ナンバーズ AI予想サイト", layout="wide")
    display_header()

    st.title("🎯 ロト・ナンバーズ AI予想サイト")
    st.write("🔍 最新の当選番号データを反映し、直近24回および50回の分析を表示します。")

    # ✅ データ読み込み
    loto6_50 = load_data("loto6_50.csv")
    loto7_50 = load_data("loto7_50.csv")
    miniloto_50 = load_data("miniloto_50.csv")

    # ✅ ランキング表示
    display_ranking("🔢 ロト6 直近50回のランキング", loto6_50)
    display_ranking("🔢 ロト7 直近50回のランキング", loto7_50)
    display_ranking("🔢 ミニロト 直近50回のランキング", miniloto_50)

    st.success("✅ ページが正常に読み込まれました！")

if __name__ == "__main__":
    main()