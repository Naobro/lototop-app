import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import os
import sys
import warnings
warnings.filterwarnings("ignore")

# 機械学習用
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

# データの読み込み
CSV_PATH = "./data/n3.csv"
df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=["第1数字", "第2数字", "第3数字"])
df[["第1数字", "第2数字", "第3数字"]] = df[["第1数字", "第2数字", "第3数字"]].astype(int)

# 入力と出力を作成（1つ前のデータを特徴量、現在を正解とする）
X, y1, y2, y3 = [], [], [], []
for i in range(len(df)-1):
    prev = df.iloc[i+1]
    curr = df.iloc[i]
    X.append([prev["第1数字"], prev["第2数字"], prev["第3数字"]])
    y1.append(curr["第1数字"])
    y2.append(curr["第2数字"])
    y3.append(curr["第3数字"])
X = np.array(X)

# 最新の当選番号（1行目が最新）
latest = df.iloc[0][["第1数字", "第2数字", "第3数字"]].tolist()

# 共通予測関数
def get_top3(model, x):
    probs = model.predict_proba([x])[0]
    return [i for i, _ in sorted(enumerate(probs), key=lambda x: -x[1])[:3]]

# --- Streamlit表示 ---
st.title("🔢 ナンバーズ3 - AI予測（3手法）")
st.markdown("前回当選番号：<br><b style='font-size:24px; color:crimson'>{}</b>".format("-".join(map(str, latest))), unsafe_allow_html=True)

# --- 1. ランダムフォレスト ---
st.header("🌲 ランダムフォレスト予測")
rf1 = RandomForestClassifier(n_estimators=100).fit(X, y1)
rf2 = RandomForestClassifier(n_estimators=100).fit(X, y2)
rf3 = RandomForestClassifier(n_estimators=100).fit(X, y3)
rf_pred = {
    "第1数字": get_top3(rf1, latest),
    "第2数字": get_top3(rf2, latest),
    "第3数字": get_top3(rf3, latest)
}
st.dataframe(pd.DataFrame(rf_pred))

# --- 2. ニューラルネットワーク ---
st.header("🧠 ニューラルネットワーク予測")
nn1 = MLPClassifier(hidden_layer_sizes=(50,), max_iter=1000).fit(X, y1)
nn2 = MLPClassifier(hidden_layer_sizes=(50,), max_iter=1000).fit(X, y2)
nn3 = MLPClassifier(hidden_layer_sizes=(50,), max_iter=1000).fit(X, y3)
nn_pred = {
    "第1数字": get_top3(nn1, latest),
    "第2数字": get_top3(nn2, latest),
    "第3数字": get_top3(nn3, latest)
}
st.dataframe(pd.DataFrame(nn_pred))

# --- 3. マルコフ連鎖風分析 ---
st.header("🔗 マルコフ連鎖予測")

def markov_predict(column_name):
    transition = defaultdict(list)
    col = df[column_name].tolist()
    for i in range(len(col)-1):
        transition[col[i]].append(col[i+1])
    last = df.iloc[0][column_name]
    counter = Counter(transition[last])
    return [n for n, _ in counter.most_common(3)]

markov_pred = {
    "第1数字": markov_predict("第1数字"),
    "第2数字": markov_predict("第2数字"),
    "第3数字": markov_predict("第3数字")
}
st.dataframe(pd.DataFrame(markov_pred))

# --- 重複数字表示 ---
st.header("✅ 3手法で一致した数字（高確率）")

def get_common_digits(*preds):
    result = []
    for i in ["第1数字", "第2数字", "第3数字"]:
        common = set(rf_pred[i]) & set(nn_pred[i]) & set(markov_pred[i])
        result.append((i, list(common)))
    return result

common_digits = get_common_digits(rf_pred, nn_pred, markov_pred)
for label, nums in common_digits:
    st.markdown(f"**{label}**：{'、'.join(map(str, nums)) if nums else '（一致なし）'}")