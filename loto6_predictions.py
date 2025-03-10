import random
import pandas as pd
import streamlit as st

# **ページのタイトル**
st.title("ロト6 AI予想サイト")

# **直近24回のデータから3回以上出現した数字を抽出する関数**
def get_numbers_with_multiple_occurrences(df, min_occurrences=3):
    numbers = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].values.flatten()
    number_counts = pd.Series(numbers).value_counts()
    return number_counts[number_counts >= min_occurrences].index.tolist()

# **電卓攻略に基づく予想**
def calculate_number_with_formula(numbers, weights):
    total = sum(numbers)
    predicted_numbers = [round(total / weight) for weight in weights]
    predicted_numbers = [min(num, 43) for num in predicted_numbers]  # 最大43に調整
    return predicted_numbers

# **前回の当選番号（C）を取得**
def get_previous_numbers(df):
    latest_result = df.iloc[0]
    return [latest_result['第1数字'], latest_result['第2数字'], latest_result['第3数字'], latest_result['第4数字'], latest_result['第5数字'], latest_result['第6数字']]

# **前回の当選番号の前後の数字（D）を取得**
def get_neighbouring_numbers(previous_numbers):
    neighbouring_numbers = []
    for num in previous_numbers:
        if num - 1 >= 1:
            neighbouring_numbers.append(num - 1)
        if num + 1 <= 43:
            neighbouring_numbers.append(num + 1)
    return list(set(neighbouring_numbers))

# **それ以外の数字（E）を取得**
def get_other_numbers(multiple_occurrences, previous_numbers):
    all_numbers = set(range(1, 44))
    all_numbers -= set(multiple_occurrences)  # A数字を除外
    all_numbers -= set(previous_numbers)  # B数字とC数字を除外
    return list(all_numbers)

# **指定された範囲からランダムに数字を選ぶ**
def get_number_from_range(number_range, used_numbers):
    available_numbers = list(set(number_range) - set(used_numbers))  # 使用済みの数字を除外
    return random.choice(available_numbers)

# **予想生成関数**
def generate_loto6_prediction(df, prediction_count=10):
    multiple_occurrences = get_numbers_with_multiple_occurrences(df)
    previous_numbers = get_previous_numbers(df)
    neighbouring_numbers = get_neighbouring_numbers(previous_numbers)
    other_numbers = get_other_numbers(multiple_occurrences, previous_numbers)

    column_ranges = {
        1: list(range(1, 17)),  # 一列目 (1〜16)
        2: list(range(2, 25)),  # 二列目 (2〜24)
        3: list(range(6, 33)),  # 三列目 (6〜32)
        4: list(range(12, 39)), # 四列目 (12〜38)
        5: list(range(19, 43)), # 五列目 (19〜42)
        6: list(range(27, 44))  # 六列目 (27〜43)
    }

    predictions = []
    for _ in range(prediction_count):
        used_numbers = set()
        prediction = []

        # 各列ごとに数字を選ぶ
        for col in range(1, 7):
            number = get_number_from_range(column_ranges[col], used_numbers)
            prediction.append(number)
            used_numbers.add(number)
        
        prediction.sort()
        predictions.append(prediction)

    return predictions

# **予想結果を表示する関数**
def display_predictions(predictions):
    prediction_df = pd.DataFrame(predictions, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字"])
    st.table(prediction_df)

# **予想アルゴリズム**
st.header("⑤ 予想")

# セッション状態を使用して予想結果を保存
if 'predictions' not in st.session_state:
    st.session_state.predictions = generate_loto6_prediction(pd.read_csv("/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv"), prediction_count=10)

# 予想を表示
display_predictions(st.session_state.predictions)

# **⑥ 検証**
st.header("⑥ 検証")
# 実際の当選番号と一致する予想数字を表示
actual_numbers = get_previous_numbers(pd.read_csv("/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv"))
matched_predictions = []

for prediction in st.session_state.predictions:
    matched_predictions.append(list(set(prediction) & set(actual_numbers)))

st.write(f"実際の当選番号: {actual_numbers}")
st.write(f"一致する予想数字: {matched_predictions}")