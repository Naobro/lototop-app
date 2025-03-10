import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_numbers():
    url = "https://www.hpfree.com/numbers/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        print("🚀 ナンバーズ3データ取得中...")

        # 回号と抽選日の取得
        title_section = soup.find("h1", class_="topTitle")
        title_text = title_section.text.strip()
        # 回号と抽選日を分割
        round_info = title_text.split("第")[1].split("回")
        round_number = round_info[0]
        draw_date = round_info[1].strip()

        # 当選番号の取得 (正しいimgタグのalt属性から)
        numbers_section = soup.find("div", class_="numbers")  # 'numbers' クラスのdivタグを選択
        images = numbers_section.find_all("img")
        numbers = [img["alt"] for img in images]

        # 当選番号を表示
        print(f"当選番号: {numbers[0]}-{numbers[1]}-{numbers[2]}")

        # 賞金情報の取得 (189行目のtable)
        prize_section = soup.find("section", id="table-Area")
        table = prize_section.find("table", class_="table1")
        rows = table.find_all("tr")

        prize_details = []
        for row in rows[1:]:  # 最初の行はヘッダーなのでスキップ
            cols = row.find_all("td")

            if len(cols) >= 3:  # 必要な列が3つ以上ある行を対象にする
                # 不要な行（販売実績額、リハーサル数字等）はスキップ
                if any(x in cols[0].text for x in ["販売実績額", "リハーサル数字", "裏リハーサル数字", "ナンバーズ風車盤", "ナンバーズ4数字絞り"]):
                    continue

                prize_details.append({
                    "タイプ": cols[0].text.strip(),
                    "当選口数": cols[1].text.strip(),
                    "当選金額": cols[2].text.strip(),
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
        print("🎯 ナンバーズ3の最新当選番号を 'data/' フォルダに保存しました。✅")
        print(f"📊 最新の当選番号: {'-'.join(numbers)}")
        for item in prize_details:
            print(item)

        # DataFrame