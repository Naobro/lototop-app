import streamlit as st
import pandas as pd
from PIL import Image
import os


def display_header():
    # ✅ 画像のパスを動的に取得
    image_path = os.path.join(os.path.dirname(__file__), "header.png")
    try:
        header_image = Image.open(image_path)
        st.image(header_image, use_container_width=True)
    except FileNotFoundError:
        st.error(f"ヘッダー画像が見つかりません: {image_path}")


def load_data(file_path):
    # ✅ CSVファイルの読み込みを行い、ファイルが存在しない場合にエラーを表示
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"データファイルが見つかりません: {file_path}")
        return pd.DataFrame()


def display_ranking(df, title):
    # ✅ 出現回数ランキングを表示
    if df.empty:
        st.warning(f"{title} のデータがありません。")
    else:
        st.subheader(title)
        ranking = (
            df.apply(pd.Series.value_counts)
            .sum(axis=1)
            .reset_index()
            .rename(columns={"index": "数字", 0: "出現回数"})
            .sort_values(by="出現回数", ascending=False)
            .reset_index(drop=True)
        )
        ranking.index += 1
        st.dataframe(ranking)


def main():
    st.set_page_config(page_title="ロト・ナンバーズAI予想", layout="wide")
    display_header()

    st.title("✨ ロト・ナンバーズ AI予想サイト ✨")

    # ✅ CSVデータの読み込み
    loto6_24 = load_data(os.path.join("data", "loto6_24.csv"))
    loto7_24 = load_data(os.path.join("data", "loto7_24.csv"))
    miniloto_24 = load_data(os.path.join("data", "miniloto_24.csv"))

    # ✅ ランキング表示
    display_ranking(loto6_24, "🔢 ロト6 直近24回のランキング")
    display_ranking(loto7_24, "🔢 ロト7 直近24回のランキング")
    display_ranking(miniloto_24, "🔢 ミニロト 直近24回のランキング")

    st.success("✅ ページが正常に読み込まれました！")


if __name__ == "__main__":
    main()