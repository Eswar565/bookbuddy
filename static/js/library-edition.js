/* Book Buddy v29: progressive enhancement for the focused skill content studio. */
(() => {
  'use strict';
  const subject = document.getElementById('s29-create-subject');
  const kind = document.getElementById('s29-create-kind');
  const rules = document.getElementById('s29-activity-kinds');
  if (subject && kind && rules) {
    let allowed = {};
    try { allowed = JSON.parse(rules.textContent); } catch { /* server validates */ }
    const labels = {
      quiz: 'Multiple choice quiz', flashcards: 'Interactive flashcards',
      'high-frequency': 'High-frequency vocabulary', writing: 'Writing assignment',
      listening: 'Listening comprehension', speaking: 'Speaking recording',
      sorting: 'Needs / Wants sorting game'
    };
    function update() {
      const selected = kind.value;
      kind.replaceChildren();
      (allowed[subject.value] || ['quiz']).forEach(type => {
        const opt = document.createElement('option');
        opt.value = type; opt.textContent = labels[type] || type;
        kind.append(opt);
      });
      if ([...kind.options].some(x => x.value === selected)) kind.value = selected;
    }
    subject.addEventListener('change', update);
    update();
  }
})();
