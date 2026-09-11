/* OmniSource runtime localization. Works from GitHub Pages sub-paths and offline. */
(function (root) {'use strict';
  const RTL=new Set(['ar','fa','ur']); const supported=['en','es','fr','de','ar','bn','zh','ja'];
  const base=location.hostname.includes('github.io') ? '/OmniSource' : '';
  const cache={}; let lang='en';
  function storage(){try{return localStorage;}catch(_){return null;}}
  function get(o,key){return key.split('.').reduce((v,k)=>v&&v[k],o);}
  async function load(code){if(cache[code])return cache[code]; try{let r=await fetch(`${base}/locales/${code}.json`);if(!r.ok)throw Error(r.status); cache[code]=await r.json();return cache[code];}catch(e){console.warn('Locale unavailable:',code,e);return code==='en'?{}:load('en');}}
  function t(key,params){let value=get(cache[lang],key);if(value==null)value=get(cache.en,key);if(value==null){console.warn('[MISSING TRANSLATION]',key);return key;} return String(value).replace(/\$\{(\w+)\}/g,(_,k)=>params&&params[k]!=null?params[k]:`\${${k}}`);}
  function apply(){document.documentElement.lang=lang;document.documentElement.dir=RTL.has(lang)?'rtl':'ltr';document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n);});document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>el.placeholder=t(el.dataset.i18nPlaceholder));root.dispatchEvent(new CustomEvent('i18n:changed',{detail:{language:lang}}));}
  async function setLanguage(code){code=(code||'').toLowerCase().split('-')[0];if(!supported.includes(code))code='en';lang=code;let s=storage();try{s&&s.setItem('language',code);}catch(_){} await load(code);apply();return code;}
  async function init(){let s=storage(), saved=s&&s.getItem('language'), browser=(navigator.language||'en').split('-')[0];lang=supported.includes(saved)?saved:(supported.includes(browser)?browser:'en');await Promise.all([load('en'),load(lang)]);apply();}
  root.OmniI18n={t,setLanguage,init,load,cache,get language(){return lang},base}; if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})(window);
