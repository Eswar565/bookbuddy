document.addEventListener('DOMContentLoaded',()=>{
 const workspace=document.querySelector('.workspace'),toggle=document.querySelector('.admin-menu-toggle'),side=document.querySelector('.sidebar');
 const overlay=document.createElement('div');overlay.className='admin-menu-overlay';overlay.setAttribute('aria-hidden','true');document.body.append(overlay);
 const close=()=>{workspace?.classList.remove('menu-open');toggle?.setAttribute('aria-expanded','false');overlay.classList.remove('active')};
 const syncTogglePosition=()=>{
  if(!toggle||!side)return;
  const isMobile=window.matchMedia('(max-width:849px)').matches;
  if(isMobile){
   if(toggle.parentElement!==document.body){document.body.prepend(toggle)}
  }else{
   const divider=side.querySelector('.sidebar-divider');
   if(toggle.parentElement!==side){
    if(divider){side.insertBefore(toggle,divider)}else{
     const wordmark=side.querySelector('.wordmark');
     if(wordmark&&wordmark.nextSibling){side.insertBefore(toggle,wordmark.nextSibling)}else{side.prepend(toggle)}
    }
   }
  }
 };
 syncTogglePosition();
 toggle?.addEventListener('click',()=>{
  setTimeout(()=>overlay.classList.toggle('active',Boolean(workspace?.classList.contains('menu-open'))),10);
 });
 overlay.addEventListener('click',close);
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){close();toggle?.focus()}});
 const mql=window.matchMedia('(min-width:850px)');
 const handleMediaChange=()=>{syncTogglePosition();close()};
 if(mql.addEventListener){mql.addEventListener('change',handleMediaChange)}else{mql.addListener(handleMediaChange)}
 window.addEventListener('resize',syncTogglePosition);
 side?.querySelectorAll('details').forEach(group=>group.addEventListener('toggle',()=>{if(group.open)side.querySelectorAll('details').forEach(other=>{if(other!==group)other.open=false})}));
});
