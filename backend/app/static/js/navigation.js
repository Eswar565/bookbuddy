/* One navigation controller for desktop and mobile. */
document.addEventListener('DOMContentLoaded',()=>{
 const nav=document.querySelector('#primary-navigation'),toggle=document.querySelector('[data-menu-toggle]'),menus=[...document.querySelectorAll('[data-nav]')],desktop=window.matchMedia('(min-width:1200px)');
 const closeDropdowns=()=>menus.forEach(item=>item.open=false);
 const search=document.querySelector('[data-search-box]');
 search?.addEventListener('toggle',()=>{if(search.open)search.querySelector('input')?.focus()});
 const closeAll=()=>{closeDropdowns();nav?.classList.remove('open');toggle?.setAttribute('aria-expanded','false')};
 toggle?.addEventListener('click',()=>{const isOpen=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(isOpen));if(!isOpen)closeDropdowns()});
 menus.forEach(item=>item.addEventListener('toggle',()=>{if(item.open)menus.forEach(other=>{if(other!==item)other.open=false})}));
 document.addEventListener('click',event=>{if(!event.target.closest('.site-header')){closeAll();if(search)search.open=false}else if(search&&!event.target.closest('[data-search-box]'))search.open=false});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){if(search?.open){search.open=false;search.querySelector('summary')?.focus();return}const open=menus.find(item=>item.open);const mobileOpen=nav?.classList.contains('open');closeAll();if(open)open.querySelector('summary').focus();else if(mobileOpen)toggle?.focus()}});
 desktop.addEventListener('change',closeAll);
 nav?.querySelectorAll('a').forEach(link=>{const target=new URL(link.href,location.href);if(target.pathname===location.pathname&&(!target.search||target.search===location.search)){link.setAttribute('aria-current','page');link.closest('details')?.classList.add('current')}link.addEventListener('click',()=>{if(!desktop.matches)closeAll()})});
 document.querySelectorAll('[data-filter-input]').forEach(input=>input.addEventListener('input',()=>{const q=input.value.toLowerCase().trim(),target=document.querySelector(input.dataset.filterInput);target?.querySelectorAll('[data-filter-item]').forEach(item=>item.hidden=!!q&&!item.textContent.toLowerCase().includes(q))}));
});
