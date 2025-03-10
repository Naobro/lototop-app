import pandas as pd
from filelock import FileLock

def update_loto6_50():
    lock_path = "/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv.lock"  # ロック用ファイルパス
    lock = FileLock(lock_path)  # ファイルロックオブジェクト

    try:
        with lock:  # ロックをかけてファイルを操作
            print("ファイルロックを取得しました。")

            # 最新データの読み込み
            latest_df = pd.read_csv("/Users/naokinishiyama/loto-prediction-app/data/loto6_latest.csv")

            # '本数字' 列をスペース区切りで分割して第1数字から第6数字に変換
            latest_df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']] = latest_df['本数字'].str.split(' ', expand=True)

            # 小数点を削除し、整数に変換
            latest_df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']] = latest_df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].astype(int)

            # 必要なカラム（抽せん日と第1〜第6数字）だけを抽出
            latest_df = latest_df[['抽せん日', '第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']]

            # "抽選"の文字を削除
            latest_df['抽せん日'] = latest_df['抽せん日'].str.replace(' 抽選', '')

            # 日付形式を修正（時間部分を削除）
            latest_df['抽せん日'] = pd.to_datetime(latest_df['抽せん日'], format='%Y年%m月%d日').dt.date

            # 最新の日付を「日付」カラムに追加
            latest_date = latest_df.iloc[0]['抽せん日']  # 最新の抽選日
            latest_df['日付'] = latest_date

            # 抽せん日カラムを削除
            latest_df = latest_df.drop(columns=['抽せん日'])

            # 既存のloto6_50.csvの読み込み
            try:
                loto50_df = pd.read_csv("/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv")
            except FileNotFoundError:
                loto50_df = pd.DataFrame(columns=latest_df.columns)  # 新規ファイルの場合は空のDataFrameを作成

            # 最新データをloto6_50.csvの先頭に追加
            updated_loto50_df = pd.concat([latest_df, loto50_df], ignore_index=True)

            # 最新24回分を抽出
            updated_loto50_df = updated_loto50_df.head(24)

            # 新しいloto6_50.csvとして保存
            updated_loto50_df.to_csv("/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv", index=False)

            print("✅ 最新データがloto6_50.csvにコピーされ、最新24回分が表示されました。")
            return updated_loto50_df

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

# 最新24回分のデータを表示
updated_loto50_df = update_loto6_50()
print(updated_loto50_df)