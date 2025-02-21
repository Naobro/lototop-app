# ロト・ナンバーズ予想サイト - ヘッダー画像を4枚並べて表示する改良版

import streamlit as st
import pandas as pd
import random
import os

st.set_page_config(page_title="ロト・ナンバーズ予想サイト", layout="wide")

# ✅ データ読み込み関数
def load_data(filename):
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename, encoding='utf-8')
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
    else:
        st.warning(f"{filename} が見つかりません。CSVファイルをアップロードしてください。")
        uploaded_file = st.file_uploader("CSVファイルをアップロード:", type=["csv"])
        if uploaded_file is not None:
            return pd.read_csv(uploaded_file, encoding='utf-8')
    return pd.DataFrame()

# ✅ 出現パターン分析 (直近24回のデータでパターンを集計)
def pattern_analysis(data):
    pattern_counts = {}
    recent_data = data.iloc[::-1].head(24)  # 最新24回分を取得

    for _, row in recent_data.iterrows():
        summary = {'1': 0, '10': 0, '20': 0, '30': 0}
        for num in row:
            try:
                num = int(num)
                if 1 <= num <= 9:
                    summary['1'] += 1
                elif 10 <= num <= 19:
                    summary['10'] += 1
                elif 20 <= num <= 29:
                    summary['20'] += 1
                elif 30 <= num <= 39:
                    summary['30'] += 1
            except ValueError:
                continue
        pattern_str = ", ".join([f"{key}-{value}" for key, value in summary.items()])
        pattern_counts[pattern_str] = pattern_counts.get(pattern_str, 0) + 1

    df_patterns = pd.DataFrame(list(pattern_counts.items()), columns=["出現パターン", "出現回数"])
    df_patterns.sort_values(by="出現回数", ascending=False, inplace=True)
    return df_patterns

# ✅ 予想数字生成 (ナンバーズ復活)
def generate_prediction(lottery_type, frequency, count):
    ranges = {
        'ロト6': (1, 43, 6),
        'ロト7': (1, 37, 7),
        'ミニロト': (1, 31, 5),
        'ナンバーズ3': (0, 9, 3),
        'ナンバーズ4': (0, 9, 4)
    }
    start, end, num_count = ranges[lottery_type]
    available_numbers = list(range(start, end + 1))
    available_numbers.sort(key=lambda x: frequency.get(x, 0), reverse=True)
    predictions = []
    sample_range = max(len(available_numbers), num_count * 2)
    for _ in range(count):
        prediction = sorted(random.sample(available_numbers[:sample_range], num_count))
        predictions.append(prediction)
    return predictions

# ✅ Streamlit UI
def main():
    st.title("ロト・ナンバーズ予想サイト 🎯 - 4枚ヘッダー画像対応版")

    # ✅ ヘッダーに4枚の当選実績画像を表示
    st.subheader("当選実績画像 (ヘッダーに4枚並べて表示)")
    cols = st.columns(4)
    for i in range(4):
        with cols[i]:
            image_file = st.file_uploader(f"ヘッダー画像 {i + 1} をアップロード:", type=["png", "jpg", "jpeg"], key=f"header_image_{i}")
            if image_file:
                st.image(image_file, caption=f"ヘッダー画像 {i + 1}", use_column_width=True)

    lottery_type = st.selectbox("予想したいロト・ナンバーズを選択:", ['ロト6', 'ロト7', 'ミニロト', 'ナンバーズ3', 'ナンバーズ4'])
    filename = f"{lottery_type}_data.csv"
    data = load_data(filename)

    st.subheader("過去データ（最新順）")
    if not data.empty:
        data_sorted = data.iloc[::-1].reset_index(drop=True)
        st.dataframe(data_sorted)

        # ✅ 出現パターン分析の表示
        st.subheader("出現パターン分析 ✨ (直近24回)")
        pattern_df = pattern_analysis(data_sorted)
        st.dataframe(pattern_df)

    else:
        st.warning("過去データがありません。CSVをアップロードしてください。")

    # ✅ 予想数字生成
    st.subheader("予想数字生成 💡")
    frequency = pd.Series(data.values.flatten()).value_counts() if not data.empty else pd.Series()
    prediction_count = st.selectbox("予想パターン数を選択:", [5, 10, 20, 50, 100])
    predictions = generate_prediction(lottery_type, frequency, prediction_count)

    for idx, pred in enumerate(predictions):
        st.write(f"パターン {idx + 1}: {pred}")

if __name__ == "__main__":
    main()
