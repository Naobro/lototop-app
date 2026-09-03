"""
曜日ごとの「予想を出すゲーム」「前回分の検証を出すゲーム」を定義する週次スケジュール。
ユーザー指定の運用ルールをそのままコード化したもの：

月: 予想=[ロト6, ナンバーズ3, ナンバーズ4]   検証=[ロト7, ナンバーズ3, ナンバーズ4]（金曜分）
火: 予想=[ミニロト, ナンバーズ3, ナンバーズ4] 検証=[ロト6, ナンバーズ3, ナンバーズ4]（月曜分）
水: 予想=[ナンバーズ3, ナンバーズ4]           検証=[ミニロト, ナンバーズ3, ナンバーズ4]（火曜分）
木: 予想=[ロト6, ナンバーズ3, ナンバーズ4]    検証=[ナンバーズ3, ナンバーズ4]（水曜分、ロトなし）
金: 予想=[ロト7, ナンバーズ3, ナンバーズ4]    検証=[ロト6, ナンバーズ3, ナンバーズ4]（木曜分）
土日: 対象なし（抽せんが無いため）
"""
from __future__ import annotations

from datetime import date, timedelta

# weekday(): 月=0 火=1 水=2 木=3 金=4 土=5 日=6
WEEKLY_PLAN: dict[int, dict[str, list[str]]] = {
    0: {"predict": ["loto6", "numbers3", "numbers4"], "verify": ["loto7", "numbers3", "numbers4"]},
    1: {"predict": ["miniloto", "numbers3", "numbers4"], "verify": ["loto6", "numbers3", "numbers4"]},
    2: {"predict": ["numbers3", "numbers4"], "verify": ["miniloto", "numbers3", "numbers4"]},
    3: {"predict": ["loto6", "numbers3", "numbers4"], "verify": ["numbers3", "numbers4"]},
    4: {"predict": ["loto7", "numbers3", "numbers4"], "verify": ["loto6", "numbers3", "numbers4"]},
}

WEEKDAY_LABELS = ["月", "火", "水", "木", "金", "土", "日"]


def plan_for_date(d: date) -> dict[str, list[str]]:
    """指定日の「予想対象」「検証対象」ゲーム一覧を返す。土日は両方とも空リスト。"""
    plan = WEEKLY_PLAN.get(d.weekday())
    if plan is None:
        return {"predict": [], "verify": []}
    return {"predict": list(plan["predict"]), "verify": list(plan["verify"])}


def verify_source_date(d: date) -> date | None:
    """dの「検証」が指す“予想を出した元の曜日”の日付を返す（直近の該当曜日）。
    月検証=直前の金曜, 火検証=直前の月曜, 水検証=直前の火曜,
    木検証=直前の水曜, 金検証=直前の木曜。
    """
    offset_by_weekday = {0: 3, 1: 1, 2: 1, 3: 1, 4: 1}  # 月曜だけ金曜(3日前)、他は前日
    offset = offset_by_weekday.get(d.weekday())
    if offset is None:
        return None
    return d - timedelta(days=offset)


def describe(d: date) -> str:
    plan = plan_for_date(d)
    label = WEEKDAY_LABELS[d.weekday()]
    src = verify_source_date(d)
    src_txt = f"（{src.strftime('%m/%d')}{WEEKDAY_LABELS[src.weekday()]}分）" if src else ""
    return (
        f"{d.strftime('%Y-%m-%d')}（{label}）: "
        f"予想={plan['predict'] or 'なし'} / 検証={plan['verify'] or 'なし'}{src_txt}"
    )
