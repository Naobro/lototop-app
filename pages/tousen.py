import streamlit as st
import pandas as pd
import re
from io import StringIO

st.set_page_config(page_title="みずほ抽選結果コピペ解析ツール", layout="wide")
st.title("📥 みずほ銀行 抽選結果コピペ → CSV変換サイト")

# 種別選択
lottery_type = st.selectbox("宝くじの種類を選んでください", ["ロト6", "ロト7", "ミニロト", "ナンバーズ3", "ナンバーズ4"])

# コピペ入力欄
text_input = st.text_area("みずほ銀行の抽選結果をそのままコピペしてください", height=300)

# 正規表現でデータ抽出
def parse_lottery_text(text, kind):
    data = {}
    lines = text.splitlines()
    text = text.replace("\u3000", " ")  # 全角スペース除去

    if kind in ["ロト6", "ロト7", "ミニロト"]:
        try:
            data['回号'] = re.search(r'第(\d+)回', text).group(1)
            data['抽せん日'] = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text).group(1)

            if kind == "ロト6":
                main_match = re.search(r'本数字[\s\n]*((?:\d{1,2}[\s\n]+){5,6}\d{1,2})', text)
                data['本数字'] = ' '.join(re.findall(r'\d{1,2}', main_match.group(1))) if main_match else ''
                bonus_match = re.search(r'ボーナス数字[\s\n]*\(?([0-9]{1,2})\)?', text)
                data['ボーナス数字'] = bonus_match.group(1) if bonus_match else ''
                等級 = ['1等', '2等', '3等', '4等', '5等']

            elif kind == "ロト7":
                main_match = re.search(r'本数字[\s\n]*((?:\d{1,2}[\s\n]+){6}\d{1,2})', text)
                data['本数字'] = ' '.join(re.findall(r'\d{1,2}', main_match.group(1))) if main_match else ''
                bonus_match = re.findall(r'ボーナス数字[\s\n]*\(?([0-9]{1,2})\)?[\s\n]+\(?([0-9]{1,2})\)?', text)
                data['ボーナス数字'] = ' '.join(bonus_match[0]) if bonus_match else ''
                等級 = ['1等', '2等', '3等', '4等', '5等', '6等']

            elif kind == "ミニロト":
                start_index = next((i for i, line in enumerate(lines) if '本数字' in line), -1)
                if start_index >= 0:
                    after_lines = lines[start_index + 1:]
                    all_numbers = re.findall(r'\d{1,2}', '\n'.join(after_lines))
                    data['本数字'] = ' '.join(all_numbers[:5])
                else:
                    data['本数字'] = ''
                bonus_match = re.search(r'\((\d{1,2})\)', text)
                data['ボーナス数字'] = bonus_match.group(1) if bonus_match else ''
                等級 = ['1等', '2等', '3等', '4等']

            if kind in ["ロト6", "ロト7"]:
                carryover_match = re.search(r'キャリーオーバー[\s\n]*([\d,]+円)', text)
                data['キャリーオーバー'] = carryover_match.group(1) if carryover_match else '0円'

            rows = []
            for rank in 等級:
                match = re.search(rf'{rank}\s+(該当なし|[\d,]+口)\s+([\d,]+円)?', text)
                if match:
                    rows.append({
                        '等級': rank,
                        '口数': match.group(1).replace('口', '').strip(),
                        '当選金額': match.group(2) if match.group(2) else '0円'
                    })

            df = pd.DataFrame(rows)
            df['回号'] = data['回号']
            df['抽せん日'] = data['抽せん日']
            df['本数字'] = data['本数字']
            df['ボーナス数字'] = data['ボーナス数字']
            if kind in ["ロト6", "ロト7"]:
                df['キャリーオーバー'] = data['キャリーオーバー']

            return df
        except Exception as e:
            raise ValueError("ロト形式の解析に失敗しました。") from e

    elif kind in ["ナンバーズ3", "ナンバーズ4"]:
        try:
            data['回号'] = re.search(r'第(\d+)回', text).group(1)
            data['抽せん日'] = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text).group(1)
            number_match = re.search(r'(?:抽せん数字|当せん番号)[\s\n]*([0-9]{3,4})', text)
            data['当選番号'] = number_match.group(1) if number_match else ''

            payouts = []
            for label in ['ストレート', 'ボックス', 'セット（ストレート）', 'セット（ボックス）', 'ミニ']:
                match = re.search(rf'{label}\s+([\d,]+)口\s+([\d,]+円)', text)
                if match:
                    payouts.append({
                        'タイプ': label,
                        '口数': match.group(1).replace(',', ''),
                        '当選金額': match.group(2)
                    })

            df = pd.DataFrame(payouts)
            df['回号'] = data['回号']
            df['抽せん日'] = data['抽せん日']
            df['当選番号'] = data['当選番号']
            return df if not df.empty else pd.DataFrame([data])

        except Exception as e:
            raise ValueError("ナンバーズ形式の解析に失敗しました。") from e

    else:
        return pd.DataFrame()

# 解析実行
if st.button("解析して表示"):
    if text_input:
        try:
            df_result = parse_lottery_text(text_input, lottery_type)
            st.success("✅ データを抽出しました")
            st.dataframe(df_result)

            csv = df_result.to_csv(index=False).encode('utf-8')
            st.download_button("💾 CSVとして保存", csv, file_name=f"{lottery_type}_parsed.csv", mime="text/csv")

        except Exception as e:
            st.error(f"⚠️ エラーが発生しました: {e}")
    else:
        st.warning("テキストを入力してください。")
