# ロト6・ロト7・ミニロト・ナンバーズ予想サイト (Streamlitベース)

try:
    import streamlit as st
except ModuleNotFoundError:
    raise ModuleNotFoundError("Streamlit モジュールが見つかりませんでした。次のコマンドを実行してください:\n\npip install streamlit")

import pandas as pd
import random

# データ読み込み関数
def load_data(filename):
    try:
        data = pd.read_csv(filename)
    except FileNotFoundError:
        data = pd.DataFrame()
    return data

# 数字の出現頻度を計算
def calculate_frequency(data):
    if not data.empty:
        all_numbers = data.values.flatten()
        all_numbers = all_numbers[~pd.isnull(all_numbers)]
        return pd.Series(all_numbers).value_counts().sort_values(ascending=False)
    return pd.Series()

# 予想数字生成関数
def generate_prediction(lottery_type, frequency):
    number_ranges = {
        'ロト6': (1, 43, 6),
        'ロト7': (1, 37, 7),
        'ミニロト': (1, 31, 5),
        'ナンバーズ3': (0, 9, 3),
        'ナンバーズ4': (0, 9, 4)
    }
    start, end, count = number_ranges[lottery_type]
    available_numbers = list(range(start, end + 1))
    available_numbers.sort(key=lambda x: frequency.get(x, 0), reverse=True)
    prediction = random.sample(available_numbers[:min(len(available_numbers), 10)], count)
    return sorted(prediction)

# Streamlit UI
def main():
    st.title("ロト・ナンバーズ予想サイト 🎯")

    lottery_type = st.selectbox("予想したいくじを選択:", ['ロト6', 'ロト7', 'ミニロト', 'ナンバーズ3', 'ナンバーズ4'])
    filename = f"{lottery_type}_data.csv"
    data = load_data(filename)
    frequency = calculate_frequency(data)

    st.subheader(f"{lottery_type}の予想数字 ✨")
    for i in range(4):
        prediction = generate_prediction(lottery_type, frequency)
        st.write(f"パターン {i + 1}: {prediction}")

    st.subheader("過去のデータ")
    if not data.empty:
        st.dataframe(data)
    else:
        st.write("過去データがありません。")

    st.subheader("新しいデータを追加")
    number_ranges = {
        'ロト6': (1, 43, 6),
        'ロト7': (1, 37, 7),
        'ミニロト': (1, 31, 5),
        'ナンバーズ3': (0, 9, 3),
        'ナンバーズ4': (0, 9, 4)
    }
    start, end, count = number_ranges[lottery_type]
    cols = st.columns(count)
    new_entry = [cols[i].number_input(f"数字 {i + 1}", min_value=start, max_value=end, step=1, key=f"num{i}")
                 for i in range(count)]

    if st.button("データを保存"):
        new_data = pd.DataFrame([new_entry], columns=[f"Num{i + 1}" for i in range(len(new_entry))])
        updated_data = pd.concat([data, new_data], ignore_index=True)
        updated_data.to_csv(filename, index=False)
        st.success("データを保存しました！")

if __name__ == "__main__":
    main()
    