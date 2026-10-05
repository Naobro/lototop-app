const fs=require('fs'),path=require('path');
const E=require('./engine'),S=require('./schedule');
const DIR=path.join(__dirname,'state'),OUT=path.join(__dirname,'out');
const NAMES={loto6:'ロト6',loto7:'ロト7',miniloto:'ミニロト',numbers3:'ナンバーズ3',numbers4:'ナンバーズ4'};
const money=n=>n.toLocaleString('ja-JP')+'円',pct=n=>n.toFixed(1)+'%',pad=n=>String(n).padStart(2,'0');
const read=(f,v)=>fs.existsSync(path.join(DIR,f))?JSON.parse(fs.readFileSync(path.join(DIR,f),'utf8')):v;
const write=(f,d)=>{fs.mkdirSync(DIR,{recursive:true});fs.writeFileSync(path.join(DIR,f),JSON.stringify(d,null,2)+'\n');};
const circ=i=>'①②③④⑤⑥⑦⑧⑨⑩'[i];
const date=process.argv[2]||E.targetDate();
if(!/^\d{4}-\d{2}-\d{2}$/.test(date))throw Error('日付はYYYY-MM-DDで指定してください');
const target=S.nextDrawDate(date),forecasts=read('forecasts.json',{}),ledger=read('ledger.json',{}),paragraphs=[];
const add=(lines,heading=false)=>paragraphs.push({lines:Array.isArray(lines)?lines:[lines],heading});
add('こんにちは、宝くじでFIREを目指しているNAOKIです。');
add('2021年から毎日宝くじを買い続けてます。');
add(['実績','ロト7の3等 約80万円当選','ナンバーズ4 ストレート 3回当選 証拠の動画','https://vt.tiktok.com/ZSQo7AyDT/']);
add('高額当選を本気で狙いたい方、ぜひ参考にしてください。');
add(['運営 予想サイト','https://naobillionaire.synergy.cfbx.jp/']);
add(['📣 最新AI予想の通知を受け取りたい方へ！','👉 LINE公式アカウント登録はこちら','https://line.me/R/ti/p/@192kvzul?oat_content=url&ts=02251322']);
let purchase=0,returned=0,complete=true;
for(const game of S.gamesToVerify(date)){
 const draws=E.loadDraws(game,date),draw=draws.at(-1);
 if(!draw||draw.date!==date)throw Error(`${game}: ${date}の結果が不足`);
 add(`✅ ${NAMES[game]} 検証（${date}）`,true);
 add(`当選番号：${draw.numbers.map(n=>E.CONFIG[game]?pad(n):n).join(E.CONFIG[game]?'・':'')}${draw.bonus.length?' （'+draw.bonus.map(pad).join('・')+'）':''}`);
 const saved=forecasts[date]?.games[game];
 if(!saved||!forecasts[date].published){add('公開済み10口の記録がないため、購入成績は未集計です。');complete=false;continue;}
 const tickets=saved.tickets.map(x=>Array.isArray(x)?x:x.numbers),result=E.settlement(game,tickets,draw);
 const hits=result.details.flatMap((x,i)=>x.rank?[`🎉 ${circ(i)} ${NAMES[game]}・${x.rank}当選！${money(x.pay)}`]:[]);
 if(hits.length){const winning=paragraphs.pop();hits.forEach(x=>add(x,true));paragraphs.push(winning);}else add('的中なし');
 if(E.CONFIG[game]){
  const actual=draw.numbers.slice().sort((a,b)=>a-b).map(E.band),patterns=(saved.patterns||[]).map(p=>p.pattern||p),matched=patterns.findIndex(p=>p.join('-')===actual.join('-'));
  if(matched>=0)add(`🎯 パターン${circ(matched)}も完全一致！`,true);
  if(saved.selection)add([`厳選数字：${saved.selection.selected.map(n=>draw.numbers.includes(n)?`**${n}**`:draw.bonus.includes(n)?`${n}（B）`:n).join(', ')}`,`削除数字：${saved.selection.cut.join(', ')}`]);
  add(E.candidateReview(game,saved,draw).filter(x=>!x.startsWith('実際のパターン：')));
  if(patterns.length){add('パターン検証',true);add(`パターン結果：${actual.join('-')}`);if(matched>=0)add(`**${circ(matched)}のパターンが完全一致！**`);add(patterns.map((p,i)=>`${circ(i)} ${p.join('-')}`));}
 }else{
  if(saved.top)add(saved.top.map((p,j)=>`第${j+1}数字TOP5：${p.top.map(x=>x.digit===draw.numbers[j]?`**${x.digit}**`:x.digit).join(', ')}`));
  add(E.candidateReview(game,saved,draw).filter(x=>x!==saved.analysisSource).map(x=>x.replaceAll('前回TOP5','TOP5')));
 }
 add(game==='numbers3'?'厳選ミニ予想検証':game==='numbers4'?'厳選セット予想検証':'厳選予想検証',true);
 add(tickets.map((p,i)=>`${circ(i)} ${p.map((n,j)=>{const hit=E.CONFIG[game]?draw.numbers.includes(n):n===draw.numbers[game==='numbers3'?j+1:j];const label=E.CONFIG[game]?pad(n):n;return hit?`**${label}**`:label;}).join(E.CONFIG[game]?'-':'').replaceAll('****','')}${E.CONFIG[game]&&p.some(n=>draw.bonus.includes(n))?' （ボーナス一致：'+p.filter(n=>draw.bonus.includes(n)).map(pad).join(', ')+'）':''}`));
 if(game==='numbers4'){
  const near=result.details.flatMap((x,i)=>x.near?.straight||x.near?.box?[`${circ(i)}：${x.near.straight?'ストレート1桁違い':''}${x.near.straight&&x.near.box?'／':''}${x.near.box?'BOX1個違い':''}`]:[]);
  add(near.length?near:['ニア（1個はずし）：なし']);
 }
 add([`購入：${tickets.length}口 ${money(result.purchase)}${game==='numbers3'?'（ミニ）':game==='numbers4'?'（セット）':''}`,`当選金額：${money(result.return)}`,`回収率：${pct(result.rate)}`]);
 if(game==='loto6'||game==='loto7')add(`キャリーオーバー：${money(draw.carry)}`);
 ledger[`${date}:${game}`]={date,game,round:draw.round,source:forecasts[date].source||'note公開記録',...result};purchase+=result.purchase;returned+=result.return;
}
add(`💰 ${date} 当日収支`,true);
add(purchase?[`購入金額：${money(purchase)}`,`当選金額：${money(returned)}`,`回収率：${pct(returned/purchase*100)}`,`収支：${money(returned-purchase)}`,complete?'':'※未記録の種別は含めていません。'].filter(Boolean):['未集計（公開済み予想の記録が不足）']);
const month=date.slice(0,7),entries=Object.values(ledger).filter(x=>x.date.startsWith(month)&&x.date<=date);
const mp=entries.reduce((s,x)=>s+x.purchase,0),mr=entries.reduce((s,x)=>s+x.return,0);
add(`📊 ${month} 月間収支（記録済み分）`,true);
add(mp?[`購入金額：${money(mp)}`,`当選金額：${money(mr)}`,`回収率：${pct(mr/mp*100)}`,`収支：${money(mr-mp)}`,'収支記録開始：2026-10-02。記録前・未記録分は未集計です。']:['未集計']);
const separatorIndex=paragraphs.length-1;add('ここからメンバーシップ限定',true);
const existing=forecasts[target];
if(existing?.published)throw Error(`${target}抽選分は公開記録済みです。予想は上書きしません。`);
const generated=existing||{date:target,basisDate:date,version:'24-transition-sa-position-v2',published:false,games:{}};
if(generated.basisDate!==date)throw Error('保存済み予想の基準日が異なります');
for(const game of S.gamesToVerify(target)){
 const draws=E.loadDraws(game,date);
 const pred=generated.games[game]||(E.CONFIG[game]?E.lotoForecast(game,draws):E.numbersForecast(game,draws));generated.games[game]=pred;
 if(E.CONFIG[game]){
  add(`🎖 ${NAMES[game]} 厳選数字・削除数字`,true);
  add([`厳選数字：${pred.selection.selected.length}個`,...[1,10,20,30].map(b=>`${b}の位：${pred.selection.selected.filter(n=>E.band(n)===b).join(', ')}`),`削除数字：${pred.selection.cut.join(', ')}`]);
  add(`🔮 ${NAMES[game]} パターン予想`,true);add(pred.patterns.map((p,i)=>`${circ(i)} ${p.pattern.join('-')}`));
  add(`🎯 ${NAMES[game]} 厳選予想10口`,true);
  pred.tickets.forEach((p,i)=>add([`${circ(i)} ${p.numbers.map(pad).join('-')}`,`${p.pattern.join('-')} ｜ ${p.sab} ｜ ZONE ${p.zones.join('-')} ｜ 引っ張り ${p.pull.map(pad).join(',')||'なし'} ｜ 連続 ${p.consecutive.map(x=>x.map(pad).join('-')).join(',')||'なし'} ｜ 末尾 ${p.tails.map(x=>x.map(pad).join('-')).join(',')||'なし'} ｜ 10回以上 ${p.cold.map(n=>`${pad(n)}(${p.gaps[n]}回未出現)`).join(',')||'なし'} ｜ 合計 ${p.sum}`]));
 }else{
  add(`🔮 ${NAMES[game]} 予想数字（各桁TOP5）`,true);add(pred.top.map((p,i)=>`第${i+1}数字：${p.top.map(x=>x.digit).join(', ')}`));
  add(game==='numbers3'?'🎯 厳選ミニ予想10口':'🎯 厳選セット予想10口',true);add(pred.tickets.map((p,i)=>`${circ(i)} ${p.join('')}`));
  add(`購入方式：${game==='numbers3'?'ミニ':'セット'}／10口・2,000円`);
 }
}
add('高額当選、狙いましょう！');forecasts[target]=generated;write('forecasts.json',forecasts);write('ledger.json',ledger);
fs.mkdirSync(OUT,{recursive:true});const article={date,predictionDate:target,title:S.title(date),paragraphs,separatorIndex};
fs.writeFileSync(path.join(OUT,'article.json'),JSON.stringify(article,null,2));
fs.writeFileSync(path.join(OUT,'article.txt'),article.title+'\n\n'+paragraphs.map(p=>p.lines.join('\n')).join('\n\n'));
console.log(article.title);console.log(`検証${date}→予想${target}／${paragraphs.length}段落／購入${purchase}・回収${returned}`);
