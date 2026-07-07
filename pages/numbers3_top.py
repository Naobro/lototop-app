import streamlit as st

# authファイルがない場合のエラー回避
try:
    from auth import check_password  # type: ignore
except ImportError:
    pass

st.set_page_config(layout="centered")

import ssl
import pandas as pd
import random
import json
import streamlit.components.v1 as components
from collections import Counter, defaultdict
import html
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

CSV_PATH = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"


# ============================================
# 共通ユーティリティ：マルコフ連鎖・的中率評価
# ============================================

def markov_top3(series):
    trans = defaultdict(Counter)
    for i in range(len(series) - 1):
        trans[series[i]][series[i + 1]] += 1
    if not series:
        return []
    last = series[0]
    return [n for n, _ in trans[last].most_common(3)]


def evaluate_hit_rate(df, required_cols, recent=30):
    """過去データを用いたモデルごとの的中率ウェイト計算（元のロジックを維持）"""
    weights = defaultdict(lambda: [0, 0, 0])
    max_idx = min(recent, len(df) - 1) if len(df) > 1 else 0
    for i in range(max_idx, 1, -1):
        window = df.iloc[i:]
        if len(window) == 0:
            continue
        current = df.iloc[i - 2][required_cols].values.tolist()
        for j, col in enumerate(required_cols):
            rf_top3 = window[col].mode().tolist()[:3]
            if current[j] in rf_top3:
                weights["RF"][j] += 1
            nn_top3 = list(window[col].value_counts().index[:3])
            if current[j] in nn_top3:
                weights["NN"][j] += 1
            mc_top3 = markov_top3(window[col].tolist())
            if current[j] in mc_top3:
                weights["MC"][j] += 1
            wh_top3 = list(window[col].value_counts().index[:3])
            if current[j] in wh_top3:
                weights["WH"][j] += 1
    model_weights = {}
    for model, hits in weights.items():
        total = sum(hits)
        model_weights[model] = [round(h / total, 3) if total else 1 / 3 for h in hits]
    if not model_weights:
        model_weights = {"RF": [1/3]*3, "NN": [1/3]*3, "MC": [1/3]*3, "WH": [1/3]*3}
    for key in ["RF", "NN", "MC", "WH"]:
        model_weights.setdefault(key, [1/3, 1/3, 1/3])
    return model_weights


# ============================================
# 予想モデル（RF/NN/マルコフ/風車盤）＋合算スコアTOP5テキスト生成
# ============================================

def build_prediction_section_text(df):
    """ランダムフォレスト・ニューラルネット・マルコフ連鎖・風車盤の
    各モデル予測TOP3と合算スコアTOP5をテキスト化して返す（ナンバーズ3版）"""
    try:
        required_cols = ["第1数字", "第2数字", "第3数字"]
        wheels = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [0, 7, 4, 1, 8, 5, 2, 9, 6, 3],
            [0, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        ]
        # df は抽せん日／回号の降順（最新が先頭）で渡される前提
        dfs_map = {
            "全データ":   (df,                            0.1),
            "直近100回": (df.head(min(100, len(df))),      0.3),
            "直近24回":  (df.head(min(24,  len(df))),      0.6),
        }

        def run_models_for_text(df_sub):
            X, ys = [], [[] for _ in range(3)]
            for i in range(len(df_sub) - 1):
                prev = df_sub.iloc[i + 1]
                curr = df_sub.iloc[i]
                X.append([prev[c] for c in required_cols])
                for j in range(3):
                    ys[j].append(curr[required_cols[j]])
            if len(X) == 0:
                return None
            latest_input = [[df_sub.iloc[0][c] for c in required_cols]]

            def top3_from_model(model):
                """model.classes_を参照して数字と確率を正確に対応付ける"""
                probs = model.predict_proba(latest_input)[0]
                classes = model.classes_
                pairs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)[:3]
                return [int(c) for c, _ in pairs]

            rf_top3, nn_top3 = [], []
            for i in range(3):
                try:
                    rf = RandomForestClassifier(n_estimators=50, random_state=42)
                    rf.fit(X, ys[i])
                    rf_top3.append(top3_from_model(rf))
                except Exception:
                    rf_top3.append([])
                try:
                    nn = MLPClassifier(max_iter=300, random_state=42)
                    nn.fit(X, ys[i])
                    nn_top3.append(top3_from_model(nn))
                except Exception:
                    nn_top3.append([])

            mc_top3 = [markov_top3(df_sub[f"第{i+1}数字"].tolist()) for i in range(3)]

            wh_top3 = []
            for i in range(3):
                count = Counter()
                wheel = wheels[i]
                for val in df_sub[f"第{i+1}数字"]:
                    if val in wheel:
                        count[wheel.index(val)] += 1
                top_pos = [p for p, _ in count.most_common(3)]
                wh_top3.append([wheel[p] for p in top_pos if p < len(wheel)])

            return {"RF": rf_top3, "NN": nn_top3, "MC": mc_top3, "WH": wh_top3}

        text = "\n=== 次回予想：各モデルTOP3（桁別） ===\n"
        text += "※ RF=ランダムフォレスト / NN=ニューラルネット / MC=マルコフ連鎖 / WH=風車盤\n\n"

        all_results = {}
        for label, (data, weight) in dfs_map.items():
            if len(data) < 5:
                continue
            result = run_models_for_text(data)
            if result is None:
                continue
            all_results[label] = (result, weight)

            text += f"【{label}】\n"
            for model_key, model_name in [
                ("RF", "ランダムフォレスト"),
                ("NN", "ニューラルネット"),
                ("MC", "マルコフ連鎖"),
                ("WH", "風車盤"),
            ]:
                tops = result[model_key]
                row = " / ".join(
                    f"第{i+1}:{','.join(map(str, tops[i])) if tops[i] else '-'}"
                    for i in range(3)
                )
                text += f"  {model_name:<10} {row}\n"
            text += "\n"

        # 合算スコアTOP5（元の numbers3 ロジック：的中率ウェイト × 直近頻出補正）
        model_weights = evaluate_hit_rate(df, required_cols)

        final_scores = [Counter() for _ in range(3)]
        df_recent24 = df.head(min(24, len(df)))
        boost_map = [{} for _ in range(3)]
        for i, col in enumerate(required_cols):
            freq_list = df_recent24[col].value_counts().index.tolist()
            for rank, num in enumerate(freq_list):
                if rank < 4:
                    boost_map[i][num] = 1.2
                elif rank < 7:
                    boost_map[i][num] = 1.1
                else:
                    boost_map[i][num] = 1.0

        for label, (result, weight_df) in all_results.items():
            for i in range(3):
                for model_key in ["RF", "NN", "MC", "WH"]:
                    weight = model_weights[model_key][i]
                    for rank, n in enumerate(result[model_key][i]):
                        score = (3 - rank) * weight_df * weight
                        boost = boost_map[i].get(n, 1.0)
                        final_scores[i][n] += score * boost

        top5_combined = [
            [n for n, _ in final_scores[i].most_common(5)] for i in range(3)
        ]

        text += "=== 合算スコアTOP5（自動学習＋直近頻出補正） ===\n"
        text += "順位  第1数字  第2数字  第3数字\n"
        for rank in range(5):
            d1 = top5_combined[0][rank] if rank < len(top5_combined[0]) else "-"
            d2 = top5_combined[1][rank] if rank < len(top5_combined[1]) else "-"
            d3 = top5_combined[2][rank] if rank < len(top5_combined[2]) else "-"
            text += f"{rank+1}位    {d1}        {d2}        {d3}\n"

        return text, top5_combined
    except Exception as e:
        return f"\n[予想モデルセクション生成エラー: {e}]\n", [[], [], []]


# ============================================
# ★ 最上部：ワンクリックコピーボタン
# ============================================

def build_copy_text(csv_path):
    """最新当選番号・直近24回・各桁ランキング・ABC統計・
    RF/NN/マルコフ/風車盤の予測結果と合算TOP5を
    AIに渡すためのテキストとして組み立てる"""
    try:
        df = pd.read_csv(csv_path)
        df.columns = [c.replace('（', '(').replace('）', ')') for c in df.columns]
        cols = ["第1数字", "第2数字", "第3数字"]
        df = df.dropna(subset=cols)
        df[cols] = df[cols].astype(int)
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
        df = df.dropna(subset=["抽せん日"]).sort_values("抽せん日", ascending=False).reset_index(drop=True)

        latest = df.iloc[0]
        latest_round = int(latest["回号"])
        next_round = latest_round + 1
        prev_winning = "".join(str(int(latest[c])) for c in cols)
        prev_sum = sum(int(latest[c]) for c in cols)

        df24 = df.head(24).reset_index(drop=True)

        text = "【ナンバーズ3 直近データ（AI貼り付け用）】\n"
        text += f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        text += f"最新回号: 第{latest_round}回 / 次回: 第{next_round}回\n"
        text += f"最新当選番号: {prev_winning}（合計 {prev_sum}）\n\n"

        # 直近24回の当選番号
        text += "=== 直近24回の当選番号 ===\n"
        text += "回号  抽せん日  第1 第2 第3\n"
        for _, row in df24.iterrows():
            text += (f"{int(row['回号'])}  {row['抽せん日'].strftime('%Y-%m-%d')}  "
                     f"{int(row['第1数字'])} {int(row['第2数字'])} {int(row['第3数字'])}\n")

        # 各桁出現ランキング
        text += "\n=== 各桁出現ランキング（直近24回・回数）===\n"
        text += "順位  第1数字  第2数字  第3数字\n"
        rankings = []
        for i in range(1, 4):
            vc = df24[f"第{i}数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False)
            rankings.append(vc)
        for rank in range(10):
            text += f"{rank+1}位 "
            for i in range(3):
                num = rankings[i].index[rank]
                cnt = rankings[i].iloc[rank]
                text += f"  {num}({cnt})"
            text += "\n"

        # ABC統計（3桁 × 24回 = 72が母数）
        abc_sets = []
        for i in range(3):
            order = rankings[i].index.tolist()
            abc_sets.append({"A": set(order[0:3]), "B": set(order[3:6]), "C": set(order[6:10])})
        abc_counts = {"A": 0, "B": 0, "C": 0}
        for _, row in df24.iterrows():
            for i in range(3):
                v = int(row[f"第{i+1}数字"])
                if v in abc_sets[i]["A"]:
                    abc_counts["A"] += 1
                elif v in abc_sets[i]["B"]:
                    abc_counts["B"] += 1
                else:
                    abc_counts["C"] += 1
        total_abc = 72
        text += "\n=== 直近24回 ABC出現統計 ===\n"
        text += "A(1-3位):頻出 / B(4-6位):中位 / C(7-10位):低頻出\n"
        for k in ["A", "B", "C"]:
            text += f"{k}数字: {abc_counts[k]}回 ({abc_counts[k]/total_abc*100:.1f}%)\n"

        # シングル/ダブル統計
        s = d = 0
        for _, row in df24.iterrows():
            nums = [int(row[f"第{i}数字"]) for i in range(1, 4)]
            if len(set(nums)) == 3:
                s += 1
            else:
                d += 1
        text += "\n=== 直近24回 タイプ別 ===\n"
        text += f"シングル(S): {s}回 / ダブル(W): {d}回\n"

        # ★ RF・NN・マルコフ・風車盤の予測結果と合算TOP5を追加
        text += "\n" + "=" * 50 + "\n"
        prediction_text, _ = build_prediction_section_text(df.copy())
        text += prediction_text
        text += "=" * 50 + "\n"

        text += "\n（出典: https://naobillionaire.synergy.cfbx.jp/ ）\n"
        return text
    except Exception as e:
        return f"データ取得エラー: {e}"


def render_copy_button(text):
    safe = json.dumps(text)
    components.html(f"""
    <div style="font-family:sans-serif; margin-bottom:10px;">
      <button id="copyBtn" style="
          width:100%; padding:16px; font-size:18px; font-weight:bold;
          color:#fff; background:#1a5490; border:none; border-radius:10px;
          cursor:pointer; box-shadow:0 3px 8px rgba(0,0,0,0.2);">
          📋 AIに渡すデータをコピー
      </button>
      <span id="copyMsg" style="display:block; margin-top:8px; color:#2e7d32; font-weight:bold;"></span>
    </div>
    <script>
      const data = {safe};
      const btn = document.getElementById("copyBtn");
      const msg = document.getElementById("copyMsg");
      btn.addEventListener("click", async () => {{
        try {{
          await navigator.clipboard.writeText(data);
          msg.textContent = "✅ コピーしました！AI（Claude/ChatGPT/Gemini）に貼り付けてください";
        }} catch (e) {{
          const ta = document.createElement("textarea");
          ta.value = data;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          document.body.removeChild(ta);
          msg.textContent = "✅ コピーしました！";
        }}
      }});
    </script>
    """, height=110)


# ★ タイトルと最上部コピーボタン
st.title("ナンバーズ3 - 当選予想ページ")
_copy_text = build_copy_text(CSV_PATH)
render_copy_button(_copy_text)
with st.expander("コピーされる内容を確認する"):
    st.code(_copy_text, language="text")
st.markdown("---")


# ============================================
# 最新の当選結果表示
# ============================================

def show_latest_results(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df.columns = [col.replace("(", "（").replace(")", "）") for col in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.fillna("未定義")
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
        df = df.dropna(subset=["抽せん日"])

        latest = df.sort_values(by="抽せん日", ascending=False).iloc[0]
        number_str = f"{latest['第1数字']}{latest['第2数字']}{latest['第3数字']}"

        st.header("① 最新の当選番号")
        table_html = f"""
        <table style="width: 80%; margin: 0 auto; border-collapse: collapse; text-align: right;">
            <tr>
                <td style="padding: 10px; font-weight: bold;text-align: left;">回号</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(str(latest['回号']))}回</td>
                <td style="padding: 10px; font-weight: bold;">抽せん日</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(latest['抽せん日'].strftime('%Y-%m-%d'))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">当選番号</td>
                <td colspan="3" style="padding: 10px; font-size: 24px; font-weight: bold; color: red; text-align: right;">
                    {number_str}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ストレート</td>
                <td colspan="2">{html.escape(str(latest['ストレート口数']))}口</td>
                <td>{html.escape(str(latest['ストレート当選金額']))}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ボックス</td>
                <td colspan="2">{html.escape(str(latest['ボックス口数']))}口</td>
                <td>{html.escape(str(latest['ボックス当選金額']))}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ストレート</td>
                <td colspan="2">{html.escape(str(latest['セット（ストレート）口数']))}口</td>
                <td>{html.escape(str(latest['セット（ストレート）当選金額']))}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ボックス</td>
                <td colspan="2">{html.escape(str(latest['セット（ボックス）口数']))}口</td>
                <td>{html.escape(str(latest['セット（ボックス）当選金額']))}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ミニ</td>
                <td colspan="2">{html.escape(str(latest['ミニ口数']))}口</td>
                <td>{html.escape(str(latest['ミニ当選金額']))}円</td>
            </tr>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.error(f"エラー詳細: {type(e)}")


show_latest_results(CSV_PATH)


# ============================================
# 直近24回（ABC分類付き）
# ============================================

st.header("② 直近24回の当選番号（ABC分類付き）")

def generate_recent_numbers3_table(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["第1数字", "第2数字", "第3数字"])
        df[["第1数字", "第2数字", "第3数字"]] = df[["第1数字", "第2数字", "第3数字"]].astype(int)
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

        def abc_with_color(d1, d2, d3):
            def colorize(x):
                return f'<span style="color:red;font-weight:bold">{x}</span>' if x == "A" else x
            a1 = colorize(abc_map_1.get(d1, "-"))
            a2 = colorize(abc_map_2.get(d2, "-"))
            a3 = colorize(abc_map_3.get(d3, "-"))
            return f"{a1},{a2},{a3}"

        df_recent["ABC分類"] = df_recent.apply(
            lambda row: abc_with_color(row["第1数字"], row["第2数字"], row["第3数字"]),
            axis=1
        )
        df_display = df_recent[["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "ABC分類"]]
        st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

generate_recent_numbers3_table(CSV_PATH)


# ============================================
# ランキング
# ============================================

st.header("ランキング")

def generate_ranking(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        df = df.sort_values("回号", ascending=False).head(24)

        def rank_counts(series):
            counts = series.value_counts().sort_values(ascending=False)
            df_rank = counts.reset_index()
            df_rank.columns = ["数字", "出現回数"]
            df_rank["順位"] = df_rank["出現回数"].rank(method="dense", ascending=False).astype(int)
            return df_rank.sort_values(["順位", "数字"]).reset_index(drop=True)

        def expand_top_ranks(ranking_df, max_rank=5):
            return ranking_df[ranking_df["順位"] <= max_rank].sort_values(["順位", "数字"]).reset_index(drop=True)

        top_1st = expand_top_ranks(rank_counts(df["第1数字"]))
        top_2nd = expand_top_ranks(rank_counts(df["第2数字"]))
        top_3rd = expand_top_ranks(rank_counts(df["第3数字"]))

        max_len = max(len(top_1st), len(top_2nd), len(top_3rd))
        fill = lambda lst: lst + [""] * (max_len - len(lst))

        combined_df = pd.DataFrame({
            "順位": [f"{i+1}位" for i in range(max_len)],
            "第1桁目": fill([f"{row['数字']}（{row['出現回数']}回）" for _, row in top_1st.iterrows()]),
            "第2桁目": fill([f"{row['数字']}（{row['出現回数']}回）" for _, row in top_2nd.iterrows()]),
            "第3桁目": fill([f"{row['数字']}（{row['出現回数']}回）" for _, row in top_3rd.iterrows()])
        })

        def highlight(row):
            if row["順位"] in ["1位", "2位", "3位"]:
                return ['background-color: gold; color: black; font-weight: bold; text-align: center'] * len(row)
            return ['text-align: center'] * len(row)

        st.write(combined_df.style.apply(highlight, axis=1).set_properties(**{'text-align': 'center'}))

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")

generate_ranking(CSV_PATH)


# ============================================
# 分析セクション（AIによる予測）
# ============================================

st.header("分析セクション")

def show_ai_predictions(csv_path):
    st.header("🎯 ナンバーズ3 AIによる次回数字予測")

    try:
        df = pd.read_csv(csv_path)
        st.write("✅ CSV読み込み成功")

        df.columns = [col.replace('（', '(').replace('）', ')') for col in df.columns]
        required_cols = ["第1数字", "第2数字", "第3数字"]
        if not all(col in df.columns for col in required_cols):
            st.error("必要なカラムが見つかりません")
            return None, None

        df = df.dropna(subset=required_cols)
        df[required_cols] = df[required_cols].astype(int)
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
        df = df.dropna(subset=["抽せん日"]).sort_values("抽せん日", ascending=False).reset_index(drop=True)

        dfs = {
            "全データ":   (df,                        0.1),
            "直近100回": (df.head(min(100, len(df))),  0.3),
            "直近24回":  (df.head(min(24,  len(df))),  0.6)
        }

        wheels = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [0, 7, 4, 1, 8, 5, 2, 9, 6, 3],
            [0, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        ]

        def run_models(df_sub):
            X, ys = [], [[] for _ in range(3)]
            for i in range(len(df_sub) - 1):
                prev = df_sub.iloc[i + 1]
                curr = df_sub.iloc[i]
                X.append([prev[c] for c in required_cols])
                for j in range(3):
                    ys[j].append(curr[required_cols[j]])
            rf_models = [RandomForestClassifier(random_state=42) for _ in range(3)]
            nn_models = [MLPClassifier(max_iter=500, random_state=42) for _ in range(3)]
            for i in range(3):
                rf_models[i].fit(X, ys[i])
                nn_models[i].fit(X, ys[i])
            latest_input = [[df_sub.iloc[0][col] for col in required_cols]]

            def get_top3(model):
                """model.classes_を参照して数字と確率を正確に対応付ける"""
                probs = model.predict_proba(latest_input)[0]
                classes = model.classes_
                pairs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)[:3]
                return [int(c) for c, _ in pairs]

            rf_top3 = [get_top3(m) for m in rf_models]
            nn_top3 = [get_top3(m) for m in nn_models]
            mc_top3_list = [markov_top3(df_sub[f"第{i+1}数字"].tolist()) for i in range(3)]

            wheel_top3 = []
            for i in range(3):
                count = Counter()
                wheel = wheels[i]
                for val in df_sub[f"第{i+1}数字"]:
                    pos = wheel.index(val)
                    count[pos] += 1
                top_pos = [p for p, _ in count.most_common(3)]
                wheel_top3.append([wheel[p] for p in top_pos])

            return {"RF": rf_top3, "NN": nn_top3, "MC": mc_top3_list, "WH": wheel_top3}

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

        model_weights = evaluate_hit_rate(df, required_cols)

        final_scores = [Counter() for _ in range(3)]

        df_recent24 = df.head(min(24, len(df)))
        boost_map = [{} for _ in range(3)]
        for i, col in enumerate(required_cols):
            freq_list = df_recent24[col].value_counts().index.tolist()
            for rank, num in enumerate(freq_list):
                if rank < 4:
                    boost_map[i][num] = 1.2
                elif rank < 7:
                    boost_map[i][num] = 1.1
                else:
                    boost_map[i][num] = 1.0

        for label, (data, weight_df) in dfs.items():
            model_set = results[label]
            for i in range(3):
                for model_key in ["RF", "NN", "MC", "WH"]:
                    weight = model_weights[model_key][i]
                    for rank, n in enumerate(model_set[model_key][i]):
                        score = (3 - rank) * weight_df * weight
                        boost = boost_map[i].get(n, 1.0)
                        final_scores[i][n] += score * boost

        top5_combined = [
            [n for n, _ in final_scores[i].most_common(5)] for i in range(3)
        ]

        df_final = pd.DataFrame({
            "第1数字": top5_combined[0],
            "第2数字": top5_combined[1],
            "第3数字": top5_combined[2],
        }, index=["第1位🥇", "第2位🥈", "第3位🥉", "第4位⭐", "第5位⭐"])

        st.subheader("🏆 各モデル合算スコア TOP5（自動学習＋直近頻出補正）")
        st.dataframe(
            df_final.style.set_properties(**{'text-align': 'center'}).set_table_styles([
                {"selector": "th.row_heading", "props": [("min-width", "80px")]}
            ]),
            use_container_width=True
        )

        # ============================================
        # ★ AI分析用データエクスポート（タブ形式）
        # ============================================
        st.markdown("---")
        st.subheader("🤖 AI分析用データエクスポート")
        st.info("以下をコピー → AI（Claude/ChatGPT/Gemini）に貼り付け")

        tab1, tab2, tab3 = st.tabs(["📋 簡単コピー", "📊 JSON形式", "📝 詳細分析用"])

        with tab1:
            try:
                simple_text = "【ナンバーズ3 集計データTOP5】\n\n"
                simple_text += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                simple_text += f"次回: 第{int(df.iloc[0]['回号']) + 1}回\n\n"
                simple_text += "=== 合算スコアTOP5 ===\n"
                simple_text += "順位  第1数字  第2数字  第3数字\n"
                for rank in range(5):
                    d1 = top5_combined[0][rank] if rank < len(top5_combined[0]) else "-"
                    d2 = top5_combined[1][rank] if rank < len(top5_combined[1]) else "-"
                    d3 = top5_combined[2][rank] if rank < len(top5_combined[2]) else "-"
                    simple_text += f"{rank+1}位    {d1}        {d2}        {d3}\n"
                simple_text += f"\n各桁TOP5詳細:\n{df_final.to_string()}"

                # ★ 予想モデルセクション（RF/NN/MC/WH＋合算TOP5）を追加
                prediction_text, _ = build_prediction_section_text(df.copy())
                simple_text += "\n\n" + "=" * 50 + "\n"
                simple_text += prediction_text
                simple_text += "=" * 50 + "\n"

                st.code(simple_text, language='text')
            except Exception as e:
                st.error(f"簡単コピー生成エラー: {e}")

        with tab2:
            try:
                prediction_data = {
                    "meta": {
                        "generated_at": datetime.now().isoformat(),
                        "current_round": int(df.iloc[0]["回号"]),
                        "next_round": int(df.iloc[0]["回号"]) + 1,
                        "previous_winning": [int(df.iloc[0][f"第{i}数字"]) for i in range(1, 4)]
                    },
                    "top5_by_digit": {
                        "第1数字": top5_combined[0],
                        "第2数字": top5_combined[1],
                        "第3数字": top5_combined[2],
                    }
                }
                json_str = json.dumps(prediction_data, ensure_ascii=False, indent=2)
                st.code(json_str, language='json')
                st.download_button(
                    label="📥 JSONファイルダウンロード",
                    data=json_str,
                    file_name=f"numbers3_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"JSON生成エラー: {e}")

        with tab3:
            try:
                df_recent_calc = df.head(24)
                s_count = d_count = 0
                for _, row in df_recent_calc.iterrows():
                    nums = [row[f"第{i}数字"] for i in range(1, 4)]
                    if len(set(nums)) == 3:
                        s_count += 1
                    else:
                        d_count += 1

                prev_winning_str = '-'.join([str(int(df.iloc[0][f'第{i}数字'])) for i in range(1, 4)])
                prev_sum = sum([int(df.iloc[0][f'第{i}数字']) for i in range(1, 4)])

                ranking_text = "\n=== 各桁出現ランキング（直近24回）===\n"
                ranking_text += "順位  第1数字(回) 第2数字(回) 第3数字(回)\n"
                digit_rankings = []
                abc_sets_local = []
                for i in range(1, 4):
                    col_name = f"第{i}数字"
                    value_counts = df_recent_calc[col_name].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False)
                    ranking = value_counts.index.tolist()
                    digit_rankings.append(ranking)
                    abc_sets_local.append({'A': set(ranking[0:3]), 'B': set(ranking[3:6]), 'C': set(ranking[6:10])})
                for rank in range(10):
                    ranking_text += f"{rank+1}位   "
                    for digit_idx in range(3):
                        num = digit_rankings[digit_idx][rank]
                        count = df_recent_calc[f"第{digit_idx+1}数字"].value_counts().get(num, 0)
                        ranking_text += f"  {num}  ({count})    "
                    ranking_text += "\n"

                abc_counts_local = {'A': 0, 'B': 0, 'C': 0}
                for _, row in df_recent_calc.iterrows():
                    for i in range(3):
                        val = int(row[f"第{i+1}数字"])
                        if val in abc_sets_local[i]['A']:
                            abc_counts_local['A'] += 1
                        elif val in abc_sets_local[i]['B']:
                            abc_counts_local['B'] += 1
                        else:
                            abc_counts_local['C'] += 1
                abc_text = "\n=== 直近24回 ABC出現統計 ===\n"
                abc_text += "【定義】A(1-3位):頻出 / B(4-6位):中位 / C(7-10位):低頻出\n\n"
                total_digits = 72
                for rank_char in ['A', 'B', 'C']:
                    count = abc_counts_local[rank_char]
                    percent = (count / total_digits) * 100
                    abc_text += f"{rank_char}数字: {count:2}回 ({percent:5.1f}%) - 1回平均 {count/24:.1f}個\n"

                latest_abc = []
                prev_nums_local = [int(df.iloc[0][f'第{i}数字']) for i in range(1, 4)]
                for i in range(3):
                    val = prev_nums_local[i]
                    if val in abc_sets_local[i]['A']:
                        latest_abc.append("A")
                    elif val in abc_sets_local[i]['B']:
                        latest_abc.append("B")
                    else:
                        latest_abc.append("C")
                abc_text += f"\n前回パターン: {','.join(latest_abc)} ({prev_winning_str})"

                detailed_text = f"""【ナンバーズ3 詳細集計データ】

=== 基本情報 ===
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
現在回号: 第{int(df.iloc[0]['回号'])}回
次回: 第{int(df.iloc[0]['回号']) + 1}回

=== 前回結果 ===
当選番号: {prev_winning_str}
合計値: {prev_sum}

=== 合算スコアTOP5 ===
"""
                for rank in range(5):
                    d1 = top5_combined[0][rank] if rank < len(top5_combined[0]) else "-"
                    d2 = top5_combined[1][rank] if rank < len(top5_combined[1]) else "-"
                    d3 = top5_combined[2][rank] if rank < len(top5_combined[2]) else "-"
                    detailed_text += f"{rank+1}位: {d1}{d2}{d3}\n"

                detailed_text += f"""
=== 各桁詳細 ===
{df_final.to_string()}
{ranking_text}
{abc_text}

=== 直近24回統計 ===
シングル(S): {s_count}回 ({s_count/24*100:.1f}%)
ダブル(W): {d_count}回 ({d_count/24*100:.1f}%)
"""
                # ★ 予想モデルセクション（RF/NN/MC/WH＋合算TOP5）を追加
                prediction_text, _ = build_prediction_section_text(df.copy())
                detailed_text += "\n" + "=" * 50 + "\n"
                detailed_text += prediction_text
                detailed_text += "=" * 50 + "\n"

                st.code(detailed_text, language='text')
            except Exception as e:
                st.error(f"詳細分析生成エラー: {e}")

        return df, df_final

    except Exception as e:
        st.error("AI予測の実行中にエラーが発生しました")
        st.exception(e)
        return None, None


# ★ 修正：以前の show_page_ai() は "data/n3.csv" という存在しないパスを参照していたため削除し、
#          CSV_PATH を直接渡すように統一
show_ai_predictions(CSV_PATH)


# ============================================
# 各種分析セクション（ソート規約を統一）
# ============================================

st.subheader("直近24回のWとSの回数")

def generate_w_and_s(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        df_recent = df.sort_values("回号", ascending=False).head(24)

        w_count = 0
        s_count = 0

        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字']]
            if len(set(numbers)) == 2:
                w_count += 1
            elif len(set(numbers)) == 3:
                s_count += 1

        result_df = pd.DataFrame({
            "分析項目": ["W（ダブル）", "S（シングル）"],
            "回数": [w_count, s_count]
        })
        st.write(result_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

generate_w_and_s(CSV_PATH)


st.subheader("直近24回のひっぱり回数")

def generate_hoppari_numbers(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        # 新しい順にソートしてから直近24回を取得
        df_recent = df.sort_values("回号", ascending=False).head(24).reset_index(drop=True)

        hoppari_count = 0
        # df_recent は index 0 が最新。i を新しい方、i+1 を1つ古い方として比較する
        for i in range(len(df_recent) - 1):
            current_numbers = {df_recent.iloc[i]['第1数字'], df_recent.iloc[i]['第2数字'], df_recent.iloc[i]['第3数字']}
            previous_numbers = {df_recent.iloc[i+1]['第1数字'], df_recent.iloc[i+1]['第2数字'], df_recent.iloc[i+1]['第3数字']}
            if len(current_numbers.intersection(previous_numbers)) > 0:
                hoppari_count += 1

        result_df = pd.DataFrame({
            "分析項目": ["ひっぱり数字"],
            "回数": [hoppari_count]
        })
        st.write(result_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

generate_hoppari_numbers(CSV_PATH)


st.subheader("直近24回の数字の分布（範囲ごとの分布）")

def generate_range_distribution(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        df_recent = df.sort_values("回号", ascending=False).head(24)

        range_counts = {'A (0-2)': 0, 'B (3-5)': 0, 'C (6-9)': 0}

        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字']]
            for num in numbers:
                if 0 <= num <= 2:
                    range_counts['A (0-2)'] += 1
                elif 3 <= num <= 5:
                    range_counts['B (3-5)'] += 1
                elif 6 <= num <= 9:
                    range_counts['C (6-9)'] += 1

        result_df = pd.DataFrame({
            "範囲": list(range_counts.keys()),
            "出現回数": list(range_counts.values())
        })
        st.write(result_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

generate_range_distribution(CSV_PATH)


st.subheader("直近24回の組み合わせパターン（ペア）のカウント")

def generate_combinations(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        df_recent = df.sort_values("回号", ascending=False).head(24)

        pair_counts = Counter()

        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字']]
            for i in range(len(numbers)):
                for j in range(i + 1, len(numbers)):
                    pair = tuple(sorted([numbers[i], numbers[j]]))
                    pair_counts[pair] += 1

        pair_df = pd.DataFrame(pair_counts.items(), columns=["ペア", "出現回数"]).sort_values(by="出現回数", ascending=False).reset_index(drop=True)

        st.write("ペアの出現回数：")
        st.write(pair_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

generate_combinations(CSV_PATH)


st.subheader("直近24回の数字の合計値の分析")

def generate_sum_analysis(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        df_recent = df.sort_values("回号", ascending=False).head(24)

        sum_counts = Counter()

        for _, row in df_recent.iterrows():
            total = row['第1数字'] + row['第2数字'] + row['第3数字']
            sum_counts[total] += 1

        sum_df = pd.DataFrame(sum_counts.items(), columns=["合計値", "出現回数"]).sort_values(by="出現回数", ascending=False).reset_index(drop=True)

        st.write("数字の合計値の出現回数：")
        st.write(sum_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

generate_sum_analysis(CSV_PATH)


# ============================================
# 予測セクション（軸数字指定）
# ============================================

st.header("ナンバーズ3 予測")
st.write("軸数字を1つ選択")

def generate_random_predictions(n, axis_number):
    predictions = []
    for _ in range(n):
        prediction = [
            axis_number,
            random.choice([i for i in range(10) if i != axis_number]),
            random.choice([i for i in range(10) if i != axis_number])
        ]
        prediction = sorted(prediction)
        if prediction not in predictions:
            predictions.append(prediction)
    return predictions

axis_number = st.selectbox("軸数字を選択 (0〜9)", list(range(10)), key="axis_number")
num_predictions = 20

if st.button("20パターン予測", key="random_predict_button"):
    random_predictions = generate_random_predictions(num_predictions, axis_number)
    st.write("ランダム予測 (20パターン)：")
    df_random_predictions = pd.DataFrame(random_predictions, columns=[f'予測番号{i+1}' for i in range(3)])
    st.dataframe(df_random_predictions)
