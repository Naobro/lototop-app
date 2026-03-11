import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from auth import check_password

st.set_page_config(layout="centered")

import ssl
import pandas as pd
import random
import html
import json 
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.exceptions import NotFittedError
from PIL import Image, ImageDraw, ImageFont
import platform

CSV_PATH = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers4_24.csv"

def format_number(val):
    try:
        return f"{int(float(val)):,}"
    except:
        return "未定義"

# ============================================
# NAOKIの予想画像生成機能（新規追加）
# ============================================

def get_system_font():
    """OS別に最適な日本語フォントを自動選択"""
    system = platform.system()
    font_candidates = {
        "Windows": [
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/arial.ttf"
        ],
        "Darwin": [  # macOS
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Arial.ttf"
        ],
        "Linux": [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]
    }
    
    for font_path in font_candidates.get(system, []):
        if os.path.exists(font_path):
            return font_path
    return None

def run_ai_prediction_logic(df_data):
    """
    科学的に正確なAI予想ロジック
    渡されたデータに基づいて5つの予想数字を各桁で生成
    """
    required_cols = ["第1数字", "第2数字", "第3数字", "第4数字"]
    
    if len(df_data) < 10:
        # データが少ない場合はランダム生成
        return pd.DataFrame({
            "第1数字": random.sample(range(10), 5),
            "第2数字": random.sample(range(10), 5),
            "第3数字": random.sample(range(10), 5),
            "第4数字": random.sample(range(10), 5),
        })
    
    # データ分割
    dfs = {
        "全データ": (df_data, 0.1),
        "直近100回": (df_data.tail(min(100, len(df_data))), 0.3),
        "直近24回": (df_data.tail(min(24, len(df_data))), 0.6)
    }
    
    # 風車盤設定
    wheels = [
        [0, 3, 6, 9, 2, 5, 8, 1, 4, 7],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [0, 7, 4, 1, 8, 5, 2, 9, 6, 3],
        [0, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    ]
    
    final_scores = [Counter() for _ in range(4)]
    WH_WEIGHT = 2.0
    RANK_SCORES = [2.0, 1.5, 1.0, 0.7, 0.5]

    # 各データセットでモデル実行
    for label, (data, weight) in dfs.items():
        if len(data) < 5:
            continue
            
        # 学習データ作成
        X, ys = [], [[] for _ in range(4)]
        for i in range(len(data) - 1):
            prev = data.iloc[i + 1]
            curr = data.iloc[i]
            X.append([prev[c] for c in required_cols])
            for j in range(4):
                ys[j].append(curr[required_cols[j]])
        
        if len(X) == 0:
            continue
            
        latest_input = [[data.iloc[0][col] for col in required_cols]]
        
        # RandomForest
        try:
            for i in range(4):
                rf = RandomForestClassifier(n_estimators=50, random_state=42)
                rf.fit(X, ys[i])
                probs = rf.predict_proba(latest_input)[0]
                top3 = sorted(range(len(probs)), key=lambda x: probs[x], reverse=True)[:3]
                for rank, n in enumerate(top3):
                    final_scores[i][n] += (3 - rank) * weight
        except:
            pass

        # ニューラルネット
        try:
            for i in range(4):
                nn = MLPClassifier(max_iter=300, random_state=42)
                nn.fit(X, ys[i])
                probs = nn.predict_proba(latest_input)[0]
                top3 = sorted(range(len(probs)), key=lambda x: probs[x], reverse=True)[:3]
                for rank, n in enumerate(top3):
                    final_scores[i][n] += (3 - rank) * weight
        except:
            pass

        # マルコフ連鎖
        for i in range(4):
            series = data[f"第{i+1}数字"].tolist()
            trans = defaultdict(Counter)
            for k in range(len(series)-1):
                trans[series[k]][series[k+1]] += 1
            if len(series) > 0:
                last_num = series[0]
                top3 = [n for n, _ in trans[last_num].most_common(3)]
                for rank, n in enumerate(top3):
                    final_scores[i][n] += (3 - rank) * weight
        
        # 風車盤分析
        for i in range(4):
            count = Counter()
            wheel = wheels[i]
            for val in data[f"第{i+1}数字"]:
                if val in wheel:
                    pos = wheel.index(val)
                    count[pos] += 1
            top_pos = [p for p, _ in count.most_common(3)]
            top3 = [wheel[p] for p in top_pos if p < len(wheel)]
            for rank, n in enumerate(top3):
                final_scores[i][n] += (3 - rank) * weight * WH_WEIGHT

       # 直近24回ランキング加点
    df_recent = data.tail(min(24, len(data)))
    for i, col in enumerate(required_cols):
        freq_list = df_recent[col].value_counts().index.tolist()
        for rank, num in enumerate(freq_list[:5]):
            final_scores[i][num] += RANK_SCORES[rank]

    # === TOP5抽出（トリプル除外版） ===
    ranked_candidates = []
    for i in range(4):
        if len(final_scores[i]) == 0:
            ranked_candidates.append(list(range(10)))
        else:
            ranked_candidates.append([n for n, _ in final_scores[i].most_common(15)])

    final_rows = []
    attempts = 0
    max_attempts = 1000

    while len(final_rows) < 5 and attempts < max_attempts:
        current_row = []
        for col_idx in range(4):
            candidates = ranked_candidates[col_idx]
            weights = [len(candidates) - i for i in range(len(candidates))]
            selected = random.choices(candidates, weights=weights, k=1)[0]
            current_row.append(selected)
        
        # トリプル除外判定（核心ロジック）
        counter = Counter(current_row)
        if max(counter.values()) <= 2:  # シングル or ダブルのみ許可
            if current_row not in final_rows:
                final_rows.append(current_row)
        attempts += 1

    # 保険処理
    while len(final_rows) < 5:
        combo = [random.randint(0, 9) for _ in range(4)]
        if max(Counter(combo).values()) <= 2:
            final_rows.append(combo)

    return pd.DataFrame({
        "第1数字": [row[0] for row in final_rows],
        "第2数字": [row[1] for row in final_rows],
        "第3数字": [row[2] for row in final_rows],
        "第4数字": [row[3] for row in final_rows],
    })

def create_naoki_prediction_image(
    current_predictions_df,
    current_round,
    current_date,
    previous_round=None,
    previous_winning=None,
    previous_predictions_df=None,
    output_path="output/naoki_prediction.png"
):
    """NAOKIデザインの予想画像を生成"""
    
    # キャンバス設定
    width, height = 1080, 1350
    background = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(background)
    
    # フォント設定
    font_path = get_system_font()
    
    try:
        if font_path:
            title_font = ImageFont.truetype(font_path, 55)
            date_font = ImageFont.truetype(font_path, 35)
            section_font = ImageFont.truetype(font_path, 42)
            header_font = ImageFont.truetype(font_path, 32)
            number_font = ImageFont.truetype(font_path, 50)
            winning_font = ImageFont.truetype(font_path, 45)
            footer_font = ImageFont.truetype(font_path, 28)
        else:
            title_font = date_font = section_font = header_font = number_font = winning_font = footer_font = ImageFont.load_default()
    except:
        title_font = date_font = section_font = header_font = number_font = winning_font = footer_font = ImageFont.load_default()
    
    y_pos = 40
    
    # タイトル部分
    title_rect = [40, y_pos, width-40, y_pos+120]
    draw.rounded_rectangle(title_rect, radius=10, fill='#1a5490')
    draw.text((width//2, y_pos+35), "NAOKIのナンバーズ4 予想", 
              font=title_font, fill='white', anchor='mm')
    draw.text((width//2, y_pos+85), datetime.now().strftime('%Y/%m/%d'), 
              font=date_font, fill='white', anchor='mm')
    y_pos += 160
    
    # 装飾線
    draw.line((60, y_pos), (width-60, y_pos), fill='#1a5490', width=4)
    y_pos += 50
    
    # === 前回検証セクション ===
    if previous_round and previous_winning and previous_predictions_df is not None:
        # セクションヘッダー
        verification_rect = [50, y_pos, width-50, y_pos+55]
        draw.rounded_rectangle(verification_rect, radius=8, fill='#e8f5e8', outline='#4caf50', width=2)
        draw.text((width//2, y_pos+27), f"📊 前回検証（第{previous_round}回）", 
                  font=section_font, fill='#2e7d32', anchor='mm')
        y_pos += 80
        
        # 当選番号表示
        winning_text = " - ".join(map(str, previous_winning))
        draw.text((width//2, y_pos), f"当選番号: {winning_text}", 
                  font=winning_font, fill='#d32f2f', anchor='mm')
        y_pos += 70
        
        # テーブル設定
        table_x = 80
        col_width = (width - 160) // 4
        
        # ヘッダー（統一表記）
        headers = ["第1数字", "第2数字", "第3数字", "第4数字"]
        for i, header in enumerate(headers):
            x = table_x + col_width * i + col_width // 2
            draw.text((x, y_pos), header, font=header_font, fill='#333333', anchor='mm')
        y_pos += 45
        
        # 区切り線
        draw.line((table_x, y_pos), (width-table_x, y_pos), fill='#cccccc', width=3)
        y_pos += 35
        
        # 検証データ（的中した数字のみ強調）
        row_height = 65
        for idx in range(5):
            for digit_idx in range(4):
                x = table_x + col_width * digit_idx + col_width // 2
                col_name = f"第{digit_idx + 1}数字"
                predicted_num = previous_predictions_df.iloc[idx][col_name]
                actual_num = previous_winning[digit_idx]
                
                # ★重要：的中した数字のみ事実として強調
                if predicted_num == actual_num:
                    circle_rect = [x-30, y_pos-30, x+30, y_pos+30]
                    draw.ellipse(circle_rect, fill='#ffcdd2', outline='#d32f2f', width=3)
                    text_color = '#d32f2f'
                else:
                    text_color = '#333333'
                
                draw.text((x, y_pos), str(predicted_num), 
                          font=number_font, fill=text_color, anchor='mm')
            y_pos += row_height
        
        y_pos += 30
    
    # 区切り線
    draw.line((60, y_pos), (width-60, y_pos), fill='#1a5490', width=4)
    y_pos += 50
    
    # === 今回予想セクション ===
    prediction_rect = [50, y_pos, width-50, y_pos+55]
    draw.rounded_rectangle(prediction_rect, radius=8, fill='#e3f2fd', outline='#2196f3', width=2)
    
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    weekday = weekdays[current_date.weekday()]
    draw.text((width//2, y_pos+27), f"🎯 今回予想（第{current_round}回・{current_date.strftime('%m/%d')}({weekday})）", 
              font=section_font, fill='#1565c0', anchor='mm')
    y_pos += 80
    
    # ヘッダー
    headers = ["第1数字", "第2数字", "第3数字", "第4数字"]
    for i, header in enumerate(headers):
        x = table_x + col_width * i + col_width // 2
        draw.text((x, y_pos), header, font=header_font, fill='#333333', anchor='mm')
    y_pos += 45
    
    # 区切り線
    draw.line((table_x, y_pos), (width-table_x, y_pos), fill='#cccccc', width=3)
    y_pos += 35
    
    # 今回予想データ（★重要：全て平等表示・一切の強調なし）
    for idx in range(5):
        for digit_idx in range(4):
            x = table_x + col_width * digit_idx + col_width // 2
            col_name = f"第{digit_idx + 1}数字"
            number = str(current_predictions_df.iloc[idx][col_name])
            
            # 一切の強調なし・全て平等
            draw.text((x, y_pos), number, font=number_font, fill='#333333', anchor='mm')
        y_pos += row_height
    
    y_pos += 50
    
    # フッター
    draw.text((width//2, y_pos), "🤖 4種AI統合分析・風車盤パターン・直近24回重点解析", 
              font=footer_font, fill='#666666', anchor='mm')
    y_pos += 45
    draw.text((width//2, y_pos), "※統計分析による予想数字です", 
              font=footer_font, fill='#999999', anchor='mm')
    
    # 保存
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        background.save(output_path, quality=95, optimize=True)
        return output_path
    except Exception as e:
        st.error(f"画像保存エラー: {e}")
        return None

def get_next_drawing_date():
    """次回抽選日を自動計算（平日のみ）"""
    today = datetime.now()
    next_day = today + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    return next_day

# ============================================
# 既存の機能（そのまま保持）
# ============================================

def show_latest_results(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df.columns = [col.replace("(", "（").replace(")", "）") for col in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.fillna("未定義")
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
        df = df.dropna(subset=["抽せん日"])
        df = df.sort_values(by="抽せん日", ascending=False).reset_index(drop=True)

        latest = df.iloc[0]
        global df_recent
        df_recent = df[["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字"]].head(24)

        number_str = f"{latest['第1数字']}{latest['第2数字']}{latest['第3数字']}{latest['第4数字']}"

        st.header("最新の当選番号")
        table_html = f"""
        <table style="width: 80%; margin: 0 auto; border-collapse: collapse; text-align: right;">
            <tr>
                <td style="padding: 10px; font-weight: bold;text-align: left;">回号</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(str(latest['回号']))}回</td>
                <td style="padding: 10px; font-weight: bold;">抽せん日</td>
                <td style="padding: 10px; font-size: 20px;">{latest['抽せん日'].strftime('%Y-%m-%d')}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">当選番号</td>
                <td colspan="3" style="padding: 10px; font-size: 24px; font-weight: bold; color: red; text-align: right;">
                    {number_str}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ストレート</td>
                <td colspan="2">{format_number(latest['ストレート口数'])}口</td>
                <td>{format_number(latest['ストレート当選金額'])}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ボックス</td>
                <td colspan="2">{format_number(latest['ボックス口数'])}口</td>
                <td>{format_number(latest['ボックス当選金額'])}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ストレート</td>
                <td colspan="2">{format_number(latest['セット（ストレート）口数'])}口</td>
                <td>{format_number(latest['セット（ストレート）当選金額'])}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ボックス</td>
                <td colspan="2">{format_number(latest['セット（ボックス）口数'])}口</td>
                <td>{format_number(latest['セット（ボックス）当選金額'])}円</td>
            </tr>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)
        
        return df

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        return None

# 最新結果と df_recent 定義
df_main = show_latest_results(CSV_PATH)

st.header("直近24回の当選番号（ABC分類付き）")

def generate_recent_numbers4_table(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["第1数字", "第2数字", "第3数字", "第4数字"])
        df[["第1数字", "第2数字", "第3数字", "第4数字"]] = df[["第1数字", "第2数字", "第3数字", "第4数字"]].astype(int)
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce").dt.strftime("%Y-%m-%d")

        df_recent = df.sort_values("回号", ascending=False).head(24).reset_index(drop=True)

        def get_abc_rank_map(series):
            counts = series.value_counts().sort_values(ascending=False)
            digits = counts.index.tolist()
            abc_map = {}
            for i, num in enumerate(digits[:10]):
                if i < 4:
                    abc_map[num] = "A"
                elif i < 7:
                    abc_map[num] = "B"
                else:
                    abc_map[num] = "C"
            return abc_map

        abc_map_1 = get_abc_rank_map(df_recent["第1数字"])
        abc_map_2 = get_abc_rank_map(df_recent["第2数字"])
        abc_map_3 = get_abc_rank_map(df_recent["第3数字"])
        abc_map_4 = get_abc_rank_map(df_recent["第4数字"])

        def abc_with_color(d1, d2, d3, d4):
            def colorize(x):
                return f'<span style="color:red;font-weight:bold">{x}</span>' if x == "A" else x
            a1 = colorize(abc_map_1.get(d1, "-"))
            a2 = colorize(abc_map_2.get(d2, "-"))
            a3 = colorize(abc_map_3.get(d3, "-"))
            a4 = colorize(abc_map_4.get(d4, "-"))
            return f"{a1},{a2},{a3},{a4}"

        df_recent["ABC分類"] = df_recent.apply(
            lambda row: abc_with_color(
                row["第1数字"], row["第2数字"], row["第3数字"], row["第4数字"]
            ),
            axis=1
        )

        df_display = df_recent[["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字", "ABC分類"]]
        st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

generate_recent_numbers4_table(CSV_PATH)

st.header("各桁の出現ランキング")
try:
    ranking_df = pd.DataFrame({
        "順位": [f"{i+1}位" for i in range(10)],
        "第1数字": df_recent["第1数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
        "第2数字": df_recent["第2数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
        "第3数字": df_recent["第3数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
        "第4数字": df_recent["第4数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
    })
    st.dataframe(ranking_df, use_container_width=True)
except Exception as e:
    st.error(f"ランキングの表示に失敗しました: {e}")

def show_ai_predictions(csv_path):
    st.header("🎯 ナンバーズ4 AIによる次回数字予測")

    try:
        df = pd.read_csv(csv_path)
        st.write("✅ CSV読み込み成功")
        # データを最新順にソート（show_latest_resultsと同じ処理）
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
        df = df.dropna(subset=["抽せん日"])
        df = df.sort_values(by="抽せん日", ascending=False).reset_index(drop=True)


        df.columns = [col.replace('（', '(').replace('）', ')') for col in df.columns]
        required_cols = ["第1数字", "第2数字", "第3数字", "第4数字"]
        if not all(col in df.columns for col in required_cols):
            st.error("必要なカラムが見つかりません")
            return None, None

        df = df.dropna(subset=required_cols)
        df[required_cols] = df[required_cols].astype(int)

        dfs = {
            "全データ": (df, 0.1),
            "直近100回": (df.tail(100), 0.3),
            "直近24回": (df.tail(24), 0.6)
        }

        wheels = [
            [0, 3, 6, 9, 2, 5, 8, 1, 4, 7],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [0, 7, 4, 1, 8, 5, 2, 9, 6, 3],
            [0, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        ]

        def run_models(df_sub):
            X, ys = [], [[] for _ in range(4)]
            for i in range(len(df_sub) - 1):
                prev = df_sub.iloc[i + 1]
                curr = df_sub.iloc[i]
                X.append([prev[c] for c in required_cols])
                for j in range(4):
                    ys[j].append(curr[required_cols[j]])
            rf_models = [RandomForestClassifier() for _ in range(4)]
            nn_models = [MLPClassifier(max_iter=500) for _ in range(4)]
            for i in range(4):
                rf_models[i].fit(X, ys[i])
                nn_models[i].fit(X, ys[i])
            latest_input = [[df_sub.iloc[0][col] for col in required_cols]]

            def get_top3(model):
                probs = model.predict_proba(latest_input)[0]
                return sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)[:3]

            rf_top3 = [get_top3(m) for m in rf_models]
            nn_top3 = [get_top3(m) for m in nn_models]

            def markov_top3(series):
                trans = defaultdict(Counter)
                for i in range(len(series) - 1):
                    trans[series[i]][series[i+1]] += 1
                last = series[0]
                return [n for n, _ in trans[last].most_common(3)]

            mc_top3 = [markov_top3(df_sub[f"第{i+1}数字"].tolist()) for i in range(4)]

            wheel_top3 = []
            for i in range(4):
                count = Counter()
                wheel = wheels[i]
                for val in df_sub[f"第{i+1}数字"]:
                    pos = wheel.index(val)
                    count[pos] += 1
                top_pos = [p for p, _ in count.most_common(3)]
                wheel_top3.append([wheel[p] for p in top_pos])

            return {"RF": rf_top3, "NN": nn_top3, "MC": mc_top3, "WH": wheel_top3}

        results = {label: run_models(data) for label, (data, _) in dfs.items()}

        def show_models(title, model_dict):
            df_show = pd.DataFrame({
                "第1数字": [", ".join(map(str, model_dict["RF"][0])),
                           ", ".join(map(str, model_dict["NN"][0])),
                           ", ".join(map(str, model_dict["MC"][0])),
                           ", ".join(map(str, model_dict["WH"][0]))],
                "第2数字": [", ".join(map(str, model_dict["RF"][1])),
                           ", ".join(map(str, model_dict["NN"][1])),
                           ", ".join(map(str, model_dict["MC"][1])),
                           ", ".join(map(str, model_dict["WH"][1]))],
                "第3数字": [", ".join(map(str, model_dict["RF"][2])),
                           ", ".join(map(str, model_dict["NN"][2])),
                           ", ".join(map(str, model_dict["MC"][2])),
                           ", ".join(map(str, model_dict["WH"][2]))],
                "第4数字": [", ".join(map(str, model_dict["RF"][3])),
                           ", ".join(map(str, model_dict["NN"][3])),
                           ", ".join(map(str, model_dict["MC"][3])),
                           ", ".join(map(str, model_dict["WH"][3]))],
            }, index=["ランダムフォレスト", "ニューラルネット", "マルコフ", "風車盤"])
            st.subheader(f"📊 {title} 各予測TOP3")
            st.dataframe(
                df_show.style.set_properties(**{'text-align': 'center'}).set_table_styles([
                    {"selector": "th.row_heading", "props": [("min-width", "100px")]}
                ]),
                use_container_width=True
            )

        for label in dfs:
            show_models(label, results[label])

        final_scores = [Counter() for _ in range(4)]
        WH_WEIGHT = 2.0
        RANK_SCORES = [2.0, 1.5, 1.0, 0.7, 0.5]

        for label, (data, weight) in dfs.items():
            model_set = results[label]
            for i in range(4):
                for rank, n in enumerate(model_set["RF"][i]):
                    final_scores[i][n] += (3 - rank) * weight
                for rank, n in enumerate(model_set["NN"][i]):
                    final_scores[i][n] += (3 - rank) * weight
                for rank, n in enumerate(model_set["MC"][i]):
                    final_scores[i][n] += (3 - rank) * weight
                for rank, n in enumerate(model_set["WH"][i]):
                    final_scores[i][n] += (3 - rank) * weight * WH_WEIGHT

        df_recent24 = df.tail(24)
        for i, col in enumerate(required_cols):
            freq_list = df_recent24[col].value_counts().index.tolist()
            for rank, num in enumerate(freq_list[:5]):
                final_scores[i][num] += RANK_SCORES[rank]

                # === TOP5抽出（トリプル除外版・メイン画面用） ===
        ranked_candidates = []
        for i in range(4):
            if len(final_scores[i]) == 0:
                ranked_candidates.append(list(range(10)))
            else:
                ranked_candidates.append([n for n, _ in final_scores[i].most_common(15)])

        final_combinations = []
        attempts = 0
        max_attempts = 2000

        while len(final_combinations) < 5 and attempts < max_attempts:
            combination = []
            for col_idx in range(4):
                candidates = ranked_candidates[col_idx][:10]
                weights = [10 - i for i in range(len(candidates))]
                selected = random.choices(candidates, weights=weights, k=1)[0]
                combination.append(selected)
            
            # トリプル除外判定（核心ロジック）
            counter = Counter(combination)
            if max(counter.values()) <= 2:  # シングル or ダブルのみ許可
                if combination not in final_combinations:
                    final_combinations.append(combination)
            attempts += 1

        # 保険処理
        while len(final_combinations) < 5:
            combo = [random.randint(0, 9) for _ in range(4)]
            if max(Counter(combo).values()) <= 2:
                final_combinations.append(combo)

        df_final = pd.DataFrame({
            "第1数字": [combo[0] for combo in final_combinations],
            "第2数字": [combo[1] for combo in final_combinations],
            "第3数字": [combo[2] for combo in final_combinations],
            "第4数字": [combo[3] for combo in final_combinations],
        }, index=["予想1", "予想2", "予想3", "予想4", "予想5"])

        st.subheader("🏆 各モデル合算スコア TOP5（風車盤＋直近24回ランキング加点強化）")
        st.dataframe(
            df_final.style.set_properties(**{'text-align': 'center'}).set_table_styles([
                {"selector": "th.row_heading", "props": [("min-width", "80px")]}
            ]),
            use_container_width=True
        )
        # ==========================================
        # AI分析用データエクスポート機能（完全版）
        # ==========================================
        st.markdown("---")
        st.subheader("🤖 AI分析用データエクスポート")
        st.info("右上の📄ボタンでワンクリックコピー → AI（Claude/ChatGPT/Gemini）に貼り付け")
        
        # タブで形式を選択
        tab1, tab2, tab3 = st.tabs(["📋 簡単コピー", "📊 JSON形式", "📝 詳細分析用"])
        
        with tab1:
            # シンプルな4桁リスト（最も使いやすい）
            try:
                simple_text = "【ナンバーズ4 AI予測TOP5】\n\n"
                simple_text += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                simple_text += f"次回予想: 第{int(df.iloc[0]['回号']) + 1}回\n\n"
                
                for idx in range(5):
                    nums = [int(df_final.iloc[idx][f'第{i}数字']) for i in range(1, 5)]
                    num_str = ''.join(map(str, nums))
                    total = sum(nums)
                                        # トリプル除外チェック（保険）
                    counter = Counter(nums)
                    if max(counter.values()) >= 3:
                        continue

                    pattern = "シングル" if len(set(nums)) == 4 else "ダブル"

                    simple_text += f"{idx+1}位: {num_str} (合計:{total}, {pattern})\n"
                
                simple_text += f"\n📊 各桁TOP5詳細:\n{df_final.to_string()}"
                st.code(simple_text, language='text')
                
            except Exception as e:
                st.error(f"簡単コピー生成エラー: {e}")
        
        with tab2:
            # JSON形式（プログラム処理用）
            try:
                prediction_data = {
                    "meta": {
                        "generated_at": datetime.now().isoformat(),
                        "current_round": int(df.iloc[0]["回号"]),
                        "next_round": int(df.iloc[0]["回号"]) + 1,
                        "previous_winning": [int(df.iloc[0][f"第{i}数字"]) for i in range(1, 5)]
                    },
                    "ai_predictions": []
                }
                               for idx in range(5):
                    nums = [int(df_final.iloc[idx][f'第{i}数字']) for i in range(1, 5)]
                    
                    # ▼▼▼ トリプル除外チェック（append の前に実行） ▼▼▼
                    counter = Counter(nums)
                    if max(counter.values()) >= 3:
                        continue  # トリプルならスキップ
                    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
                    
                    prediction_data["ai_predictions"].append({
                        "rank": idx + 1,
                        "numbers": nums,
                        "four_digit": ''.join(map(str, nums)),
                        "sum": sum(nums),
                        "pattern": "シングル" if len(set(nums)) == 4 else "ダブル",
                        "odd_count": sum(1 for n in nums if n % 2 == 1),
                        "even_count": sum(1 for n in nums if n % 2 == 0)
                    })

                
                json_str = json.dumps(prediction_data, ensure_ascii=False, indent=2)
                st.code(json_str, language='json')
                
                # ダウンロード機能
                st.download_button(
                    label="📥 JSONファイルダウンロード",
                    data=json_str,
                    file_name=f"numbers4_prediction_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"JSON生成エラー: {e}")
                st.code("エラーが発生しました。簡単コピーをご利用ください。", language='text')
        
        with tab3:
            # 詳細分析用（統計情報含む）
            try:
                # 統計情報の計算
                df_recent_calc = df.head(24)
                s_count = d_count = t_count = 0
                for _, row in df_recent_calc.iterrows():
                    cnts = Counter([row[f"第{i}数字"] for i in range(1, 5)])
                    vals = list(cnts.values())
                    if 3 in vals or 4 in vals:
                        t_count += 1
                    elif vals.count(2) >= 1:
                        d_count += 1
                    else:
                        s_count += 1
                
                prev_winning = '-'.join([str(int(df.iloc[0][f'第{i}数字'])) for i in range(1, 5)])
                prev_sum = sum([int(df.iloc[0][f'第{i}数字']) for i in range(1, 5)])
                
                detailed_text = f"""【ナンバーズ4 詳細分析データ】

=== 基本情報 ===
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
現在回号: 第{int(df.iloc[0]['回号'])}回
次回予想: 第{int(df.iloc[0]['回号']) + 1}回

=== 前回結果 ===
当選番号: {prev_winning}
合計値: {prev_sum}

=== AI予測TOP5 ==="""
                
                for idx in range(5):
                    nums = [int(df_final.iloc[idx][f'第{i}数字']) for i in range(1, 5)]
                    num_str = ''.join(map(str, nums))
                    total = sum(nums)
                                        # トリプル除外チェック
                    counter = Counter(nums)
                    if max(counter.values()) >= 3:
                        continue

                    pattern = "シングル" if len(set(nums)) == 4 else "ダブル"

                                    rank = 1  # 実際に表示される順位カウンター
                for idx in range(5):
                    nums = [int(df_final.iloc[idx][f'第{i}数字']) for i in range(1, 5)]
                    
                    # トリプル除外チェック
                    counter = Counter(nums)
                    if max(counter.values()) >= 3:
                        continue  # トリプルはスキップ
                    
                    num_str = ''.join(map(str, nums))
                    total = sum(nums)
                    pattern = "シングル" if len(set(nums)) == 4 else "ダブル"
                    detailed_text += f"\n{rank}位: {num_str} (合計:{total}, {pattern})"
                    rank += 1  # 実際に表示した時だけカウントアップ


=== 各桁詳細予測 ===
{df_final.to_string()}

=== 直近24回統計 ===
シングル: {s_count}回 ({s_count/24*100:.1f}%)
ダブル: {d_count}回 ({d_count/24*100:.1f}%)
トリプル: {t_count}回 ({t_count/24*100:.1f}%)

=== 分析手法 ===
- ランダムフォレスト（機械学習）
- ニューラルネットワーク（深層学習）
- マルコフ連鎖（確率論）
- 風車盤パターン分析（物理的配置）
- 直近24回重点ランキング
"""
                
                st.code(detailed_text, language='text')
                
            except Exception as e:
                st.error(f"詳細分析生成エラー: {e}")
                st.code("エラーが発生しました。他のタブをご利用ください。", language='text')

        return df, df_final

    except Exception as e:
        st.error("AI予測の実行中にエラーが発生しました")
        st.exception(e)
        return None, None

df_main, df_final = show_ai_predictions(CSV_PATH)

# ============================================
# NAOKIの予想画像生成ボタン（新規追加）
# ============================================

if df_main is not None and df_final is not None:
    st.markdown("---")
    st.header("📸 NAOKIの予想画像生成")
    
    if st.button("🎨 NAOKIの予想画像を生成", type="primary"):
        with st.spinner("科学的バックテスト実行中... 画像生成中..."):
            try:
                # 最新情報取得
                latest_round = int(df_main.iloc[0]["回号"])
                next_round = latest_round + 1
                next_date = get_next_drawing_date()
                
                # 前回当選番号
                previous_winning = [
                    int(df_main.iloc[0]["第1数字"]),
                    int(df_main.iloc[0]["第2数字"]),
                    int(df_main.iloc[0]["第3数字"]),
                    int(df_main.iloc[0]["第4数字"])
                ]
                
                # ★科学的バックテスト：前回予想の生成
                # 最新回(N)を予測するために、N-1回までのデータを使用
                df_for_previous_prediction = df_main.iloc[1:].reset_index(drop=True)
                previous_predictions_df = run_ai_prediction_logic(df_for_previous_prediction)
                
                st.info(f"前回検証: 第{latest_round}回を{len(df_for_previous_prediction)}回分のデータで予測し、実際の結果と照合")
                
                # 画像生成
                image_path = create_naoki_prediction_image(
                    current_predictions_df=df_final,
                    current_round=next_round,
                    current_date=next_date,
                    previous_round=latest_round,
                    previous_winning=previous_winning,
                    previous_predictions_df=previous_predictions_df,
                    output_path=f"output/naoki_prediction_{next_round}.png"
                )
                
                if image_path:
                    st.success(f"✅ 画像生成完了: 第{next_round}回")
                    st.image(image_path, caption=f"NAOKIのナンバーズ4予想（第{next_round}回）", use_column_width=True)
                    
                    # 的中統計表示
                    hit_count = 0
                    for i in range(4):
                        for j in range(5):
                            if previous_predictions_df.iloc[j][f"第{i+1}数字"] == previous_winning[i]:
                                hit_count += 1
                    
                    st.info(f"前回検証結果: {hit_count}/20個の予想数字が的中")
                    
                    # ダウンロードボタン
                    with open(image_path, "rb") as file:
                        st.download_button(
                            label="📥 画像をダウンロード",
                            data=file,
                            file_name=f"naoki_prediction_{next_round}.png",
                            mime="image/png"
                        )
                else:
                    st.error("画像生成に失敗しました")
                    
            except Exception as e:
                st.error(f"画像生成エラー: {e}")
                st.exception(e)

# ============================================
# 既存の分析セクション（そのまま保持）
# ============================================

st.subheader("シングル・ダブル・トリプル分析")
s = d = t = 0
for _, row in df_recent.iterrows():
    cnts = Counter([row[f"第{i}数字"] for i in range(1, 5)])
    vals = list(cnts.values())
    if 3 in vals:
        t += 1
    elif vals.count(2) == 1:
        d += 1
    else:
        s += 1
st.write(pd.DataFrame({
    "タイプ": ["シングル", "ダブル", "トリプル"],
    "回数": [s, d, t]
}))

st.subheader("ひっぱり数字の回数")
hoppari = 0
for i in range(1, len(df_recent)):
    prev = set(df_recent.iloc[i - 1][[f"第{n}数字" for n in range(1, 5)]])
    curr = set(df_recent.iloc[i][[f"第{n}数字" for n in range(1, 5)]])
    if prev & curr:
        hoppari += 1
st.write(f"ひっぱり数字の回数：{hoppari} 回")

st.subheader("数字の範囲ごとの分布")
range_counts = {'0-2': 0, '3-5': 0, '6-9': 0}
for _, row in df_recent.iterrows():
    for i in range(1, 5):
        num = row[f"第{i}数字"]
        if num <= 2:
            range_counts['0-2'] += 1
        elif num <= 5:
            range_counts['3-5'] += 1
        else:
            range_counts['6-9'] += 1
st.write(pd.DataFrame({
    "範囲": list(range_counts.keys()),
    "出現回数": list(range_counts.values())
}))

st.subheader("ペア（2つ組）出現回数")
pair_counts = Counter()
for _, row in df_recent.iterrows():
    nums = [row[f"第{i}数字"] for i in range(1, 5)]
    for i in range(4):
        for j in range(i+1, 4):
            pair = tuple(sorted([nums[i], nums[j]]))
            pair_counts[pair] += 1
pair_df = pd.DataFrame(pair_counts.items(), columns=["ペア", "出現回数"]).sort_values(by="出現回数", ascending=False)
st.dataframe(pair_df)

st.subheader("合計値の出現回数")
sum_counts = Counter()
for _, row in df_recent.iterrows():
    total = sum([row[f"第{i}数字"] for i in range(1, 5)])
    sum_counts[total] += 1
sum_df = pd.DataFrame(sum_counts.items(), columns=["合計値", "出現回数"]).sort_values(by="出現回数", ascending=False)
st.dataframe(sum_df)

st.subheader("スキップ回数分析（数字ごとに直近3回の出現：◯回前）")
try:
    history_map = {i: [] for i in range(10)}
    for idx in range(len(df_recent)):
        row = df_recent.iloc[idx]
        for d in range(1, 5):
            num = row[f"第{d}数字"]
            if idx not in history_map[num]:
                history_map[num].append(idx)

    def format_rank(n):
        return f"{n}回前" if isinstance(n, int) else "出現なし"

    display_rows = []
    for num in range(10):
        last_1 = format_rank(history_map[num][0]) if len(history_map[num]) > 0 else "出現なし"
        last_2 = format_rank(history_map[num][1]) if len(history_map[num]) > 1 else "出現なし"
        last_3 = format_rank(history_map[num][2]) if len(history_map[num]) > 2 else "出現なし"
        display_rows.append({
            "数字": num,
            "直近出現": last_1,
            "2回前出現": last_2,
            "3回前出現": last_3
        })

    skip_df = pd.DataFrame(display_rows)
    st.dataframe(skip_df)

except Exception as e:
    st.error(f"スキップ分析の表示に失敗しました: {e}")

st.header("ナンバーズ4予想（軸数字指定）")
axis = st.selectbox("軸数字を選んでください（0〜9）", list(range(10)))
if st.button("20通りを表示"):
    preds = []
    while len(preds) < 20:
        others = random.sample([i for i in range(10) if i != axis], 3)
        combo = sorted([axis] + others)
        if combo not in preds:
            preds.append(combo)
    st.dataframe(pd.DataFrame(preds, columns=["予測1", "予測2", "予測3", "予測4"]))

st.header("ナンバーズ4予想（AI風ロジック）")
if st.button("AI風ロジックで20通り生成"):
    total_sums = df_recent[[f"第{i}数字" for i in range(1, 5)]].sum(axis=1)
    avg = total_sums.mean()
    med = total_sums.median()
    mode_vals = total_sums.mode().tolist()

    recent_flat = []
    for _, row in df_recent.iterrows():
        recent_flat.extend([row[f"第{i}数字"] for i in range(1, 5)])
    skip_count = {i: None for i in range(10)}
    for idx in range(len(df_recent)):
        row = df_recent.iloc[idx]
        for d in range(1, 5):
            num = row[f"第{d}数字"]
            if skip_count[num] is None:
                skip_count[num] = idx

    def classify_abc(n):
        if n <= 3:
            return "A"
        elif n <= 6:
            return "B"
        else:
            return "C"

    def is_valid_combo(combo):
        total = sum(combo)
        if not (med - 4 <= total <= med + 4):
            return False
        abc_counts = {"A": 0, "B": 0, "C": 0}
        for n in combo:
            abc_counts[classify_abc(n)] += 1
        if max(abc_counts.values()) >= 3:
            return False
        if all(skip_count[n] is not None and skip_count[n] < 3 for n in combo):
            return False
        return True

    predictions = []
    tries = 0
    while len(predictions) < 20 and tries < 1000:
        cand = sorted(random.sample(range(10), 4))
        if cand not in predictions and is_valid_combo(cand):
            predictions.append(cand)
        tries += 1

    if predictions:
        st.success("以下の条件で絞り込まれた予想を表示します：")
        st.markdown("- 合計値：中央値 ±4")
        st.markdown("- ABCバランス（偏りすぎNG）")
        st.markdown("- 最近出ていない数字を優先")
        st.dataframe(pd.DataFrame(predictions, columns=["予測1", "予測2", "予測3", "予測4"]))
    else:
        st.warning("条件に合致する予測が生成できませんでした。")
if st.button("🎨 画像生成テスト"):
    test_predictions = pd.DataFrame({
        "第1数字": [6, 3, 9, 2, 0],
        "第2数字": [5, 1, 9, 4, 3], 
        "第3数字": [2, 7, 1, 0, 8],
        "第4数字": [5, 6, 4, 7, 8]
    })
    
    image_path = create_naoki_prediction_image(
        current_predictions_df=test_predictions,
        current_round=6928,
        current_date=datetime(2026, 2, 26),
        output_path="test.png"
    )
    
    if image_path:
        st.success("✅ 画像生成成功")
        st.image(image_path)
    else:
        st.error("❌ 生成失敗")
