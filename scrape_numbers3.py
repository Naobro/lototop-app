import requests
from bs4 import BeautifulSoup

def get_numbers3():
    url = "https://www.hpfree.com/numbers/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # ---------- 1. ナンバーズ3の当選番号部分（変更しない） ----------
    # Numbers3の当選番号は、148行目に当たる<div class="numbers">内の画像から取得
    numbers_section = soup.find_all("div", class_="numbers")[1]  # 148行目に当たる部分
    images = numbers_section.find_all("img")
    # 当選番号は最初の3つのimgタグのalt属性を取得（例：「1-2-8」など）
    numbers3 = [img["alt"] for img in images[0:3]]
    print("ナンバーズ3 当選番号:", "-".join(numbers3))

    # ---------- 2. 回号と抽選日を取得 ----------
    title_section = soup.find("h1", class_="topTitle")
    title_text = title_section.text.strip()
    # 「第6677回2025年3月7日(金)」の形式で回号と抽選日を抽出
    round_info = title_text.split("第")[1].split("回")
    round_number = round_info[0]
    draw_date = round_info[1].strip()
    print(f"回号: {round_number}, 抽選日: {draw_date}")

    # ---------- 3. ナンバーズ3の賞金データ部分（ストレート、ボックスなど） ----------
    prize_sections = soup.find_all("section", id="table-Area")
    if len(prize_sections) < 2:
        print("Numbers3の賞金一覧セクションが見つかりません。")
        return
    prize_section = prize_sections[1]  # Numbers3の賞金一覧セクション
    table = prize_section.find("table", class_="table1")
    rows = table.find_all("tr")  # テーブルの全行を取得
    
    prize_details = []
    for row in rows[1:]:
        cols = row.find_all("td")
        # 正常なデータ行は、口数と金額が2つの<td>を持つはず
        if len(cols) == 2:
            # 賞金タイプは<td>ではなく<th>に入っているはず
            th = row.find("th")
            if th is None:
                continue
            prize_type = th.text.strip()
            # 不要な行（販売実績額、リハーサル数字など）はスキップ
            if prize_type in ["販売実績額", "リハーサル数字", "裏リハーサル数字", "ナンバーズ風車盤", "ナンバーズ4数字絞り"]:
                continue
            prize_details.append({
                "タイプ": prize_type,
                "当選口数": cols[0].text.strip(),
                "当選金額": cols[1].text.strip()
            })
    
    # ストレート、ボックス、セットストレート、セットボックスのデータを表示
    print("ナンバーズ3 当選口数と当選金額:")
    for prize in prize_details:
        print(f"{prize['タイプ']} - 口数: {prize['当選口数']}, 当選金額: {prize['当選金額']}")

# 実行
get_numbers3()