import streamlit as st
import pandas as pd
import os
from PIL import Image

def load_latest_data(file_path, num_rows=24):
    """
    指定されたCSVファイルから最新のデータをnum_rows分取得する関数
    """
    if not os.path.exists(file_path):
        st.error(f"データファイルが見つかりません: {file_path}")
        return pd.DataFrame()  # 空のデータフレームを返す

    df = pd.read_csv(file_path)
    df = df.tail(num_rows)  # 最新のnum_rows行を取得
    return df.reset_index(drop=True)

def display_header():
    """
    ヘッダー画像を表示する関数
    """
    image_path = os.path.join(os.path.dirname(__file__), "header.png")
    if os.path.exists(image_path):
        header_image = Image.open(image_path)
        st.image(header_image, use_container_width=True)
    else:
        st.warning("ヘッダー画像が見つかりませんでした。")

def display_data(title, data):
    """
    データフレームを表示する関数
    """
    if data.empty:
        st.warning(f"🔢 {title} のデータがありません。")
    else:
        st.subheader(f"🔢 {title}")
        st.dataframe(data)

def main():
    """
    Streamlitアプリのメイン関数
    """
    st.set_page_config(page_title="ロト・ナンバーズ AI予想サイト", layout="wide")
    display_header()

    # ✅ 50回分のデータから最新24回を取得
    loto6_24 = load_latest_data("data/loto6_50.csv", num_rows=24)
    loto7_24 = load_latest_data("data/loto7_50.csv", num_rows=24)
    miniloto_24 = load_latest_data("data/miniloto_50.csv", num_rows=24)

    # データ表示
    display_data("ロト6 直近24回のランキング", loto6_24)
    display_data("ロト7 直近24回のランキング", loto7_24)
    display_data("ミニロト 直近24回のランキング", miniloto_24)

    st.success("✅ ページが正常に読み込まれました！")

if __name__ == "__main__":
    main()
