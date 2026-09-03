import html
import random
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

try:
    from auth import check_password  # type: ignore
except ImportError:
    pass

st.set_page_config(layout="centered")

import pandas as pd

import numbers_common as nc

CSV_PATH = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers4_24.csv"
DIGIT_COUNT = 4


def format_number(val) -> str:
    try:
        return f"{int(float(val)):,}"
    except Exception:
        return "未定義"


# ============================================
# データ読み込み（キャッシュ：毎回GitHubへ再取得しない）
# ============================================
@st.cache_data(ttl=600, show_spinner=False)
def load_data(csv_path: str) -> pd.DataFrame:
    return nc.load_df(csv_path, DIGIT_COUNT)


df = load_data(CSV_PATH)
df_recent = nc.recent(df, 24)
cols = nc.digit_cols(DIGIT_COUNT)

st.title("ナンバーズ4 - 当選番号・統計データ")
st.caption("このページは当選番号と統計データのみを掲載しています。AIによる予想レポートは別途noteで公開予定です。")
st.markdown("---")

# ============================================
# ① 最新の当選番号
# ============================================
def show_latest_results(latest: pd.Series) -> None:
    number_str = "".join(str(int(latest[c])) for c in cols)
    st.header("① 最新の当選番号")
    table_html = f"""
    <table style="width: 80%; margin: 0 auto; border-collapse: collapse; text-align: right;">
        <tr>
            <td style="padding: 10px; font-weight: bold;text-align: left;">回号</td>
            <td style="padding: 10px; font-size: 20px;">{html.escape(str(int(latest['回号'])))}回</td>
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
            <td colspan="2">{format_number(latest['セット(ストレート)口数'])}口</td>
            <td>{format_number(latest['セット(ストレート)当選金額'])}円</td>
        </tr>
        <tr>
            <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ボックス</td>
            <td colspan="2">{format_number(latest['セット(ボックス)口数'])}口</td>
            <td>{format_number(latest['セット(ボックス)当選金額'])}円</td>
        </tr>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)


try:
    show_latest_results(df.iloc[0])
except Exception as e:
    st.error(f"最新結果の表示でエラーが発生しました: {e}")

# ============================================
# ② 直近24回（SAB分類付き）
# ============================================
st.header("② 直近24回の当選番号（SAB分類付き）")
st.caption("SAB分類はロトのページと同じ定義：S=直近24回で5回以上出現 / A=3〜4回 / B=2回以下")
maps = nc.sab_maps(df_recent, DIGIT_COUNT)
sab_table = nc.sab_annotated_table(df_recent, DIGIT_COUNT, maps)
st.write(sab_table.to_html(escape=False, index=False), unsafe_allow_html=True)

# ============================================
# 各桁出現ランキング
# ============================================
st.header("③ 各桁の出現ランキング（直近24回）")
st.dataframe(nc.ranking_table(df_recent, DIGIT_COUNT), use_container_width=True)

# ============================================
# NEW: 偶数・奇数の比率
# ============================================
st.header("④ 偶数・奇数の比率（直近24回）")
st.caption("例：あるパターンが「偶4・奇0」なら4桁とも偶数、というように各回の内訳を出し、24回で集計します。")
parity_df = nc.parity_per_draw(df_recent, DIGIT_COUNT)
pattern_table, overall = nc.parity_summary(parity_df, DIGIT_COUNT)
col1, col2 = st.columns(2)
with col1:
    st.write("回ごとの偶数・奇数パターン")
    st.dataframe(parity_df[["回号", "抽せん日", "偶数", "奇数", "パターン"]], use_container_width=True)
with col2:
    st.write("パターン別の出現回数")
    st.dataframe(pattern_table, use_container_width=True)
    st.metric("偶数の割合", f"{overall['even_pct']:.1f}%", help=f"{overall['even']}/{overall['total_slots']}個")
    st.metric("奇数の割合", f"{overall['odd_pct']:.1f}%", help=f"{overall['odd']}/{overall['total_slots']}個")

# ============================================
# NEW: 合計値のレンジ分布
# ============================================
max_sum = 9 * DIGIT_COUNT
st.header(f"⑤ 合計値のレンジ分布（0〜{max_sum}を3分割・直近24回）")
st.caption(f"各桁0〜9なので、合計値は最小0（{'+'.join(['0'] * DIGIT_COUNT)}=0）〜最大{max_sum}（{'+'.join(['9'] * DIGIT_COUNT)}={max_sum}）の範囲に必ず入ります。")
st.dataframe(nc.sum_range_distribution(df_recent, DIGIT_COUNT), use_container_width=True)

st.markdown("---")

# ============================================
# シングル・ダブル・トリプル分析
# ============================================
st.subheader("シングル・ダブル・トリプル分析（直近24回）")
st.dataframe(pd.DataFrame(list(nc.type_counts(df_recent, DIGIT_COUNT).items()), columns=["タイプ", "回数"]))

# ============================================
# ひっぱり数字の回数
# ============================================
st.subheader("ひっぱり数字の回数（直近24回）")
st.write(f"ひっぱり数字の回数：{nc.hoppari_count(df_recent, DIGIT_COUNT)} 回")

# ============================================
# 数字の範囲ごとの分布
# ============================================
st.subheader("数字の範囲ごとの分布（直近24回）")
range_dist = nc.range_distribution(df_recent, DIGIT_COUNT)
st.dataframe(pd.DataFrame({"範囲": list(range_dist.keys()), "出現回数": list(range_dist.values())}))

# ============================================
# ペア（2つ組）出現回数
# ============================================
st.subheader("ペア（2つ組）出現回数（直近24回）")
st.dataframe(nc.pair_counts(df_recent, DIGIT_COUNT))

# ============================================
# 合計値の出現回数
# ============================================
st.subheader("合計値の出現回数（直近24回）")
st.dataframe(nc.sum_value_counts(df_recent, DIGIT_COUNT))

# ============================================
# スキップ回数分析（数字ごとに直近何回前に出たか）
# ============================================
st.subheader("スキップ回数分析（数字ごとに直近3回の出現：◯回前）")
try:
    history_map = {i: [] for i in range(10)}
    for idx in range(len(df_recent)):
        row = df_recent.iloc[idx]
        for c in cols:
            num = int(row[c])
            if idx not in history_map[num]:
                history_map[num].append(idx)

    def format_rank(n):
        return f"{n}回前" if isinstance(n, int) else "出現なし"

    display_rows = []
    for num in range(10):
        h = history_map[num]
        display_rows.append({
            "数字": num,
            "直近出現": format_rank(h[0]) if len(h) > 0 else "出現なし",
            "2回前出現": format_rank(h[1]) if len(h) > 1 else "出現なし",
            "3回前出現": format_rank(h[2]) if len(h) > 2 else "出現なし",
        })
    st.dataframe(pd.DataFrame(display_rows))
except Exception as e:
    st.error(f"スキップ分析の表示に失敗しました: {e}")

# ============================================
# 軸数字を指定したランダム予測（簡易ツール／AIモデルは使用しない）
# ============================================
st.header("ナンバーズ4予想（軸数字指定・ランダム）")
st.caption("これはAIモデルではなく、指定した軸数字に他3桁をランダムに組み合わせる簡易ツールです。")
axis = st.selectbox("軸数字を選んでください（0〜9）", list(range(10)))
if st.button("20通りを表示"):
    preds = []
    while len(preds) < 20:
        others = random.sample([i for i in range(10) if i != axis], 3)
        combo = sorted([axis] + others)
        if combo not in preds:
            preds.append(combo)
    st.dataframe(pd.DataFrame(preds, columns=["予測1", "予測2", "予測3", "予測4"]))
