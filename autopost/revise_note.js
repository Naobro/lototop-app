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


const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const fmt=s=>esc(s).replace(/(https?:\/\/[^\s<]+)/g,u=>`<a href="${u}">${u}</a>`).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
(async()=>{
const me=await api('GET','/v2/current_user');if(me.urlname!=='naobillion')throw Error('account mismatch');
const key='nc33e6567fa0f',n=await api('GET',`/v3/notes/${key}?draft=true&draft_reedit=false&ts=${Date.now()}`);
if(n.key!==key||n.status!=='published'||n.price!==500)throw Error('Unexpected article');
fs.mkdirSync(path.join(__dirname,'out'),{recursive:true});fs.writeFileSync(path.join(__dirname,'out/before.json'),JSON.stringify(n));
const a=JSON.parse(fs.readFileSync(path.join(__dirname,'revision-2026-10-05.json'))),html=a.paragraphs.map(p=>{p.id=crypto.randomUUID();const tag=p.heading?'h'+Math.min(p.level||2,3):'p';return `<${tag} name="${p.id}" id="${p.id}">${p.lines.map(fmt).join('<br>')}</${tag}>`;});
const separator=a.paragraphs[a.separatorIndex].id;
const payload={author_ids:[],body_length:a.paragraphs.reduce((v,p)=>v+p.lines.join('').length,0),disable_comment:n.disable_comment??false,exclude_from_creator_top:n.exclude_from_creator_top??false,exclude_ai_learning_reward:n.exclude_ai_learning_reward??false,free_body:html.slice(0,a.separatorIndex+1).join(''),pay_body:html.slice(a.separatorIndex+1).join(''),hashtags:[],image_keys:[],index:false,is_refund:false,limited:false,magazine_ids:[],magazine_keys:[],name:a.title,price:500,send_notifications_flag:false,separator,status:'published',circle_permissions:[{kind:'circle_plan',keys:[PLAN_KEY]}],lead_form:null,line_add_friend:null,pro_coupon_keys:[]};
if(Array.isArray(n.discount_campaigns)&&n.discount_campaigns.length)payload.discount_campaigns=n.discount_campaigns;
await api('PUT',`/v1/text_notes/${n.id}`,payload);
const after=await api('GET',`/v3/notes/${key}?draft=true&draft_reedit=false&ts=${Date.now()}`),body=after.body||'';
if(after.status!=='published'||after.price!==500||!JSON.stringify(after.circle_plans||[]).includes(PLAN_KEY)||!body.includes('パターン②も完全一致')||!body.includes('03-04-15-29-37-43')||body.includes('各位置の遷移率')||body.includes('前回1口目'))throw Error('Post-update verification failed');
fs.writeFileSync(path.join(__dirname,'out/after.json'),JSON.stringify(after));console.log(`更新確認OK: ${after.note_url} price=${after.price} image=${!!after.eyecatch} membership=true`);
})().catch(e=>{console.error(e.message);process.exit(1)});
