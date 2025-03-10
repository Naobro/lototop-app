import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_numbers():
    url = "https://www.hpfree.com/numbers/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        print("🚀 ナンバーズ4データ取得中...")

        # 回号と抽選日の取得
        title_section = soup.find("h1", class_="topTitle")
        title_text = title_section.text.strip()
        # 回号と抽選日を分割
        round_info = title_text.split("第")[1].split("回")
        round_number = round_info[0]
        draw_date = round_info[1].strip()

        # ナンバーズ4 当選番号の取得 (alt属性から)
        numbers_section = soup.find("section", id="result-Area")
        images = numbers_section.find_all("img")
        
        # ナンバーズ4は4つの画像から抽出
        numbers = [img["alt"] for img in images[:4]]  # 4つの画像を取得
        print(f"ナンバーズ4 当選番号: {'-'.join(numbers)}")

        # 当選口数と配当金の取得 (テーブルから)
        prize_section = soup.find("section", id="table-Area")
        table = prize_section.find("table", class_="table1")
        rows = table.find_all("tr")

        prize_details = []  # すべての行をここに格納する

        # 賞金タイプを手動で指定
        prize_types = ["ストレート", "ボックス", "セット・ストレート", "セット・ボックス", "ミニ"]

        # デバッグ: rowsの内容を確認
        print(f"rows: {len(rows)}")  # rowsの数を確認
        for row in rows:
            print(row.text.strip())  # 各行のテキストを表示

        for idx, row in enumerate(rows[1:]):  # 最初の行はヘッダーなのでスキップ
            cols = row.find_all("td")
            # デバッグ: colsの内容を確認
            print(f"cols: {[col.text.strip() for col in cols]}")  # 各列の内容を表示
            if len(cols) == 2:  # 正しい行は2つのデータを持っている場合
                # "ミニ"の行をスキップ
                if "ミニ" in prize_types[idx]:
                    continue

                prize_details.append({
                    "タイプ": prize_types[idx] if idx < len(prize_types) else "不明",  # 賞金タイプ
                    "当選口数": cols[0].text.strip(),  # 口数
                    "当選金額": cols[1].text.strip(),  # 当選金額
                    "当選番号": "-".join(numbers),  # 当選番号を一緒に保存
                    "回号": round_number,  # 回号
                    "抽選日": draw_date   # 抽選日
                })

        # デバッグ: prize_detailsが空でないか確認
        if not prize_details:
            print("❌ prize_detailsは空です。")
        else:
            print("🎯 データが正常に取得されました。")

        # デバッグ: 当選番号と賞金データを表示
        print("🎯 ナンバーズ4の最新当選番号を 'data/' フォルダに保存しました。✅")
        print(f"📊 最新の当選番号: {'-'.join(numbers)}")
        for item in prize_details:
            print(item)

        # DataFrameに変換してCSVに保存
        data_dir = "/Users/naokinishiyama/loto-prediction-app/data"
        os.makedirs(data_dir, exist_ok=True)

        if prize_details:  # prize_detailsが空でない場合にのみCSVを書き込む
            df_prizes = pd.DataFrame(prize_details)
            numbers_csv_path = os.path.join(data_dir, "numbers_4_latest.csv")
            df_prizes.to_csv(numbers_csv_path, index=False, encoding="utf-8-sig", mode="w")
            print(f"📊 データが {numbers_csv_path} に保存されました。")
        else:
            print("❌ CSVへの書き込みは行いません。")

    except Exception as e:
        print(f"❌ スクレイピングエラー: {e}")

if __name__ == "__main__":
    scrape_numbers()
    import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_numbers3():
    url = "https://www.hpfree.com/numbers/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # ナンバーズ3の当選番号の場所を指定
    numbers_section = soup.find_all("div", class_="numbers")[1]  # 148行目に当たる部分

    # 画像からalt属性を取得
    images = numbers_section.find_all("img")
    
    # 当選番号（最初の3つのimgタグのalt属性を取得）
    numbers3 = [img["alt"] for img in images[0:3]]  # 画像の最初の3つ（alt属性）を取得
    
    # 回号と抽選日を取得
    title_section = soup.find("h1", class_="topTitle")
    title_text = title_section.text.strip()
    round_info = title_text.split("第")[1].split("回")
    round_number = round_info[0]
    draw_date = round_info[1].strip()

    # 賞金データの取得
    prize_section = soup.find_all("section", id="table-Area")[1]
    table = prize_section.find("table", class_="table1")
    rows = table.find_all("tr")

    prize_details = []
    for row in rows[1:]:  # 最初の行（ヘッダー行）はスキップ
        cols = row.find_all("td")
        if len(cols) == 2:  # 正しい行は2つの列を持っている場合
            prize_details.append({
                "タイプ": row.find("th").text.strip(),
                "当選口数": cols[0].text.strip(),
                "当選金額": cols[1].text.strip(),
            })

    # データフレームに変換
    data = {
        "当選番号": "-".join(numbers3),
        "回号": round_number,
        "抽選日": draw_date,
    }

    # 口数と当選金額をデータに追加
    for prize in prize_details:
        prize_type = prize["タイプ"]
        data[f"{prize_type} 口数"] = prize["当選口数"]
        data[f"{prize_type} 当選金額"] = prize["当選金額"]

    # pandas DataFrameに変換
    df = pd.DataFrame([data])

    # CSVに保存
    data_dir = "./data"  # 保存先ディレクトリを設定
    os.makedirs(data_dir, exist_ok=True)
    csv_path = f"{data_dir}/numbers_3_latest.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"📊 データが {csv_path} に保存されました。")

# 実行
get_numbers3()