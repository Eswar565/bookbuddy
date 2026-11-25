(()=>{'use strict';
// A reload should not unexpectedly discard the reader's position on long worksheets.
const key='bookbuddy:scroll:'+location.pathname+location.search;
try{if(performance.getEntriesByType('navigation')[0]?.type==='reload'){
 const saved=Number(sessionStorage.getItem(key)||0);
 if(saved>0)window.addEventListener('load',()=>requestAnimationFrame(()=>requestAnimationFrame(()=>window.scrollTo({top:saved,behavior:'instant'}))),{once:true});
}}
catch{}
let writePending=false;
window.addEventListener('scroll',()=>{if(writePending)return;writePending=true;requestAnimationFrame(()=>{writePending=false;try{sessionStorage.setItem(key,String(Math.round(window.scrollY)));}catch{}});},{passive:true});
// Clear when navigating away; only reload restoration uses the stored offset.
document.querySelectorAll('[data-password-toggle]').forEach(btn=>btn.addEventListener('click',()=>{const field=document.getElementById(btn.getAttribute('aria-controls'));if(!field)return;field.type=field.type==='password'?'text':'password';btn.textContent=field.type==='password'?'Show':'Hide';btn.setAttribute('aria-label',field.type==='password'?'Show password':'Hide password');}));
})();
