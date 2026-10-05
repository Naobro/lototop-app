const test = require('node:test');
const assert = require('node:assert/strict');
const { transitions, facts, validLoto, settlement, targetDate, numbersPicks } = require('../engine');
function selectPool(draws,config){
  const fs=require('fs'),path=require('path'),vm=require('vm'),c=vm.createContext({});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../lib/stats.js'),'utf8')+'\nthis.L=LotoStats;',c);
  return c.L.calcSelectedNumbers(draws.map(d=>({'回号':d.round,'本数字':d.numbers})),{...config,mainKey:'本数字',tierRules:c.L.DEFAULT_TIER_RULES},24);
}
test('pre-draw position leader 06 is retained despite recent appearance and uneven timing',()=>{
  const e=require('../engine'),d=e.loadDraws('loto7','2026-09-25');
  const pool=selectPool(d,{mainCount:7,maxNumber:37,selectedCount:27});
  assert.ok(pool.selected.includes(6),'06 is S and position-2 leader, not a gap-based deletion');
  assert.equal(pool.selected.length,27);
});
test('rare last-draw numbers are not unconditionally reserved ahead of SA and positional candidates',()=>{
  const draws=Array.from({length:24},(_,i)=>({round:i+1,numbers:i===23?[4,5]:[1,2]}));
  const pool=selectPool(draws,{mainCount:2,maxNumber:5,selectedCount:2});
  assert.deepEqual(Array.from(pool.selected),[1,2]);
});
test('candidate review distinguishes N3 first-digit omission from a winning mini',()=>{
  const e=require('../engine');
  const saved={top:[{top:[{digit:2}]},{top:[{digit:6}]},{top:[{digit:9}]}],tickets:[[6,9]],ranking:[{top:[{digit:2,score:3,count:5,signals:['S']},{digit:8,score:1,count:2,signals:[]}]},{top:[{digit:6,score:2,count:3,signals:['A']}]},{top:[{digit:9,score:2,count:3,signals:['A']}]}]};
  const text=e.candidateReview('numbers3',saved,{numbers:[8,6,9]}).join('\n');
  assert.match(text,/第1数字.*8.*候補外/);assert.match(text,/ミニ.*候補内/);
});
test('missing historical diagnostics do not invent an exclusion reason',()=>{
  const e=require('../engine');
  const text=e.candidateReview('loto7',{tickets:[]},{numbers:[6],bonus:[]}).join('\n');
  assert.match(text,/記録.*不足/);
});
test('all three loto games produce ten compliant tickets from their dated candidates',()=>{
  const e=require('../engine');
  for(const game of ['loto6','loto7','miniloto']){
    const d=e.loadDraws(game,'2026-10-02'),p=e.lotoForecast(game,d);
    assert.equal(p.patterns.length,5);assert.equal(p.tickets.length,10);
    for(const ticket of p.tickets){assert.ok(e.validLoto(ticket.numbers,d));assert.ok(ticket.numbers.every(n=>p.selection.selected.includes(n)));}
  }
});
test('24-draw analysis is date-filtered and cold numbers are capped at two',()=>{
  const e=require('../engine'),d=e.loadDraws('loto6','2026-10-02');
  assert.equal(d.at(-1).date,'2026-10-01');
  assert.equal(e.validLoto([12,17,18,25,35,41],d),false);
});
test('latest 24 draws give 23 transitions and do not count the open last draw', () => {
  const draws = Array.from({length:30}, (_,i)=>({date:'2026-10-02',numbers:[i%2 ? 12 : 2]}));
  const t=transitions(draws,1);
  assert.equal(t.length,1); assert.equal(t[0].total,11);
  assert.equal(t[0].rates[1],1);
});
test('hard rules reject pull three, run three, tail triple and four in one band',()=>{
  const draws=[{numbers:[2,14,20,21,31,39]}];
  assert.equal(validLoto([2,14,20,28,35,41],draws),false);
  assert.equal(validLoto([1,6,13,14,15,37],draws),false);
  assert.equal(validLoto([1,11,15,22,31,38],draws),false);
  assert.equal(validLoto([1,10,12,15,18,35],draws),false);
  assert.equal(validLoto([1,6,12,14,15,37],draws),true);
});
test('published Oct 2 tickets settle against actual prize columns, mini and set',()=>{
  assert.equal(settlement('loto7',[[1,16,23,25,27,32,36]],{numbers:[1,6,12,23,28,32,36],bonus:[31,34],amounts:[0,5670900,330200,6200,1400,1100]}).return,1400);
  assert.equal(settlement('numbers3',[[6,9]],{numbers:[8,6,9],amounts:[88600,14700,51600,7300,8800]}).return,8800);
  assert.equal(settlement('numbers4',[[7,3,8,0],[0,7,3,8]],{numbers:[7,3,8,0],amounts:[1125400,46800,586100,23400]}).return,609500);
});
test('overnight retry retains latest completed Friday, not Saturday or Monday daytime',()=>{
  assert.equal(targetDate(new Date('2026-10-02T18:00:00Z')),'2026-10-02');
  assert.equal(targetDate(new Date('2026-10-04T23:00:00Z')),'2026-10-02');
  assert.equal(targetDate(new Date('2026-10-05T12:00:00Z')),'2026-10-05');
});
test('N4 excludes past boxes, triples and double doubles, retains ten unique boxes',()=>{
  const top=Array.from({length:4},()=>Array.from({length:5},(_,digit)=>({digit,score:5-digit,count:5-digit})));
  const draws=[{numbers:[0,1,2,3]}];
  const p=numbersPicks('numbers4',top,draws);
  assert.equal(p.length,10);
  assert.equal(new Set(p.map(x=>x.slice().sort().join(''))).size,10);
  for(const x of p){const counts={};x.forEach(n=>counts[n]=(counts[n]||0)+1);assert.ok(Math.max(...Object.values(counts))<=2);assert.ok(Object.values(counts).filter(n=>n===2).length<=1);assert.notEqual(x.slice().sort().join(''),'0123');}
});
