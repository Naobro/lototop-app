"""
note公開用の予想画像を生成するモジュール。
元は numbers4_top.py にのみ実装されていたが、桁数を引数化して
ナンバーズ3・4どちらでも使えるようにした。
"""
from __future__ import annotations

import os
import platform
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont


def get_system_font() -> str | None:
    system = platform.system()
    font_candidates = {
        "Windows": [
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/arial.ttf",
        ],
        "Darwin": [
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Arial.ttf",
        ],
        "Linux": [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ],
    }
    for font_path in font_candidates.get(system, []):
        if os.path.exists(font_path):
            return font_path
    return None


def create_prediction_image(
    digit_count: int,
    combinations: list[tuple[int, ...]],
    current_round: int,
    current_date: datetime,
    previous_round: int | None = None,
    previous_winning: list[int] | None = None,
    backtest_summary_text: str | None = None,
    output_path: str = "output/naoki_prediction.png",
    combo_meta: list[dict] | None = None,
    rank_offset: int = 0,
    subtitle: str | None = None,
) -> str | None:
    """combo_meta: combinations と同じ順番で {"sab_pattern": "ASAA", "type": "ダブル"} のような
    辞書を渡すと、各行にSABパターンとタイプを添えて描画する（根拠の要約表示）。
    rank_offset: 2枚目の画像で「11位」からの通し番号にしたい場合などに使う。
    """
    game_label = f"ナンバーズ{digit_count}"
    width = 1080
    row_height = 90 if combo_meta else 80
    backtest_lines = backtest_summary_text.count("\n") + 1 if backtest_summary_text else 0
    height = (
        520  # ヘッダー〜「今回予想」見出しまで
        + (160 if (previous_round and previous_winning) else 0)
        + row_height * max(len(combinations), 1)
        + 34 * backtest_lines
        + 140  # 免責文とマージン
    )
    background = Image.new("RGB", (width, height), color="#ffffff")
    draw = ImageDraw.Draw(background)

    font_path = get_system_font()
    try:
        if font_path:
            title_font = ImageFont.truetype(font_path, 55)
            date_font = ImageFont.truetype(font_path, 32)
            section_font = ImageFont.truetype(font_path, 40)
            number_font = ImageFont.truetype(font_path, 46)
            winning_font = ImageFont.truetype(font_path, 42)
            footer_font = ImageFont.truetype(font_path, 26)
            meta_font = ImageFont.truetype(font_path, 22)
        else:
            title_font = date_font = section_font = number_font = winning_font = footer_font = meta_font = ImageFont.load_default()
    except Exception:
        title_font = date_font = section_font = number_font = winning_font = footer_font = meta_font = ImageFont.load_default()

    y = 40
    draw.rounded_rectangle([40, y, width - 40, y + 120], radius=10, fill="#1a5490")
    draw.text((width // 2, y + 35), f"NAOKIの{game_label} 予想", font=title_font, fill="white", anchor="mm")
    draw.text((width // 2, y + 85), datetime.now().strftime("%Y/%m/%d"), font=date_font, fill="white", anchor="mm")
    y += 160

    if previous_round and previous_winning:
        draw.rounded_rectangle([50, y, width - 50, y + 55], radius=8, fill="#e8f5e8", outline="#4caf50", width=2)
        draw.text((width // 2, y + 27), f"前回結果（第{previous_round}回）", font=section_font, fill="#2e7d32", anchor="mm")
        y += 80
        winning_text = "-".join(map(str, previous_winning))
        draw.text((width // 2, y), f"当選番号: {winning_text}", font=winning_font, fill="#d32f2f", anchor="mm")
        y += 70

    draw.line([(60, y), (width - 60, y)], fill="#1a5490", width=4)
    y += 40
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    weekday = weekdays[current_date.weekday()]
    heading = f"今回予想（第{current_round}回・{current_date.strftime('%m/%d')}({weekday})）"
    if subtitle:
        heading += f" ／ {subtitle}"
    draw.rounded_rectangle([50, y, width - 50, y + 55], radius=8, fill="#e3f2fd", outline="#2196f3", width=2)
    draw.text((width // 2, y + 27), heading, font=section_font, fill="#1565c0", anchor="mm")
    y += 90

    for i, combo in enumerate(combinations):
        rank = rank_offset + i + 1
        num_str = "".join(map(str, combo))
        total = sum(combo)
        box_bottom = y + row_height - 15
        draw.rounded_rectangle([80, y, width - 80, box_bottom], radius=8, outline="#cccccc", width=2)
        mid_y = (y + box_bottom) // 2
        draw.text((150, mid_y), f"{rank}位", font=section_font, fill="#333333", anchor="lm")
        draw.text((width // 2 + 20, mid_y), num_str, font=number_font, fill="#1a5490", anchor="mm")
        draw.text((width - 130, mid_y), f"合計{total}", font=footer_font, fill="#666666", anchor="mm")
        if combo_meta and i < len(combo_meta):
            meta = combo_meta[i]
            meta_text = f"SAB:{meta.get('sab_pattern', '-')}　{meta.get('type', '')}"
            draw.text((width // 2 + 20, mid_y + 30), meta_text, font=meta_font, fill="#888888", anchor="mm")
        y += row_height

    y += 20
    if backtest_summary_text:
        for line in backtest_summary_text.split("\n"):
            draw.text((width // 2, y), line, font=footer_font, fill="#555555", anchor="mm")
            y += 34

    draw.text((width // 2, y + 20), "※統計分析による数字です。当選を保証するものではありません", font=footer_font, fill="#999999", anchor="mm")

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        background.save(output_path, quality=95, optimize=True)
        return output_path
    except Exception:
        return None


def create_prediction_image_pair(
    digit_count: int,
    combinations: list[tuple[int, ...]],
    current_round: int,
    current_date: datetime,
    output_path_prefix: str,
    combo_meta: list[dict] | None = None,
    previous_round: int | None = None,
    previous_winning: list[int] | None = None,
    backtest_summary_text: str | None = None,
    split_size: int = 10,
) -> list[str]:
    """20件などの組み合わせを split_size 件ずつ2枚（以上）の画像に分けて生成する。
    1枚目には前回結果とバックテスト情報を、2枚目以降には付けない（画像を軽くするため）。
    戻り値は生成できた画像パスのリスト。
    """
    paths = []
    chunks = [combinations[i:i + split_size] for i in range(0, len(combinations), split_size)]
    meta_chunks = None
    if combo_meta:
        meta_chunks = [combo_meta[i:i + split_size] for i in range(0, len(combo_meta), split_size)]
    for idx, chunk in enumerate(chunks):
        lo = idx * split_size + 1
        hi = idx * split_size + len(chunk)
        path = create_prediction_image(
            digit_count=digit_count,
            combinations=chunk,
            current_round=current_round,
            current_date=current_date,
            previous_round=previous_round if idx == 0 else None,
            previous_winning=previous_winning if idx == 0 else None,
            backtest_summary_text=backtest_summary_text if idx == 0 else None,
            output_path=f"{output_path_prefix}_{lo}-{hi}.png",
            combo_meta=meta_chunks[idx] if meta_chunks else None,
            rank_offset=idx * split_size,
            subtitle=f"{lo}〜{hi}位",
        )
        if path:
            paths.append(path)
    return paths
