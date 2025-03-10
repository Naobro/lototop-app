import pandas as pd
import random
import numpy as np
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# **直近24回の当選番号の処理**
def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df = df.fillna("未定義")
    df["第1数字"] = df["第1数字"].astype(int)
    df["第2数字"] = df["第2数字"].astype(int)
    df["第3数字"] = df["第3数字"].astype(int)
    df["第4数字"] = df["第4数字"].astype(int)  # 4番目の数字を追加
    return df.tail(24)

# **風車予想**
def windmill_prediction(df):
    windmill_predictions = []

    # 風車の移動範囲設定
    right_move = {0: [1, 3, 2], 1: [2, 3, 5], 2: [4, 2, 1], 3: [3, 4, 2]}
    left_move = {0: [1, 3, 5], 1: [1, 4, 5], 2: [1, 2, 3], 3: [1, 2, 5]}
    
    for _, row in df.iterrows():
        # 各数字の風車移動を生成
        windmill_1 = (row['第1数字'] + random.choice(right_move[0])) % 10  # 第1数字
        windmill_2 = (row['第2数字'] + random.choice(right_move[1])) % 10  # 第2数字
        windmill_3 = (row['第3数字'] + random.choice(right_move[2])) % 10  # 第3数字
        windmill_4 = (row['第4数字'] + random.choice(right_move[3])) % 10  # 第4数字

        windmill_predictions.append((windmill_1, windmill_2, windmill_3, windmill_4))

    return windmill_predictions

# **ボックスで多い当選番号**
def box_predictions():
    box_frequent_numbers = [
        [0, 2, 4, 5],
        [0, 1, 8, 9],
        [5, 7, 8, 9],
        [0, 4, 7, 9],
        [0, 5, 6, 9]
    ]
    return box_frequent_numbers

# **ストレートで多い当選番号**
def straight_predictions():
    straight_frequent_numbers = [
        [1, 5, 6, 4],
        [6, 9, 9, 2],
        [9, 9, 0, 9],
        [0, 7, 5, 8],
        [8, 5, 4, 9]
    ]
    return straight_frequent_numbers

# **ランダム予測（軸数字を必ず含む）**
def generate_random_predictions(n, axis_number):
    predictions = []
    for _ in range(n):
        # ランダム予測：軸数字を含んだ予測
        prediction = [axis_number, random.choice([i for i in range(10) if i != axis_number]), 
                      random.choice([i for i in range(10) if i != axis_number]),
                      random.choice([i for i in range(10) if i != axis_number])]
        prediction = sorted(prediction)  # 順番を無視するためにソート
        if prediction not in predictions:  # 重複を排除
            predictions.append(prediction)
    return predictions

# **予測アルゴリズムをまとめて呼び出す関数**
def generate_predictions(csv_path, axis_number):
    df = load_data(csv_path)
    
    # 風車予測
    windmill = windmill_prediction(df)
    
    # ボックス予測
    box_predictions_list = box_predictions()
    
    # ストレート予測
    straight_predictions_list = straight_predictions()

    # ランダム予測
    random_predictions = generate_random_predictions(20, axis_number)

    return windmill, box_predictions_list, straight_predictions_list, random_predictions

# **予測のボタン処理**
axis_number = st.selectbox("軸数字を選択 (0〜9)", list(range(10)), key="axis_number")
num_predictions = 20  # 予測数を20に固定

if st.button("20パターン予測", key="random_predict_button"):
    windmill, box_predictions_list, straight_predictions_list, random_predictions = generate_predictions("/path/to/numbers4_24.csv", axis_number)
    
    # 予測結果を表示
    st.write(f"ランダム予測 (20パターン)：")
    df_random_predictions = pd.DataFrame(random_predictions, columns=[f'予測番号{i+1}' for i in range(4)])
    st.dataframe(df_random_predictions)
    
    st.write(f"ボックス予測：")
    df_box_predictions = pd.DataFrame(box_predictions_list, columns=[f'予測番号{i+1}' for i in range(4)])
    st.dataframe(df_box_predictions)

    st.write(f"ストレート予測：")
    df_straight_predictions = pd.DataFrame(straight_predictions_list, columns=[f'予測番号{i+1}' for i in range(4)])
    st.dataframe(df_straight_predictions)

    st.write(f"風車予測：")
    df_windmill_predictions = pd.DataFrame(windmill, columns=[f'予測番号{i+1}' for i in range(4)])
    st.dataframe(df_windmill_predictions)