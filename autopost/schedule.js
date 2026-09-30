// 曜日ごとの「検証する種別（今日の抽せん）」と「予想する種別（次の抽せん日）」。
const DOW = ['日', '月', '火', '水', '木', '金', '土'];

function jstToday() {
  return new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
}

function dow(date) {
  return new Date(`${date}T00:00:00Z`).getUTCDay();
}

// 今日抽せんがあった種別
function gamesToVerify(date) {
  const loto = { 1: 'loto6', 2: 'miniloto', 4: 'loto6', 5: 'loto7' }[dow(date)];
  const d = dow(date);
  if (d === 0 || d === 6) return [];
  return [...(loto ? [loto] : []), 'numbers3', 'numbers4'];
}

// 次の抽せん日（金曜なら翌週月曜）
function nextDrawDate(date) {
  const d = new Date(`${date}T00:00:00Z`);
  do d.setUTCDate(d.getUTCDate() + 1); while ([0, 6].includes(d.getUTCDay()));
  return d.toISOString().slice(0, 10);
}

const NAMES = { loto6: 'ロト6', loto7: 'ロト7', miniloto: 'ミニロト', numbers3: 'ナンバーズ3', numbers4: 'ナンバーズ4' };

function title(date) {
  const next = nextDrawDate(date);
  const [, m, d] = next.split('-').map(Number);
  const games = gamesToVerify(next).map((g) => NAMES[g]).join('・');
  return `🎯【${m}月${d}日 抽せん分】${games} 予想公開`;
}

module.exports = { jstToday, gamesToVerify, nextDrawDate, title, DOW, dow };
