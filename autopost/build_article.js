// naobillionaire の「note記事まとめ作成」ページ(_auto/digest)を、サイトの本番JSのまま jsdom で実行し、
// note に貼る本文を作る。CSVはこのリポジトリの data/（直前に更新したもの）を読ませる。
// 出力: autopost/out/article.json { title, paragraphs:[{lines:[...]}], separatorIndex }
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');
const { jstToday, title } = require('./schedule');

const SITE = 'https://naobillionaire.synergy.cfbx.jp';
const PAGE = `${SITE}/_auto/digest/index.html`;
const DATA = path.join(__dirname, '..', 'data');
const OUT = path.join(__dirname, 'out');

async function loadPage() {
  const html = await (await fetch(PAGE)).text();
  const vc = new VirtualConsole();
  vc.on('jsdomError', (e) => console.error('page error:', e.message));
  const dom = new JSDOM(html.replace(/<script[^>]*googletagmanager[^>]*><\/script>/, ''), {
    url: PAGE, runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) {
      w.fetch = async (u, o) => {
        const url = new URL(u, PAGE).href;
        const m = url.match(/raw\.githubusercontent\.com\/Naobro\/lototop-app\/main\/data\/([\w.]+\.csv)/);
        if (m) {
          const body = fs.readFileSync(path.join(DATA, m[1]), 'utf8');
          return new Response(body, { status: 200 });
        }
        if (url.includes('/member/api/')) return new Response('[]', { status: 200 });
        return fetch(url, o);
      };
      w.navigator.clipboard = { writeText: async () => {} };
    },
  });
  const doc = dom.window.document;
  for (let i = 0; i < 60; i++) {
    await new Promise((r) => setTimeout(r, 500));
    const c = doc.getElementById('digest-content');
    if (c && !c.classList.contains('loading') || (c && c.querySelector('.digest-block'))) break;
  }
  return doc;
}

const clean = (s) => s.replace(/\s+/g, ' ').trim();

// ブラウザで innerText をコピーしたときと同じ並びの行にする
function linesOf(el) {
  const out = [];
  const walk = (n) => {
    for (const c of n.children) {
      if (['H4', 'P'].includes(c.tagName) || c.classList.contains('nums') || c.classList.contains('copy-list-row') || c.classList.contains('disclaimer-box')) {
        out.push(clean(c.textContent));
      } else walk(c);
    }
  };
  walk(el);
  return out.filter(Boolean);
}

function greeting(doc) {
  return [...doc.querySelectorAll('#digest-greeting p')].map((p) => {
    const lines = [];
    let cur = '';
    for (const n of p.childNodes) {
      if (n.nodeName === 'BR') { lines.push(clean(cur)); cur = ''; } else cur += n.textContent;
    }
    lines.push(clean(cur));
    return { lines: lines.filter(Boolean) };
  });
}

(async () => {
  const today = process.argv[2] || jstToday();
  const doc = await loadPage();
  const label = doc.getElementById('today-label').textContent;
  if (!label.includes(today)) throw new Error(`記事まとめページの基準日が今日(${today})ではありません: ${label}`);
  const blocks = [...doc.querySelectorAll('#digest-content .digest-block')];
  if (blocks.length === 0) throw new Error('検証・予想ブロックが0件です');

  const paragraphs = greeting(doc);
  let separatorIndex = -1;
  for (const b of blocks) {
    const h = clean(b.querySelector('h2').textContent);
    const body = b.querySelector('h2').nextElementSibling;
    const lead = body.querySelector(':scope > p.page-lead');
    if (!h.startsWith('✅') && separatorIndex < 0) separatorIndex = paragraphs.length - 1; // ここまで無料
    paragraphs.push({ lines: [h], heading: true });
    if (lead) paragraphs.push({ lines: [clean(lead.textContent)] });
    const rest = linesOf(body).filter((l) => !lead || l !== clean(lead.textContent));
    if (rest.length) paragraphs.push({ lines: rest });
  }
  if (separatorIndex < 0) throw new Error('予想セクションが見つかりません（有料ラインを決められない）');

  fs.mkdirSync(OUT, { recursive: true });
  const article = { date: today, title: title(today), label: clean(label), paragraphs, separatorIndex };
  fs.writeFileSync(path.join(OUT, 'article.json'), JSON.stringify(article, null, 2));
  fs.writeFileSync(path.join(OUT, 'article.txt'), paragraphs.map((p) => p.lines.join('\n')).join('\n\n'));
  console.log(article.title);
  console.log(article.label);
  console.log(`段落 ${paragraphs.length} / 無料は ${separatorIndex + 1} 段落目まで`);
})().catch((e) => { console.error(e); process.exit(1); });
