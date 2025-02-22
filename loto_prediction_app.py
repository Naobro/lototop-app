import streamlit as st
import pandas as pd
import os
from PIL import Image

def display_header():
    image_path = os.path.join(os.path.dirname(__file__), "header.png")
    header_image = Image.open(image_path)
    st.image(header_image, use_container_width=True)

def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        st.error(f"ファイルが見つかりません: {file_path}")
        return pd.DataFrame()

def save_updated_data(file_path, new_data):
    new_data.to_csv(file_path, index=False)
    st.success(f"データを正常に更新しました: {file_path}")

def update_data_section(title, file_path):
    st.subheader(title)
    data = load_data(file_path)
    if not data.empty:
        st.dataframe(data)
        uploaded_file = st.file_uploader(f"最新の当選番号ファイルをアップロード ({title})", type="csv", key=title)
        if uploaded_file is not None:
            new_data = pd.read_csv(uploaded_file)
            save_updated_data(file_path, new_data)
            st.experimental_rerun()

def show_ranking(data, title):
    st.subheader(f"{title} - よく出ている数字ランキング")
    if not data.empty:
        numbers = data.values.flatten()
        numbers = numbers[~pd.isnull(numbers)]
        numbers = [int(x) for x in numbers if str(x).isdigit()]
        df = pd.Series(numbers).value_counts().reset_index()
        df.columns = ['数字', '出現回数']
        df['順位'] = df['出現回数'].rank(method='min', ascending=False).astype(int)
        df = df.sort_values(by='順位')
        st.dataframe(df[['順位', '出現回数', '数字']])
    else:
        st.info("データが見つかりませんでした。")

def main():
    st.set_page_config(page_title="ロト・ナンバーズ AI予想", layout="wide")
    display_header()

    st.title("ロト・ナンバーズ AI予想サイト")
    st.markdown("""
        **機能一覧**:
        - ✅ ロト6・ロト7・ミニロトの直近24回・50回・全回データ分析
        - ✅ ナンバーズ3・ナンバーズ4の1桁～4桁ランキング
        - ✅ データアップロードによる最新結果の自動反映
    """)

    # データ更新セクション
    update_data_section("ロト6 直近24回データ", "data/loto6_24.csv")
    update_data_section("ロト6 直近50回データ", "data/loto6_50.csv")
    update_data_section("ロト7 直近24回データ", "data/loto7_24.csv")
    update_data_section("ロト7 直近50回データ", "data/loto7_50.csv")
    update_data_section("ミニロト 直近24回データ", "data/miniloto_24.csv")
    update_data_section("ミニロト 直近50回データ", "data/miniloto_50.csv")

    # ランキング表示
    st.header("📊 ランキング表示")
    show_ranking(load_data("data/loto6_24.csv"), "ロト6 直近24回")
    show_ranking(load_data("data/loto6_50.csv"), "ロト6 直近50回")
    show_ranking(load_data("data/loto7_24.csv"), "ロト7 直近24回")
    show_ranking(load_data("data/loto7_50.csv"), "ロト7 直近50回")
    show_ranking(load_data("data/miniloto_24.csv"), "ミニロト 直近24回")
    show_ranking(load_data("data/miniloto_50.csv"), "ミニロト 直近50回")

if __name__ == "__main__":
    main()
import pandas as pd

def load_latest_data(file_path, num_rows=24):
    """📊 指定されたCSVファイルから最新のデータを取得します。"""
    df = pd.read_csv(file_path)
    # 最新データが一番下にある場合、下から指定した行数を取得
    latest_data = df.tail(num_rows).reset_index(drop=True)
    return latest_data
loto6_24 = load_latest_data("data/loto6_50.csv", num_rows=24)