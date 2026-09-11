#!/usr/bin/env node
/* Validate locale files against English. Keeps JSON APIs static and CI-friendly.
 * The build owns the coverage document (feeds/translation-status.json, mirrored
 * to api/translation-status.json by publish_repo_artifacts); CI only verifies
 * the committed copy still matches the locale state and never rewrites it. */
const fs=require('fs'), path=require('path');
const dir=path.join(__dirname,'..','locales'); let errors=0;
function parse(file){let dup=[]; let text=fs.readFileSync(file,'utf8'); try { return JSON.parse(text,(k,v)=>v); } catch(e){ console.error(`[ERROR] ${path.basename(file)} invalid JSON: ${e.message}`); errors++; return {}; }}
function flat(o,p='',out={}){Object.entries(o).forEach(([k,v])=>{let key=p?`${p}.${k}`:k;if(v&&typeof v==='object'&&!Array.isArray(v))flat(v,key,out);else out[key]=v;});return out;}
function duplicates(file){let s=fs.readFileSync(file,'utf8'), d=new Set(), stack=[], i=0, n=s.length;
  function skipString(){i++; while(i<n){let c=s[i]; if(c==='\\'){i+=2; continue;} i++; if(c==='"')break;}}
  while(i<n){let c=s[i];
    if(c==='"'){let start=i; skipString(); let j=i; while(j<n&&/\s/.test(s[j]))j++;
      if(s[j]===':'&&stack.length&&stack[stack.length-1].obj){let key=s.slice(start,i);
        let scope=stack[stack.length-1]; if(scope.keys.has(key))d.add(key.slice(1,-1)); scope.keys.add(key);}}
    else if(c==='{'){stack.push({obj:true,keys:new Set()}); i++;}
    else if(c==='['){stack.push({obj:false}); i++;}
    else if(c==='}'||c===']'){stack.pop(); i++;}
    else i++;}
  if(d.size){console.error(`[ERROR] ${path.basename(file)} duplicate keys: ${[...d].join(', ')}`);errors++;}}
if(!fs.existsSync(dir)){console.error('[ERROR] locales directory missing');process.exit(1)}
let files=fs.readdirSync(dir).filter(x=>x.endsWith('.json')).sort(); if(!files.includes('en.json')){console.error('[ERROR] en.json is required');process.exit(1)}
let en=flat(parse(path.join(dir,'en.json'))), report={};
for(const name of files){let f=path.join(dir,name); duplicates(f); let data=flat(parse(f)), missing=Object.keys(en).filter(k=>!(k in data)), empty=Object.keys(data).filter(k=>data[k]===null||String(data[k]).trim()===''); if(missing.length){console.error(`[ERROR] ${name} missing: ${missing.join(', ')}`);errors++;} if(empty.length){console.error(`[ERROR] ${name} empty: ${empty.join(', ')}`);errors++;} report[name.slice(0,-5)]=Math.round((Object.keys(en).length-missing.length)/Object.keys(en).length*100);}
let docPath=path.join(__dirname,'..','feeds','translation-status.json'), committed=null;
if(!fs.existsSync(docPath)){console.error('[ERROR] feeds/translation-status.json missing: the build owns this document - run `python3 scripts/omnisource.py --no-sync --no-health` and commit it');errors++;}
else{try{committed=JSON.parse(fs.readFileSync(docPath,'utf8')); if(typeof committed!=='object'||committed===null||Array.isArray(committed))throw new Error('top level must be a JSON object');}catch(e){console.error(`[ERROR] feeds/translation-status.json invalid: ${e.message}`);errors++;committed=null;}}
if(committed){for(const [name,pct] of Object.entries(report)){if(committed[name]!==pct){console.error(`[ERROR] translation-status drift for ${name}: committed ${committed[name]} != actual ${pct} - rebuild and commit`);errors++;}} for(const name of Object.keys(committed)){if(!(name in report)){console.error(`[ERROR] translation-status lists unknown locale ${name} - rebuild and commit`);errors++;}}}
if(errors){console.error(`Translation validation failed with ${errors} error(s).`);process.exit(1)} console.log('Translation validation passed:',report);
