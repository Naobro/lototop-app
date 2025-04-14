import pandas as pd
import os
import requests
from bs4 import BeautifulSoup

def scrape_loto7_latest():
    url = "https://takarakuji-loto.jp/loto7_tousenp.html"
    
    # キャッシュを無視するためのヘッダー設定
    headers = {
        'Cache-Control': 'no-cache',  # キャッシュを無視
        'Pragma': 'no-cache',         # 古いキャッシュを無視
        'Expires': '0'                # キャッシュの期限を過去に設定
    }

    # リクエストにヘッダーを追加
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("成功: ページが正常に取得されました。")
    else:
        print(f"エラー: HTTP {response.status_code}")
        return  # エラー時はここで関数を終了

    soup = BeautifulSoup(response.content, "html.parser")

    try:
        print("🚀 ロト7最新データ取得中...")

        # HTMLの全行をリストに分割（行ごとの処理）
        html_lines = str(soup).splitlines()

        # 332行目から423行目を取得（インデックスは0から始まる）
        selected_lines = html_lines[331:423]

        # 取得した行を結合して再度HTMLとして扱う
        selected_html = "\n".join(selected_lines)

        # 新しいBeautifulSoupオブジェクトとして処理
        selected_soup = BeautifulSoup(selected_html, "html.parser")

        # 回号「616」の抽選結果セクションを特定
        latest_draw_section = selected_soup.find("div", string="第６１６回　ロト7 当選番号速報")
        
        # 回号「616」の情報が見つからない場合
        if latest_draw_section is None:
            raise ValueError(f"❌ 回号 ６１６ の情報が見つかりませんでした。")

        print(f"最新の抽選結果: 回号 ６１６")

        # 本数字取得
        main_number_imgs = latest_draw_section.find_next("table", class_="rbox1").select("img")  # 本数字の画像を取得
        main_numbers = [img["alt"] for img in main_number_imgs[:7]]  # ロト7は7つの本数字

        # ボーナス数字取得
        bonus_section = latest_draw_section.find_next("table", class_="rbox2").select("img")  # ボーナス数字の画像を選択
        bonus_numbers = [img["alt"] for img in bonus_section[:2]]  # 最初の2つをボーナス数字として取得

        # キャリーオーバー取得
        carry_over = "0円"
        carry_over_rows = latest_draw_section.find_next("table", class_="tb1").select("tr")
        for row in carry_over_rows:
            if "キャリーオーバー" in row.text:
                tds = row.find_all("td")
                if len(tds) >= 2:
                    carry_over = tds[1].text.strip()
                    break

        # 賞金情報取得
        prize_rows = latest_draw_section.find_next("table", class_="tb1").select("tr")[1:6]  # 1等から5等まで
        prize_data = []
        for row in prize_rows:
            cols = row.find_all("td")
            if len(cols) == 4:
                grade = cols[0].text.strip()
                winners = cols[1].text.strip()
                amount = cols[2].text.strip()
                prize_data.append([grade, winners, amount])

        # データ保存パス
        data_dir = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/"
        os.makedirs(data_dir, exist_ok=True)

        # 最新当選番号CSV保存（上書きモード）
        latest_csv_path = os.path.join(data_dir, "loto7_latest.csv")
        latest_df = pd.DataFrame({
            "回号": ["６１６"],
            "本数字": [" ".join(main_numbers)],
            "ボーナス数字": [", ".join(bonus_numbers) if bonus_numbers else "未取得"],
            "キャリーオーバー": [carry_over]
        })
        latest_df.to_csv(latest_csv_path, index=False, encoding="utf-8-sig", mode="w")

        # 賞金情報CSV保存
        prize_csv_path = os.path.join(data_dir, "loto7_prizes.csv")
        prize_df = pd.DataFrame(prize_data, columns=["等級", "口数", "当選金額"])
        prize_df["キャリーオーバー"] = carry_over  # キャリーオーバーを追加
        prize_df.to_csv(prize_csv_path, index=False, encoding="utf-8-sig", mode="w")

        # キャリーオーバー情報CSV保存
        carryover_csv_path = os.path.join(data_dir, "loto7_carryover.csv")
        carry_over_df = pd.DataFrame({"キャリーオーバー": [carry_over]})
        carry_over_df.to_csv(carryover_csv_path, index=False, encoding="utf-8-sig", mode="w")

        print("🎯 ロト7最新当選番号、賞金情報、キャリーオーバーを 'data/' フォルダに保存しました。✅")

        # データ保存後に即確認
        print("\n📊 最新の当選番号:")
        print(pd.read_csv(latest_csv_path, encoding="utf-8").head())

    except Exception as e:
        print(f"❌ スクレイピングエラー: {e}")

# 実行部分
if __name__ == "__main__":
    scrape_loto7_latest()