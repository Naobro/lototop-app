import pandas as pd
import streamlit as st
from loto_prediction import generate_and_save_predictions, verify_predictions_with_actual

# **Streamlit アプリケーション**
st.title("ロト6 AI予想サイト")

# **予想を生成しCSVに保存**
csv_path = "predictions.csv"
predictions = generate_and_save_predictions(csv_path, prediction_count=10)

# **最新の当選番号**
actual_numbers = [23, 25, 26, 30, 34, 35]

# **予想結果の検証を実行**
verify_predictions_with_actual(actual_numbers, predictions)

# **予想結果を表示**
st.header("予想結果")
st.write(f"予想結果: {len(predictions)}パターン")
prediction_df = pd.DataFrame(predictions, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字"])
st.table(prediction_df)