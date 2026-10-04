// build_article.js の出力を note に投稿する（noteの編集画面が内部で使っているAPIを直接呼ぶ）。
// 認証: 環境変数 NOTE_COOKIE（ブラウザの note.com の Cookie ヘッダ文字列）
// 使い方: node autopost/post_note.js draft   … 下書き作成→画像→保存→確認→下書き削除（動作テスト用）
//         node autopost/post_note.js publish … 本番公開（有料500円・SNSで0円・メンバー見放題・Xポスト）
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const API = 'https://note.com/api';
const PLAN_KEY = 'b62c08521a39'; // メンバーシップ「予想 見放題」
const PRICE = 500;
const EYECATCH = path.join(__dirname, 'eyecatch.jpg'); // 元: naobillionaire.synergy.cfbx.jp/_auto/digest/imeges/note.webp
const STATE = path.join(__dirname, 'state', 'posted.json');
const mode = process.argv[2] || 'draft';
if (!['draft','publish'].includes(mode)) throw new Error('mode は draft または publish');

const raw = (process.env.NOTE_COOKIE || '').trim();
// 値だけ登録された場合（"名前=" なし）はセッションCookieとして扱う
const cookie = raw && !raw.includes('=') ? `_note_session_v5=${raw}` : raw;
if (!cookie) { console.error('NOTE_COOKIE が設定されていません'); process.exit(1); }
const xsrf = decodeURIComponent((cookie.match(/XSRF-TOKEN=([^;]+)/) || [])[1] || '');

async function api(method, p, body, extra = {}) {
  const headers = {
    Cookie: cookie, 'X-Requested-With': 'XMLHttpRequest', Origin: 'https://editor.note.com', Referer: 'https://editor.note.com/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36',
    ...(xsrf ? { 'X-XSRF-TOKEN': xsrf } : {}),
  };
  let payload;
  if (body instanceof FormData) payload = body;
  else if (body !== undefined) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body); }
  const res = await fetch(API + p, { method, headers, body: payload, ...extra });
  const text = await res.text();
  let json; try { json = JSON.parse(text); } catch { json = null; }
  if (!res.ok || (json && json.error)) {
    throw new Error(`${method} ${p} → HTTP ${res.status}: ${text.slice(0, 300)}`);
  }
  return json ? json.data : text;
}

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const linkify = (s) => esc(s).replace(/(https?:\/\/[^\s<]+)/g, (u) => `<a href="${u}" target="_blank" rel="nofollow noopener">${u}</a>`);

function toHtml(paragraphs) {
  return paragraphs.map((p) => {
    const id = crypto.randomUUID();
    p.id = id;
    const inner = p.lines.map(linkify).join('<br>');
    return `<p name="${id}" id="${id}">${p.heading ? `<strong>${inner}</strong>` : inner}</p>`;
  });
}

(async () => {
  const a = JSON.parse(fs.readFileSync(path.join(__dirname, 'out', 'article.json'), 'utf8'));
  const state = fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE, 'utf8')) : {};
  if (mode === 'publish' && state[a.date]) { console.log(`${a.date} は投稿済み: ${state[a.date].url}`); return; }
  if(mode === 'publish') {
    const res=await fetch('https://note.com/api/v2/creators/naobillion/contents?kind=note&page=1');
    if(!res.ok) throw new Error('公開済み記事の確認に失敗');
    const list=await res.json();
    if(!Array.isArray(list.data?.contents)) throw new Error('公開済み記事一覧の形式が不明');
    if(list.data.contents.some(n=>n.name===a.title&&n.status==='published')) { console.log('同じタイトルの記事が公開済みです'); return; }
  }

  const me = await api('GET', '/v2/current_user');
  console.log(`ログイン確認: ${me.urlname}`);
  if (me.urlname !== 'naobillion') throw new Error(`想定外のアカウントです: ${me.urlname}`);

  const htmls = toHtml(a.paragraphs);
  const body = htmls.join('');
  const bodyLength = a.paragraphs.reduce((n, p) => n + p.lines.join('').length, 0);
  const sepId = a.paragraphs[a.separatorIndex].id;
  const freeBody = htmls.slice(0, a.separatorIndex + 1).join('');
  const payBody = htmls.slice(a.separatorIndex + 1).join('');

  const created = await api('POST', '/v1/text_notes', { template_key: null });
  const { id, key } = created;
  console.log(`下書き作成: id=${id} key=${key}`);
  if(mode==='publish') {
    const forecastPath=path.join(__dirname,'state/forecasts.json');
    const forecasts=JSON.parse(fs.readFileSync(forecastPath,'utf8'));
    if(!forecasts[a.predictionDate]) throw new Error('保存済み予想がありません');
    forecasts[a.predictionDate].noteKey=key;
    fs.writeFileSync(forecastPath,JSON.stringify(forecasts,null,2));
  }

  try {
    await api('POST', `/v1/text_notes/draft_save?id=${id}&is_temp_saved=true`, {
      body, body_length: bodyLength, name: a.title, separator: sepId, index: false, is_lead_form: false,
    });
    console.log('本文を保存');

    try {
      // noteはwebp不可のため、同じ画像をJPEGにしたものを使う（元画像を差し替えたら eyecatch.jpg も更新する）
      const img = fs.readFileSync(EYECATCH);
      const fd = new FormData();
      fd.append('note_id', String(id));
      fd.append('file', new Blob([img], { type: 'image/jpeg' }), 'eyecatch.jpg');
      fd.append('width', '1920');
      fd.append('height', '1005');
      await api('POST', '/v1/image_upload/note_eyecatch', fd);
      console.log('見出し画像を設定');
    } catch (e) { console.warn(`見出し画像の設定に失敗（本文は続行）: ${e.message}`); }

    if (mode !== 'publish') {
      const d = await api('GET', `/v3/notes/${key}?draft=true&draft_reedit=false&ts=${Date.now()}`);
      console.log(`下書き確認: ${d.name} / 本文${(d.body || '').length}文字 / 画像${d.eyecatch ? 'あり' : 'なし'}`);
      return;
    }

    const tweet = `noteで記事を書きました！この投稿をリポストするとお得に記事を読むことができます。\n${a.title} | NAO億万長者への道 @naobillionaire #note https://note.com/naobillion/n/${key}`;
    await api('PUT', `/v1/text_notes/${id}`, {
      author_ids: [], body_length: bodyLength, disable_comment: false, exclude_from_creator_top: false, exclude_ai_learning_reward: false,
      free_body: freeBody, hashtags: [], image_keys: [], index: false, is_refund: false, limited: false,
      magazine_ids: [], magazine_keys: [], name: a.title, pay_body: payBody, price: PRICE, send_notifications_flag: true,
      separator: sepId, status: 'published',
      circle_permissions: [{ kind: 'circle_plan', keys: [PLAN_KEY] }],
      discount_campaigns: [{ kind: 'twitter_retweet', twitter_status_body: tweet, discounted_price: 0 }],
      lead_form: null, line_add_friend: null, pro_coupon_keys: [],
    });
    console.log('公開しました');
    // Persist immediately: an X/verification failure must not create a second article.
    fs.mkdirSync(path.dirname(STATE), { recursive: true });
    state[a.date] = {key,url:`https://note.com/naobillion/n/${key}`,title:a.title};
    fs.writeFileSync(STATE, JSON.stringify(state, null, 2));
    const forecastPath=path.join(__dirname,'state/forecasts.json');
    const forecasts=JSON.parse(fs.readFileSync(forecastPath,'utf8'));
    if(forecasts[a.predictionDate]) {
      forecasts[a.predictionDate].published=true;
      forecasts[a.predictionDate].source=state[a.date].url;
      fs.writeFileSync(forecastPath,JSON.stringify(forecasts,null,2));
    }

    try {
      await api('POST', '/v3/discount_campaigns/twitter/post_status', { note_key: key });
      console.log('Xに告知ポスト');
    } catch (e) { console.warn(`Xポストに失敗: ${e.message}`); }

    const n = await api('GET', `/v3/notes/${key}`);
    const ok = n.status === 'published' && n.price === PRICE && JSON.stringify(n.circle_plans || []).includes(PLAN_KEY);
    console.log(`確認: status=${n.status} price=${n.price} plan=${ok} url=${n.note_url}`);
    if (!ok) throw new Error('公開後の設定確認に失敗しました');
    fs.mkdirSync(path.dirname(STATE), { recursive: true });
    state[a.date] = { key, url: n.note_url, title: a.title };
    fs.writeFileSync(STATE, JSON.stringify(state, null, 2));
  } finally {
    if (mode !== 'publish') {
      await api('DELETE', `/v1/text_notes/draft_delete?id=${id}`).catch((e) => console.warn(`下書き削除に失敗: ${e.message}`));
      console.log('テスト用の下書きを削除');
    }
  }
})().catch((e) => { console.error(e.message || e); process.exit(1); });
