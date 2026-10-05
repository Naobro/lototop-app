const fs = require('fs');
const path = require('path');
const vm = require('vm');
const band = n => n < 10 ? 1 : n < 20 ? 10 : n < 30 ? 20 : 30;
const counts = a => a.reduce((m,n)=>(m[n]=(m[n]||0)+1,m),{});
const sorted = a => a.slice().sort((a,b)=>a-b);
const box = a => sorted(a).join('-');
const FILES={loto6:'loto6_50.csv',loto7:'loto7_50.csv',miniloto:'miniloto_50.csv',numbers3:'numbers3_24.csv',numbers4:'numbers4_24.csv'};
const CONFIG={loto6:{mainCount:6,maxNumber:43,selectedCount:30},loto7:{mainCount:7,maxNumber:37,selectedCount:27},miniloto:{mainCount:5,maxNumber:31,selectedCount:20}};
function loadDraws(game,date){
  const rows=fs.readFileSync(path.join(__dirname,'../data',FILES[game]),'utf8').trim().split(/\r?\n/).map(s=>s.split(','));
  const headers=rows.shift();
  const n=CONFIG[game]?.mainCount || (game==='numbers3'?3:4);
  const tiers={loto6:5,loto7:6,miniloto:4,numbers3:5,numbers4:4}[game];
  const b=game==='loto7'?2:CONFIG[game]?1:0;
  return rows.filter(r=>/^\d+$/.test(r[0])&&r[1]<=date).map(r=>({
    round:Number(r[0]),date:r[1],numbers:r.slice(2,2+n).map(Number),bonus:r.slice(2+n,2+n+b).map(Number),
    amounts:r.slice(2+n+b+tiers,2+n+b+2*tiers).map(Number),
    carry:Number(r[2+n+b+2*tiers]||0),
  })).sort((a,b)=>a.round-b.round);
}
function transitions(draws,n){
  const recent=draws.slice(-24);
  if(recent.length<24)throw Error('遷移分析には24回のデータが必要です');
  return Array.from({length:n},(_,position)=>{
    const current=band(sorted(recent.at(-1).numbers)[position]);
    const hits={};let total=0;
    for(let i=0;i<23;i++)if(band(sorted(recent[i].numbers)[position])===current){
      const next=band(sorted(recent[i+1].numbers)[position]);hits[next]=(hits[next]||0)+1;total++;
    }
    // A missing conditional sample has no measured rate; never replace it with frequency.
    return {position:position+1,current,total,rates:Object.fromEntries([1,10,20,30].map(b=>[b,total?(hits[b]||0)/total:0]))};
  });
}
function facts(pick,draws){
  const a=sorted(pick),previous=draws.at(-1).numbers;
  const gaps=Object.fromEntries(a.map(n=>{const g=draws.slice().reverse().findIndex(d=>d.numbers.includes(n));return [n,g<0?draws.length:g];}));
  const tail=Object.values(counts(a.map(n=>n%10)));
  return {pull:a.filter(n=>previous.includes(n)),consecutive:a.slice(1).flatMap((n,i)=>n===a[i]+1?[[a[i],n]]:[]),
    triple:a.some(n=>a.includes(n+1)&&a.includes(n+2)),tails:Object.entries(counts(a.map(n=>n%10))).filter(([,c])=>c>=2).map(([t])=>a.filter(n=>n%10===+t)),
    cold:a.filter(n=>gaps[n]>=10),gaps,pattern:a.map(band),sum:a.reduce((s,n)=>s+n,0),
    zones:[a.filter(n=>n<=13).length,a.filter(n=>n>=14&&n<=28).length,a.filter(n=>n>=29).length],tailCounts:tail};
}
function validLoto(pick,draws){
  const f=facts(pick,draws);
  return new Set(pick).size===pick.length&&f.pull.length<=2&&!f.triple&&f.cold.length<=2&&
    f.tails.length<=1&&f.tailCounts.every(c=>c<=2)&&Object.values(counts(f.pattern)).every(c=>c<=3);
}
function combinations(a,k,visit,start=0,p=[]){if(p.length===k){visit(p.slice());return;}for(let i=start;i<=a.length-k+p.length;i++){p.push(a[i]);combinations(a,k,visit,i+1,p);p.pop();}}
function patterns(t){
  const out=[];
  function walk(p=[],score=1){if(p.length===t.length){out.push({pattern:p,score});return;}
    for(const b of [1,10,20,30]){const rate=t[p.length].rates[b];if(!rate||b<(p.at(-1)||0)||p.filter(n=>n===b).length>=3)continue;walk([...p,b],score*rate);}}
  walk();return out.sort((a,b)=>b.score-a.score||a.pattern.join('-').localeCompare(b.pattern.join('-')));
}
function libraries(){const c=vm.createContext({});for(const [f,name] of [['stats.js','LotoStats'],['numbers-stats.js','NumbersStats']])vm.runInContext(fs.readFileSync(path.join(__dirname,'lib',f),'utf8')+`\nthis.${name}=${name};`,c);return c;}
function lotoForecast(game,draws){
  const {LotoStats:L}=libraries();const cfg={...CONFIG[game],mainKey:'本数字',positionBoundaries:[1,10,20,30],tierRules:L.DEFAULT_TIER_RULES};
  const converted=draws.map(d=>({'回号':d.round,'本数字':sorted(d.numbers)}));
  const selection=L.calcSelectedNumbers(converted,cfg,24);
  const freq=counts(draws.slice(-24).flatMap(d=>d.numbers));
  const sab=n=>(freq[n]||0)>=5?'S':(freq[n]||0)>=3?'A':'B';
  const ts=transitions(draws,cfg.mainCount), ps=patterns(ts),wanted=new Map(ps.map(p=>[p.pattern.join('-'),[]]));
  combinations([...selection.selected],cfg.mainCount,a=>{
    const key=a.map(band).join('-');const list=wanted.get(key);if(!list||!validLoto(a,draws))return;
    const labels=a.map(sab),f=facts(a,draws);
    if(labels.filter(x=>x==='S').length>=5||labels.filter(x=>x==='A').length>=5||labels.filter(x=>x==='B').length>1)return;
    if(game==='loto6'&&!['3-2-1','1-3-2','2-1-3'].includes(f.zones.join('-')))return;
    const center=cfg.mainCount*(cfg.maxNumber+1)/2;
    const score=a.reduce((s,n)=>s+(freq[n]||0),0)-Math.abs(f.sum-center)/cfg.maxNumber;
    list.push({numbers:a,score});if(list.length>80){list.sort((a,b)=>b.score-a.score);list.length=40;}
  });
  const selectedPatterns=ps.filter(p=>wanted.get(p.pattern.join('-')).length>=2).slice(0,5);
  if(selectedPatterns.length<5)throw Error(`${game}: 条件を満たす5パターンが不足（ルールは緩めません）`);
  const tickets=[],usage={};
  for(const p of selectedPatterns){const list=wanted.get(p.pattern.join('-'));for(let i=0;i<2;i++){
    list.sort((a,b)=>(b.score-b.numbers.reduce((s,n)=>s+(usage[n]||0)*2,0))-(a.score-a.numbers.reduce((s,n)=>s+(usage[n]||0)*2,0))||a.numbers.join('-').localeCompare(b.numbers.join('-')));
    const chosen=list.shift().numbers;chosen.forEach(n=>usage[n]=(usage[n]||0)+1);
    tickets.push({numbers:chosen,sab:chosen.map(sab).join(''),...facts(chosen,draws)});
  }}
  const positional=L.calcDigitPositionTop5(converted,cfg,24,cfg.maxNumber);
  const top5=L.calcDigitPositionTop5(converted,cfg,24,5);
  const diagnostics=Array.from({length:cfg.maxNumber},(_,i)=>i+1).map(number=>{
    const positions=positional.flatMap((p,j)=>{const item=p.top.find(x=>x.number===number);return item?[{position:j+1,count:item.count,rank:1+p.top.filter(x=>x.count>item.count).length}]:[];});
    const gap=facts([number],draws).gaps[number];
    const positionScore=top5.reduce((s,p)=>{const i=p.top.findIndex(x=>x.number===number);return s+(i<0?0:5-i);},0);
    return {number,tier:sab(number),count:freq[number]||0,gap,positions,positionScore,selected:selection.selected.includes(number),previous:draws.at(-1).numbers.includes(number)};
  });
  return {selection,transitions:ts,patterns:selectedPatterns,tickets,diagnostics,selectionVersion:'sa-position-v2'};
}
function product(arrays,visit,p=[]){if(p.length===arrays.length){visit(p);return;}for(const n of arrays[p.length])product(arrays,visit,[...p,n]);}
function numbersPicks(game,top,draws){
  const mini=game==='numbers3', positions=(mini?top.slice(1):top).map(p=>Array.isArray(p)?p:p.top);
  const historical=new Set(draws.slice(-24).map(d=>box(d.numbers)));
  const candidates=[];
  product(positions,p=>{
    const digits=p.map(x=>x.digit),cs=Object.values(counts(digits));
    if(!mini&&(Math.max(...cs)>2||cs.filter(n=>n===2).length>1||historical.has(box(digits))))return;
    candidates.push({numbers:digits,score:p.reduce((s,x)=>s+x.score,0),frequency:p.reduce((s,x)=>s+x.count,0)});
  });
  candidates.sort((a,b)=>b.score-a.score||b.frequency-a.frequency||a.numbers.join('').localeCompare(b.numbers.join('')));
  const seen=new Set(),out=[],usage={};
  while(out.length<10){const eligible=candidates.filter(x=>!seen.has(mini?x.numbers.join(''):box(x.numbers)));
    eligible.sort((a,b)=>(b.score-b.numbers.reduce((s,n,j)=>s+(usage[j+':'+n]||0)*0.5,0))-(a.score-a.numbers.reduce((s,n,j)=>s+(usage[j+':'+n]||0)*0.5,0))||b.frequency-a.frequency||a.numbers.join('').localeCompare(b.numbers.join('')));
    if(!eligible.length)throw Error(`${game}: 条件を満たす10口が不足`);
    const a=eligible[0].numbers;seen.add(mini?a.join(''):box(a));a.forEach((n,j)=>usage[j+':'+n]=(usage[j+':'+n]||0)+1);out.push(a);
  }return out;
}
function numbersForecast(game,draws){const {LotoStats:L,NumbersStats:N}=libraries();const n=game==='numbers3'?3:4;
  const input=draws.map(d=>({'本数字':d.numbers})),cfg={mainKey:'本数字',digitCount:n,tierRules:L.DEFAULT_TIER_RULES};
  const ranking=N.calcDigitPrediction(input,cfg,24,10);
  const top=ranking.map(p=>({position:p.position,top:p.top.slice(0,5)}));
  const gaps=Array.from({length:n},(_,j)=>Object.fromEntries(Array.from({length:10},(_,digit)=>{const g=draws.slice().reverse().findIndex(d=>d.numbers[j]===digit);return [digit,g<0?draws.length:g];})));
  return {top,ranking,gaps,tickets:numbersPicks(game,top,draws)};
}
function candidateReview(game,saved,draw){
  if(CONFIG[game]){
    if(!saved.selection)return ['前回の厳選数字の記録が不足しています。削除理由は断定できません。'];
    const selected=saved.selection.selected,inside=draw.numbers.filter(n=>selected.includes(n)),outside=draw.numbers.filter(n=>!selected.includes(n));
    const out=[`厳選数字${selected.length}個：本数字${draw.numbers.length}個中${inside.length}個が候補内。候補外：${outside.join(', ')||'なし'}`,
      `ボーナス数字：${(draw.bonus||[]).filter(n=>selected.includes(n)).join(', ')||'候補内なし'}（候補外：${(draw.bonus||[]).filter(n=>!selected.includes(n)).join(', ')||'なし'}）`];
    for(const n of outside){
      if(saved.legacyReasons?.[n]){out.push(`${n}の削除理由：${saved.legacyReasons[n]}`);continue;}
      const d=saved.diagnostics?.find(x=>x.number===n);
      if(!d){out.push(`${n}：当時の評価記録が不足しているため、削除理由は断定できません。`);continue;}
      const positions=d.positions.map(x=>`第${x.position}数字${x.rank}位・${x.count}回`).join('／')||'各位置で未出現';
      const peers=saved.diagnostics.filter(x=>x.selected&&x.tier===d.tier).sort((a,b)=>a.positionScore-b.positionScore||a.count-b.count);
      const peer=peers[0];
      out.push(`${n}：${d.tier}分類・24回中${d.count}回、${positions}。位置評価${d.positionScore}点、${d.gap}回未出現。引っ張り${d.previous?'あり':'なし'}。`);
      out.push(`${n}は${selected.length}個の候補枠に入らず。選定方式はS/Aと位置別TOP5が主軸で、間隔・出現時期の偏りは減点していません。${peer?`採用された同分類の${peer.number}は位置評価${peer.positionScore}点・${peer.count}回。`:''}`);
    }
    if(outside.length)out.push('次回への確認点：候補外数字と採用境界の順位を比較し、位置別上位を落としていないか確認します。今回出た数字という理由だけで追加はしません。');
    const actual=sorted(draw.numbers).map(band),pats=(saved.patterns||[]).map(p=>p.pattern||p);
    const match=pats.findIndex(p=>p.join('-')===actual.join('-'));
    out.push(`実際のパターン：${actual.join('-')}。${pats.length?match>=0?`前回予想${match+1}番と完全一致。`:'前回5案に一致なし。':'前回パターン記録が不足。'}`);
    return out;
  }
  if(!saved.top)return ['前回TOP5の記録が不足しているため、候補外の理由は断定できません。'];
  const out=[];if(saved.analysisSource)out.push(saved.analysisSource);
  draw.numbers.forEach((digit,j)=>{
    const included=saved.top[j].top.some(x=>x.digit===digit),r=saved.ranking?.[j]?.top;
    if(included){out.push(`第${j+1}数字 ${digit}：前回TOP5候補内。`);return;}
    if(!r){out.push(`第${j+1}数字 ${digit}：候補外。当時の全数字評価記録が不足しているため、順位・削除理由は未確認。`);return;}
    const index=r.findIndex(x=>x.digit===digit),x=r[index],cut=r[4];
    out.push(`第${j+1}数字 ${digit}：候補外。24回中${x.count}回、${index+1}位・${x.score.toFixed(3)}点。評価要素：${x.signals.join('・')||'S/A・引っ張り・風車盤の加点なし'}。${saved.gaps?`同桁で${saved.gaps[j][digit]}回未出現。`:''}`);
    if(cut)out.push(`第${j+1}数字の採用境界は${cut.digit}（5位・${cut.score.toFixed(3)}点、${cut.count}回）。${x.score<cut.score?'加点合計が採用境界より低かったため候補外。':'同点で、出現回数または数字順の順位により候補外。'}出現間隔で除外したわけではありません。`);
  });
  const tickets=saved.tickets.map(p=>Array.isArray(p)?p:p.numbers);
  if(game==='numbers3'){
    const inside=draw.numbers.slice(-2).every((n,j)=>saved.top[j+1].top.some(x=>x.digit===n));
    const hit=tickets.some(p=>p.join('')===draw.numbers.slice(-2).join(''));
    out.push(`ミニ下2桁：${inside?'両桁とも候補内':'候補外の桁あり'}。${hit?'公開10口に的中あり。':inside?'候補には入ったが10口への組合せ選抜で拾えませんでした。':'まず下2桁の候補選定が検証対象です。'}`);
  }else{
    const positionInside=draw.numbers.every((n,j)=>saved.top[j].top.some(x=>x.digit===n));
    let boxInside=false;product(saved.top.map(p=>p.top.map(x=>x.digit)),p=>{if(box(p)===box(draw.numbers))boxInside=true;});
    const hit=tickets.some(p=>box(p)===box(draw.numbers));
    out.push(`セット：ストレート候補${positionInside?'内':'外'}／BOXを構成${boxInside?'可能':'不可'}。${hit?'公開10口に的中あり。':boxInside?'候補では構成可能でしたが、除外条件・10口選抜の段階で拾えませんでした。':'TOP5候補から当選BOXを作れず、候補選定が検証対象です。'}`);
  }
  return out;
}
function settlement(game,tickets,draw){
  const details=tickets.map(a=>{
    let rank=null,pay=0;const n=a.filter(x=>draw.numbers.includes(x)).length,b=a.filter(x=>draw.bonus?.includes(x)).length;
    if(game==='numbers3'){if(a.join('')===draw.numbers.slice(-2).join('')){rank='ミニ';pay=draw.amounts[4];}}
    else if(game==='numbers4'){if(a.join('')===draw.numbers.join('')){rank='セットストレート';pay=draw.amounts[2];}else if(box(a)===box(draw.numbers)){rank='セットボックス';pay=draw.amounts[3];}}
    else{const tier=game==='loto7'?(n===7?1:n===6&&b?2:n===6?3:n===5?4:n===4?5:n===3&&b?6:null):game==='loto6'?(n===6?1:n===5&&b?2:n===5?3:n===4?4:n===3?5:null):(n===5?1:n===4&&b?2:n===4?3:n===3?4:null);if(tier){rank=tier+'等';pay=draw.amounts[tier-1];}}
    if(!Number.isFinite(pay))throw Error(`${game}: 当選金額が不足`);
    const positional=a.filter((n,j)=>n===draw.numbers[j]).length;
    const actualCounts=counts(draw.numbers);let matched=0;for(const n of a)if(actualCounts[n]){matched++;actualCounts[n]--;}
    return {numbers:a,rank,pay,near:game==='numbers4'&&!rank?{straight:positional===3,box:matched===3}:null};
  });
  const purchase=tickets.length*(game==='loto7'?300:200),returned=details.reduce((s,d)=>s+d.pay,0);
  return {purchase,return:returned,rate:returned/purchase*100,profit:returned-purchase,details};
}
function targetDate(now=new Date()){
  const jst=new Date(now.getTime()+9*3600e3);
  if(jst.getUTCHours()<21)jst.setUTCDate(jst.getUTCDate()-1);
  while([0,6].includes(jst.getUTCDay()))jst.setUTCDate(jst.getUTCDate()-1);
  return jst.toISOString().slice(0,10);
}
module.exports={band,loadDraws,transitions,facts,validLoto,patterns,lotoForecast,numbersForecast,numbersPicks,candidateReview,settlement,targetDate,CONFIG};
