// 楽天宝くじの当せん番号ページから「今日の抽せん分」を取得し、data/ のCSVに追記する。
// 使い方: node autopost/update_results.js [YYYY-MM-DD]（省略時はJSTの今日）
// 今日の分がまだ掲載されていなければ exit code 2（ワークフロー側で待って再試行する）。
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');
const { jstToday, gamesToVerify } = require('./schedule');
const { targetDate } = require('./engine');

const DATA = path.join(__dirname, '..', 'data');
const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36';
const PAGES = { loto6: 'loto6', loto7: 'loto7', miniloto: 'mini', numbers3: 'numbers3', numbers4: 'numbers4' };

const num = (s) => {
  const t = (s || '').replace(/[,口円()\s]/g, '');
  return /^\d+$/.test(t) ? Number(t) : 0; // 「該当なし」は0
};

async function latestTable(game, wantedDate) {
  const res = await fetch(`https://takarakuji.rakuten.co.jp/backnumber/${PAGES[game]}/`, { headers: { 'User-Agent': UA } });
  if (!res.ok) throw new Error(`${game}: HTTP ${res.status}`);
  const doc = new JSDOM(await res.text()).window.document;
  const tables = [...doc.querySelectorAll('table.tblNumberGuid')];
  const table = tables.find(t => [...t.querySelectorAll('tr')].some(tr =>
    tr.querySelector('th')?.textContent.replace(/\s+/g,'') === '抽せん日' &&
    tr.querySelector('td')?.textContent.trim().replace(/\//g,'-') === wantedDate)) || tables[0];
  if (!table) throw new Error(`${game}: 結果テーブルが見つかりません`);
  const rows = {};
  for (const tr of table.querySelectorAll('tr')) {
    const th = tr.querySelector('th');
    if (!th) continue;
    const label = th.textContent.replace(/\s+/g, '').replace(/\(.*\)はボーナス数字/, '');
    rows[label] = [...tr.querySelectorAll('td, th[colspan]')].map((c) => c.textContent.trim()).filter((x) => x !== '');
  }
  const round = num(rows['回号'][0].replace('第', '').replace('回', ''));
  const date = rows['抽せん日'][0].replace(/\//g, '-');
  return { round, date, rows };
}

function toRow(game, t) {
  const r = t.rows;
  const requirePrizes = keys => {
    for(const k of keys) if(!r[k] || r[k].length<2) throw new Error(`${game}: ${k}の口数・当選金額が不足`);
  };
  const kuchi = (k) => num((r[k] || [])[0]);
  const kin = (k) => num((r[k] || [])[1]);
  if (game === 'numbers3' || game === 'numbers4') {
    const digits = r['当せん番号'][0].split('').map(Number);
    const kinds = ['ストレート', 'ボックス', 'セット（ストレート）', 'セット（ボックス）'];
    if (game === 'numbers3') kinds.push('ミニ');
    requirePrizes(kinds);
    if(digits.length!==(game==='numbers3'?3:4)||digits.some(n=>!Number.isInteger(n)||n<0||n>9)) throw new Error(`${game}: 当選番号の形式が不正`);
    return {
      main: [t.round, t.date, ...digits, ...kinds.map(kuchi), ...kinds.map(kin)],
      short: [t.round, ...digits],
    };
  }
  const nums = r['本数字'].filter((x) => !x.startsWith('(')).map(num);
  let bonus = (r['本数字'].filter((x) => x.startsWith('('))).concat(r['ボーナス数字'] || []).map(num);
  const tiers = { loto6: 5, loto7: 6, miniloto: 4 }[game];
  const ranks = Array.from({ length: tiers }, (_, i) => `${i + 1}等`);
  requirePrizes(ranks);
  if((game==='loto6'||game==='loto7')&&!r['キャリーオーバー']?.length) throw new Error(`${game}: キャリーオーバーが不足`);
  const row = [t.round, t.date, ...nums, ...bonus, ...ranks.map(kuchi), ...ranks.map(kin)];
  if (game === 'loto6') row.push(num((r['キャリーオーバー'] || [])[0]), ''); // 既存形式は末尾カンマあり
  if (game === 'loto7') row.push(num((r['キャリーオーバー'] || [])[0]));
  const expect = { loto6: [6, 1], loto7: [7, 2], miniloto: [5, 1] }[game];
  if (nums.length !== expect[0] || bonus.length !== expect[1]) throw new Error(`${game}: 数字の個数が想定外 ${nums} / ${bonus}`);
  return { main: row };
}

function append(file, row) {
  const p = path.join(DATA, file);
  const text = fs.readFileSync(p, 'utf8');
  if (text.split('\n').some((l) => l.split(',')[0] === String(row[0]))) return false;
  fs.writeFileSync(p, (text.endsWith('\n') ? text : text + '\n') + row.join(',') + '\n');
  return true;
}

(async () => {
  const today = process.argv[2] || targetDate();
  const games = gamesToVerify(today);
  let missing = [];
  for (const game of games) {
    const t = await latestTable(game, today);
    if (t.date !== today) { missing.push(`${game}(最新${t.date})`); continue; }
    const { main, short } = toRow(game, t);
    const file = { loto6: 'loto6_50.csv', loto7: 'loto7_50.csv', miniloto: 'miniloto_50.csv', numbers3: 'numbers3_24.csv', numbers4: 'numbers4_24.csv' }[game];
    const added = append(file, main);
    if (short) append(game === 'numbers3' ? 'n3.csv' : 'n4.csv', short);
    console.log(`${game} 第${t.round}回 ${added ? '追記' : '反映済み'}: ${main.join(',')}`);
  }
  if (missing.length) { console.log(`まだ掲載されていません: ${missing.join(', ')}`); process.exit(2); }
})().catch((e) => { console.error(e); process.exit(1); });
