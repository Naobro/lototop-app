// Public read-only check prevents duplicating manual posts as well as bot posts.
const fs=require('fs'),path=require('path');
const {title,nextDrawDate}=require('./schedule'),{targetDate}=require('./engine');
const date=process.argv[2]||targetDate();
(async()=>{
 const statePath=path.join(__dirname,'state/posted.json');
 const state=fs.existsSync(statePath)?JSON.parse(fs.readFileSync(statePath,'utf8')):{};
 let published=!!state[date],found=state[date];
 if(!published){
  for(let page=1;page<=3;page++){
   const r=await fetch(`https://note.com/api/v2/creators/naobillion/contents?kind=note&page=${page}`);
   if(!r.ok)throw Error(`公開済み記事の確認失敗: HTTP ${r.status}`);
   const j=await r.json(),items=j.data?.contents;
   if(!Array.isArray(items))throw Error('公開済み記事一覧の形式が不明');
   const item=items.find(n=>n.name===title(date)&&n.status==='published');
   if(item){published=true;found={key:item.key,url:`https://note.com/naobillion/n/${item.key}`,title:item.name};break;}
   if(!items.length)break;
  }
 }
 if(published&&found){
   const forecastPath=path.join(__dirname,'state/forecasts.json');
   const forecasts=fs.existsSync(forecastPath)?JSON.parse(fs.readFileSync(forecastPath,'utf8')):{};
   const prediction=forecasts[nextDrawDate(date)];
   // Only a saved note key proves this is the same ticket snapshot. Manual posts
   // need their actual tickets imported; never claim generated tickets were published.
   if(prediction?.noteKey===found.key){prediction.published=true;prediction.source=found.url;fs.writeFileSync(forecastPath,JSON.stringify(forecasts,null,2));}
   else if(!prediction?.published) console.log('手動投稿または予想未照合：実際の10口の取込みが必要です');
   fs.mkdirSync(path.dirname(statePath),{recursive:true});state[date]=found;fs.writeFileSync(statePath,JSON.stringify(state,null,2));
 }
 console.log(published?'投稿済み（重複生成・公開をスキップ）':'未投稿');
 if(process.env.GITHUB_OUTPUT)fs.appendFileSync(process.env.GITHUB_OUTPUT,`posted=${published}\n`);
})().catch(e=>{console.error(e.message);process.exit(1);});
