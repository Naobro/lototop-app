import pandas as pd
import random
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from tensorflow import keras

# **直近24回の当選番号の処理**
def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df = df.fillna("未定義")
    df["第1数字"] = df["第1数字"].astype(int)
    df["第2数字"] = df["第2数字"].astype(int)
    df["第3数字"] = df["第3数字"].astype(int)
    return df.tail(24)

# **同じボックス番号を削除**
def remove_same_box(df):
    box_numbers = []
    filtered_df = []
    for _, row in df.iterrows():
        box = tuple(sorted([row['第1数字'], row['第2数字'], row['第3数字']]))
        if box not in box_numbers:
            box_numbers.append(box)
            filtered_df.append(row)
    return pd.DataFrame(filtered_df)

# **ダブル予測**
def double_and_single(df):
    predictions = set()  # 重複を防ぐためにsetを使用
    for _, row in df.iterrows():
        numbers = [row['第1数字'], row['第2数字'], row['第3数字']]
        
        # ダブル：3つの数字の内、2つが同じ
        if len(set(numbers)) == 2:
            # 数字の並びをソートして同じ組み合わせの重複を防ぐ
            sorted_numbers = tuple(sorted(numbers))
            predictions.add(sorted_numbers)
        
        # シングル：すべて異なる数字が出る予測
        elif len(set(numbers)) == 3:
            predictions.add(tuple(sorted(numbers)))  # シングルもソートして重複を防ぐ
    
    # 結果をリストに戻す（セットにすることで重複を排除）
    predictions = list(predictions)
    
    # リストに戻す
    return predictions

# **ハーフ予測**
def generate_half_predictions(axis_number, n):
    single_predictions = [random.sample([i for i in range(10) if i != axis_number], 3) for _ in range(n//2)]
    double_predictions = [[axis_number, axis_number, random.choice([i for i in range(10) if i != axis_number])] for _ in range(n//2)]
    random.shuffle(double_predictions)
    return single_predictions + double_predictions

# **完全ランダム予想**
def generate_random_predictions(n):
    predictions = []
    for _ in range(n):
        prediction = [random.randint(0, 9) for _ in range(3)]
        predictions.append(prediction)
    return predictions

# **風車予想**
def windmill_prediction(df):
    windmill_predictions = []

    for _, row in df.iterrows():
        # 各数字の風車移動（3〜5の範囲で右移動）
        windmill_1 = (row['第1数字'] + random.choice([3, 4, 5])) % 10
        windmill_2 = (row['第2数字'] + random.choice([3, 4, 5])) % 10
        windmill_3 = (row['第3数字'] + random.choice([3, 4, 5])) % 10
        windmill_predictions.append((windmill_1, windmill_2, windmill_3))

    return windmill_predictions

# **ランダムフォレスト予測**
def random_forest_prediction(df):
    # ここでは仮の特徴量とターゲットを作成
    X = df[['第1数字', '第2数字', '第3数字']]  # 特徴量
    y = np.random.randint(0, 2, size=len(df))  # 仮のターゲット
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestClassifier(n_estimators=100)
    rf.fit(X_train, y_train)
    predictions = rf.predict(X_test)
    
    return predictions

# **ニューラルネットワーク予測**
def neural_network_prediction(df):
    # ここでは仮の特徴量とターゲットを作成
    X = df[['第1数字', '第2数字', '第3数字']]  # 特徴量
    y = np.random.randint(0, 2, size=len(df))  # 仮のターゲット
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = keras.Sequential([
        keras.layers.Dense(64, activation='relu', input_dim=3),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(1, activation='sigmoid')
    ])

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X_train, y_train, epochs=10, batch_size=32)

    predictions = model.predict(X_test)
    
    return predictions

# **ひっぱり予測**
def check_hoppari(df):
    hoppari_count = 0
    for i in range(1, len(df)):
        current_numbers = {df.iloc[i]['第1数字'], df.iloc[i]['第2数字'], df.iloc[i]['第3数字']}
        previous_numbers = {df.iloc[i-1]['第1数字'], df.iloc[i-1]['第2数字'], df.iloc[i-1]['第3数字']}
        if len(current_numbers.intersection(previous_numbers)) > 0:
            hoppari_count += 1
    return hoppari_count

# **合計値の予測**
def remove_same_sum(df):
    sum_counts = Counter()
    valid_rows = []

    for _, row in df.iterrows():
        total_sum = row['第1数字'] + row['第2数字'] + row['第3数字']
        if sum_counts[total_sum] == 0:
            valid_rows.append(row)
            sum_counts[total_sum] += 1

    return pd.DataFrame(valid_rows)

# **予測アルゴリズムをまとめて呼び出す関数**
def generate_predictions(csv_path):
    df = load_data(csv_path)
    df = remove_same_box(df)
    box_freq = box_frequency(df)
    straight_freq = straight_frequency(df)
    windmill = windmill_prediction(df)
    hoppari = check_hoppari(df)
    rf_predictions = random_forest_prediction(df)
    nn_predictions = neural_network_prediction(df)
    double_single = double_and_single(df)
    return box_freq, straight_freq, windmill, hoppari, rf_predictions, nn_predictions, double_single