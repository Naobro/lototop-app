"""
予想レポート生成ツール（社内用・非公開）
=================================================
pages/ フォルダの外に置いているため、Streamlitの左メニュー（公開ページ一覧）には
表示されない。使うときは手元で

    streamlit run predict_report.py

として起動し、生成したテキスト・画像をnoteの記事に貼り付ける、という運用を想定。

無料公開ページ（pages/numbers3_top.py, pages/numbers4_top.py）からは
このファイルも numbers_predict.py も一切importしていないので、
予想ロジックは公開ページから完全に切り離されている。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import streamlit as st
import streamlit.components.v1 as components

import numbers_common as nc
import numbers_predict as npred
from predict_image import create_prediction_image_pair

st.set_page_config(page_title="予想レポート生成（社内用）", layout="centered")

GAMES = {
    "ナンバーズ3": {
        "digit_count": 3,
        "csv_path": "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv",
    },
    "ナンバーズ4": {
        "digit_count": 4,
        "csv_path": "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers4_24.csv",
    },
}


def render_copy_button(text: str, key: str) -> None:
    safe = json.dumps(text)
    components.html(
        f"""
        <div style="font-family:sans-serif; margin-bottom:10px;">
          <button id="copyBtn_{key}" style="
              width:100%; padding:14px; font-size:16px; font-weight:bold;
              color:#fff; background:#1a5490; border:none; border-radius:10px;
              cursor:pointer;">
              📋 note用テキストをコピー
          </button>
          <span id="copyMsg_{key}" style="display:block; margin-top:6px; color:#2e7d32; font-weight:bold;"></span>
        </div>
        <script>
          const data_{key} = {safe};
          document.getElementById("copyBtn_{key}").addEventListener("click", async () => {{
            try {{
              await navigator.clipboard.writeText(data_{key});
              document.getElementById("copyMsg_{key}").textContent = "✅ コピーしました";
            }} catch (e) {{
              const ta = document.createElement("textarea");
              ta.value = data_{key};
              document.body.appendChild(ta);
              ta.select();
              document.execCommand("copy");
              document.body.removeChild(ta);
              document.getElementById("copyMsg_{key}").textContent = "✅ コピーしました";
            }}
          }});
        </script>
        """,
        height=90,
    )


def get_next_drawing_date() -> datetime:
    d = datetime.now() + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


@st.cache_data(ttl=600, show_spinner=False)
def load_data(csv_path: str, digit_count: int):
    return nc.load_df(csv_path, digit_count)


st.title("🔒 予想レポート生成（社内用・note公開素材）")
st.caption("このページは公開ページの一覧には出ません。生成物をnoteに貼り付けて有料公開する運用を想定しています。")

game_name = st.selectbox("対象ゲーム", list(GAMES.keys()))
game = GAMES[game_name]
digit_count = game["digit_count"]

df = load_data(game["csv_path"], digit_count)
df_recent24 = nc.recent(df, 24)
latest_round = int(df.iloc[0]["回号"])

st.write(f"最新回号: 第{latest_round}回 / 予想対象: 第{latest_round + 1}回")

if st.button("🎯 予想レポートを生成する（RF/NN学習＋バックテストのため数十秒かかります）", type="primary"):
    with st.spinner("モデル学習とウォークフォワード検証を実行中..."):
        report_text, joint_top_combos, backtest, combo_explanations = npred.build_prediction_report_text(
            df, digit_count, n_combos=20
        )

        # --- 統計セクション（無料ページと同じ集計＋新規追加分）もnote用テキストに含める ---
        maps = nc.sab_maps(df_recent24, digit_count)
        sab_text, _, _ = nc.sab_stats_text(df_recent24, digit_count, maps)
        parity_df = nc.parity_per_draw(df_recent24, digit_count)
        pattern_table, parity_overall = nc.parity_summary(parity_df, digit_count)
        sum_range_df = nc.sum_range_distribution(df_recent24, digit_count)
        type_counts = nc.type_counts(df_recent24, digit_count)

        stats_lines = ["", "=" * 50, "=== 直近24回の補足統計 ===", ""]
        stats_lines.append(sab_text)
        stats_lines.append("")
        stats_lines.append("=== 偶数・奇数パターン（直近24回） ===")
        for _, row in pattern_table.iterrows():
            stats_lines.append(f"{row['パターン']}: {row['回数']}回")
        stats_lines.append(
            f"全体比率: 偶数 {parity_overall['even']}/{parity_overall['total_slots']} "
            f"({parity_overall['even_pct']:.1f}%) / 奇数 {parity_overall['odd']}/{parity_overall['total_slots']} "
            f"({parity_overall['odd_pct']:.1f}%)"
        )
        stats_lines.append("")
        max_sum = 9 * digit_count
        stats_lines.append(f"=== 合計値レンジ分布（0〜{max_sum}を3分割・直近24回） ===")
        for _, row in sum_range_df.iterrows():
            stats_lines.append(f"{row['合計値レンジ']}: {row['回数']}回")
        stats_lines.append("")
        stats_lines.append("=== タイプ別（直近24回） ===")
        for k, v in type_counts.items():
            stats_lines.append(f"{k}: {v}回")

        full_text = report_text + "\n".join(stats_lines) + "\n" + "=" * 50 + "\n"
        full_text += f"\n（{datetime.now().strftime('%Y-%m-%d %H:%M')} 生成 / 出典データ元: NAOKIのロト・ナンバーズ予想）\n"

    st.success("生成完了")
    st.subheader("📋 note貼り付け用テキスト")
    render_copy_button(full_text, key="report")
    st.code(full_text, language="text")

    st.subheader("📊 各モデルの直近バックテスト的中率")
    bt_rows = []
    for m in ["RF", "NN", "MC", "WH"]:
        bt_rows.append({"モデル": npred.MODEL_NAMES[m], "的中率(%)": round(backtest[m]["hit_rate_pct"], 1)})
    bt_rows.append({"モデル": "ランダム基準(理論値)", "的中率(%)": 30.0})
    st.dataframe(bt_rows, use_container_width=True)

    st.subheader("🖼️ note用画像（10通り×2枚）")
    previous_winning = [int(df.iloc[0][c]) for c in nc.digit_cols(digit_count)]
    combos = [ce["combo"] for ce in combo_explanations]
    combo_meta = [{"sab_pattern": ce["sab_pattern"], "type": ce["type"]} for ce in combo_explanations]
    backtest_summary_text = "\n".join(
        f"{npred.MODEL_NAMES[m]} 的中率 {backtest[m]['hit_rate_pct']:.1f}%（直近{backtest[m]['tested']}回検証・ランダム基準30%）"
        for m in ["RF", "NN", "MC", "WH"]
    )
    next_round = latest_round + 1
    image_paths = create_prediction_image_pair(
        digit_count=digit_count,
        combinations=combos,
        current_round=next_round,
        current_date=get_next_drawing_date(),
        output_path_prefix=f"output/{game_name}_prediction_{next_round}",
        combo_meta=combo_meta,
        previous_round=latest_round,
        previous_winning=previous_winning,
        backtest_summary_text=backtest_summary_text,
        split_size=10,
    )
    if image_paths:
        for i, path in enumerate(image_paths, 1):
            st.image(path, caption=f"{game_name} 予想（第{next_round}回・{i}枚目）", use_container_width=True)
            with open(path, "rb") as f:
                st.download_button(
                    f"📥 {i}枚目をダウンロード", data=f, file_name=os.path.basename(path),
                    mime="image/png", key=f"dl_{i}",
                )
    else:
        st.error("画像生成に失敗しました")
else:
    st.info("上のボタンを押すとレポートを生成します。")
