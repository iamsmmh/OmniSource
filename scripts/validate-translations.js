#!/usr/bin/env node
/* Validate locale files against English. Keeps JSON APIs static and CI-friendly. */
const fs=require('fs'), path=require('path');
const dir=path.join(__dirname,'..','locales'); let errors=0;
function parse(file){let dup=[]; let text=fs.readFileSync(file,'utf8'); try { return JSON.parse(text,(k,v)=>v); } catch(e){ console.error(`[ERROR] ${path.basename(file)} invalid JSON: ${e.message}`); errors++; return {}; }}
function flat(o,p='',out={}){Object.entries(o).forEach(([k,v])=>{let key=p?`${p}.${k}`:k;if(v&&typeof v==='object'&&!Array.isArray(v))flat(v,key,out);else out[key]=v;});return out;}
function duplicates(file){let s=fs.readFileSync(file,'utf8'), re=/"([^"\\]+)"\s*:/g,m, seen=new Set(), d=new Set(); while((m=re.exec(s))){if(seen.has(m[1]))d.add(m[1]);seen.add(m[1]);} if(d.size){console.error(`[ERROR] ${path.basename(file)} duplicate keys: ${[...d].join(', ')}`);errors++;}}
if(!fs.existsSync(dir)){console.error('[ERROR] locales directory missing');process.exit(1)}
let files=fs.readdirSync(dir).filter(x=>x.endsWith('.json')); if(!files.includes('en.json')){console.error('[ERROR] en.json is required');process.exit(1)}
let en=flat(parse(path.join(dir,'en.json'))), report={};
for(const name of files){let f=path.join(dir,name); duplicates(f); let data=flat(parse(f)), missing=Object.keys(en).filter(k=>!(k in data)), empty=Object.keys(data).filter(k=>data[k]===null||String(data[k]).trim()===''); if(missing.length){console.error(`[ERROR] ${name} missing: ${missing.join(', ')}`);errors++;} if(empty.length){console.error(`[ERROR] ${name} empty: ${empty.join(', ')}`);errors++;} report[name.slice(0,-5)]=Math.round((Object.keys(en).length-missing.length)/Object.keys(en).length*100);}
fs.mkdirSync(path.join(__dirname,'..','api'),{recursive:true}); fs.writeFileSync(path.join(__dirname,'..','api','translation-status.json'),JSON.stringify(report,null,2)+'\n');
if(errors){console.error(`Translation validation failed with ${errors} error(s).`);process.exit(1)} console.log('Translation validation passed:',report);
