import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# ミニロト最新データをスクレイピングする関数
def scrape_miniloto_latest():
    url = "https://takarakuji-loto.jp/miniloto-e.html"  # ミニロトの最新データURL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        print("🚀 ミニロト最新データ取得中...")

        # 抽選情報を取得
        draw_info = soup.find("div", class_="lb bold text16 font1")  # 抽選回と抽選日
        if draw_info is None:
            raise ValueError("❌ 抽選情報が取得できませんでした。HTML構造を確認してください。")
        
        draw_text = draw_info.text.strip()
        print(f"抽選情報: {draw_text}")

        draw_parts = draw_text.split()
        if len(draw_parts) < 5:
            raise ValueError(f"❌ 抽選情報のフォーマットが予期しない形式です: {draw_parts}")

        draw_number = draw_parts[0].replace("第", "").replace("回", "回")
        draw_date = draw_parts[3] + " " + draw_parts[4]

        # 当選番号取得（ミニロトは5つの本数字）
        main_number_section = soup.find("table", class_="rbox rbox1 text14 smp_text12")  # 当選番号のあるtable
        main_numbers = [img["alt"] for img in main_number_section.find_all("img", class_="w_auto")][:5]  # 5つの本数字

        # ボーナス数字取得（ミニロトは1つ）
        bonus_section = soup.find("table", class_="rbox rbox3 text14 smp_text12")  # ボーナス数字のあるtable
        bonus_numbers = [img["alt"] for img in bonus_section.find_all("img")][:1]  # 最初の1つをボーナス数字として取得

        # キャリーオーバー取得
        carry_over = "0円"
        carry_over_row = soup.find("td", text="キャリーオーバー")
        if carry_over_row:
            carry_over = carry_over_row.find_next("td").text.strip()

        # 賞金情報取得
        prize_rows = soup.select("table.tb1 tr")[1:6]  # 1等から5等まで
        prize_data = []
        for row in prize_rows:
            cols = row.find_all("td")
            if len(cols) == 4:
                grade = cols[0].text.strip()
                winners = cols[1].text.strip()
                amount = cols[2].text.strip()
                prize_data.append([grade, winners, amount])

        # データ保存パス
        data_dir = "/Users/naokinishiyama/loto-prediction-app/data"
        os.makedirs(data_dir, exist_ok=True)

        # 最新当選番号CSV保存（上書きモード）
        latest_csv_path = os.path.join(data_dir, "miniloto_latest.csv")
        latest_df = pd.DataFrame({
            "回号": [draw_number],
            "抽せん日": [draw_date],
            "本数字": [" ".join(main_numbers)],
            "ボーナス数字": [", ".join(bonus_numbers) if bonus_numbers else "未取得"],  # ボーナス数字を表示
            "キャリーオーバー": [carry_over]
        })
        latest_df.to_csv(latest_csv_path, index=False, encoding="utf-8-sig", mode="w")

        # 賞金情報CSV保存
        prize_csv_path = os.path.join(data_dir, "miniloto_prizes.csv")
        prize_df = pd.DataFrame(prize_data, columns=["等級", "口数", "当選金額"])
        prize_df["キャリーオーバー"] = carry_over  # キャリーオーバーを追加
        prize_df.to_csv(prize_csv_path, index=False, encoding="utf-8-sig", mode="w")

        # キャリーオーバー情報CSV保存
        carryover_csv_path = os.path.join(data_dir, "miniloto_carryover.csv")
        carry_over_df = pd.DataFrame({"キャリーオーバー": [carry_over]})
        carry_over_df.to_csv(carryover_csv_path, index=False, encoding="utf-8-sig", mode="w")

        print("🎯 ミニロト最新当選番号、賞金情報、キャリーオーバーを 'data/' フォルダに保存しました。✅")

        # データ保存後に即確認
        print("\n📊 最新の当選番号:")
        print(pd.read_csv(latest_csv_path, encoding="utf-8").head())

    except Exception as e:
        print(f"❌ スクレイピングエラー: {e}")

# 実行部分
if __name__ == "__main__":
    scrape_miniloto_latest()