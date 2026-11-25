/* Progressive enhancements: all server actions still work without JavaScript. */
'use strict';
document.addEventListener('DOMContentLoaded',()=>{
 document.querySelectorAll('.sidebar a,.bb18-sidebar a').forEach(a=>{const u=new URL(a.href,location.href);if(u.pathname===location.pathname&&(!u.search||u.search===location.search)){a.setAttribute('aria-current','page');const parent=a.closest('details');if(parent)parent.open=true;}});
 document.querySelectorAll('.notice,.flash').forEach(el=>{el.setAttribute('role','status');const b=document.createElement('button');b.type='button';b.className='folio-dismiss';b.setAttribute('aria-label','Dismiss notification');b.innerHTML='<svg class="bb-icon" aria-hidden="true" focusable="false"><use href="#i-x"/></svg>';b.addEventListener('click',()=>el.remove());el.append(b);});
 document.querySelectorAll('table').forEach((table,index)=>{
  if(!table.tBodies.length||table.closest('[data-no-filter]')||table.hasAttribute('data-no-filter')||table.classList.contains('bb-compare-table'))return;
  const rows=[...table.tBodies[0].rows];if(rows.length<2)return;
  const wrap=document.createElement('div');wrap.className='folio-table-scroll';table.before(wrap);wrap.append(table);wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Scrollable records table');
  const bar=document.createElement('div');bar.className='folio-table-tools';
  const label=document.createElement('label');label.textContent='Find on this page';const input=document.createElement('input');input.type='search';input.placeholder='Filter visible records…';input.id='folio-filter-'+index;label.htmlFor=input.id;label.append(input);
  const count=document.createElement('span');count.setAttribute('role','status');count.textContent=rows.length+' records';
  const compact=document.createElement('button');compact.type='button';compact.textContent='Compact rows';compact.setAttribute('aria-pressed','false');compact.addEventListener('click',()=>{const active=table.classList.toggle('folio-compact');compact.setAttribute('aria-pressed',String(active));compact.textContent=active?'Comfortable rows':'Compact rows';});
  bar.append(label,count,compact);wrap.before(bar);
  const empty=document.createElement('tr');empty.className='folio-no-results';empty.hidden=true;const cell=document.createElement('td');cell.colSpan=rows[0].cells.length;cell.textContent='No records match this search.';empty.append(cell);table.tBodies[0].append(empty);
  input.addEventListener('input',()=>{let visible=0;const term=input.value.trim().toLocaleLowerCase();rows.forEach(row=>{row.hidden=!row.textContent.toLocaleLowerCase().includes(term);if(!row.hidden)visible++;});count.textContent=visible+' of '+rows.length+' records';empty.hidden=visible!==0;});
 });
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){document.querySelector('.workspace')?.classList.remove('menu-open');document.querySelector('.admin-menu-toggle')?.setAttribute('aria-expanded','false');}});
});
