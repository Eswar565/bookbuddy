/**
 * Book Buddy - Shared Unified Dropdown & Select Controller
 * Handles custom dropdowns, listboxes, keyboard navigation, and automatic native <select> enhancement.
 */
(function () {
  'use strict';

  function createChevronSvg() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'bb-chevron');
    svg.setAttribute('width', '16');
    svg.setAttribute('height', '16');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2.5');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    var polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('points', '6 9 12 15 18 9');
    svg.appendChild(polyline);
    return svg;
  }

  function createCheckSvg() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'check');
    svg.setAttribute('width', '16');
    svg.setAttribute('height', '16');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2.5');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    var polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('points', '20 6 9 17 4 12');
    svg.appendChild(polyline);
    return svg;
  }

  // Position calculation with viewport flip-up
  function adjustPosition(trigger, menu) {
    if (!trigger || !menu) return;
    var rect = trigger.getBoundingClientRect();
    var spaceBelow = window.innerHeight - rect.bottom;
    var spaceAbove = rect.top;
    var estimatedHeight = menu.offsetHeight || 260;

    if (spaceBelow < estimatedHeight + 10 && spaceAbove > spaceBelow) {
      menu.classList.add('dropdown-menu--up');
      menu.classList.add('bb-select-menu--up');
    } else {
      menu.classList.remove('dropdown-menu--up');
      menu.classList.remove('bb-select-menu--up');
    }
  }

  // Setup custom select enhancement for a native <select>
  function setupCustomSelect(selectEl) {
    if (!selectEl || selectEl.dataset.customized === 'true') return;
    selectEl.dataset.customized = 'true';

    // Container
    var wrap = document.createElement('div');
    wrap.className = 'bb-custom-select-wrap';
    wrap.style.position = 'relative';
    wrap.style.width = '100%';

    // Trigger button
    var trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'bb-select-trigger dropdown-trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    if (selectEl.id) {
      trigger.id = selectEl.id + '-custom-trigger';
    }

    var valueSpan = document.createElement('span');
    valueSpan.className = 'bb-select-value';
    trigger.appendChild(valueSpan);
    trigger.appendChild(createChevronSvg());

    // Menu listbox
    var menu = document.createElement('div');
    menu.className = 'bb-select-menu dropdown-menu';
    menu.setAttribute('role', 'listbox');
    menu.style.display = 'none';
    if (selectEl.id) {
      menu.id = selectEl.id + '-custom-menu';
    }

    // Insert wrapper in place of select
    selectEl.parentNode.insertBefore(wrap, selectEl);
    wrap.appendChild(trigger);
    wrap.appendChild(menu);
    wrap.appendChild(selectEl);

    // Hide original select visually while keeping it accessible to forms
    selectEl.style.position = 'absolute';
    selectEl.style.opacity = '0';
    selectEl.style.pointerEvents = 'none';
    selectEl.style.width = '1px';
    selectEl.style.height = '1px';
    selectEl.style.overflow = 'hidden';
    selectEl.style.clip = 'rect(0, 0, 0, 0)';
    selectEl.setAttribute('tabindex', '-1');

    function populateOptions() {
      menu.innerHTML = '';
      var options = Array.from(selectEl.options);
      var selectedOpt = selectEl.selectedOptions[0] || options[0];

      if (selectedOpt) {
        valueSpan.textContent = selectedOpt.textContent;
      } else {
        valueSpan.textContent = 'Select an option';
      }

      options.forEach(function (opt) {
        var item = document.createElement('button');
        item.type = 'button';
        item.className = 'dropdown-item bb-select-item';
        item.setAttribute('role', 'option');
        item.dataset.value = opt.value;
        var isSelected = opt.selected;
        item.setAttribute('aria-selected', isSelected ? 'true' : 'false');
        if (isSelected) item.classList.add('is-selected');
        if (opt.disabled) item.disabled = true;

        var textSpan = document.createElement('span');
        textSpan.textContent = opt.textContent;
        item.appendChild(textSpan);
        item.appendChild(createCheckSvg());

        item.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          selectEl.value = opt.value;
          selectEl.dispatchEvent(new Event('change', { bubbles: true }));
          selectEl.dispatchEvent(new Event('input', { bubbles: true }));
          updateSelection();
          closeMenu();
          trigger.focus();
        });

        menu.appendChild(item);
      });
    }

    function updateSelection() {
      var val = selectEl.value;
      var selectedOpt = selectEl.selectedOptions[0];
      if (selectedOpt) {
        valueSpan.textContent = selectedOpt.textContent;
      }
      var items = menu.querySelectorAll('.bb-select-item');
      items.forEach(function (btn) {
        var isMatch = btn.dataset.value === val;
        btn.setAttribute('aria-selected', isMatch ? 'true' : 'false');
        if (isMatch) {
          btn.classList.add('is-selected');
        } else {
          btn.classList.remove('is-selected');
        }
      });
    }

    function openMenu() {
      // Close other open menus
      document.querySelectorAll('.dropdown-menu[role="listbox"], .dropdown-menu[role="menu"]').forEach(function (m) {
        if (m !== menu) {
          m.style.display = 'none';
          var parentTrigger = m.parentElement ? m.parentElement.querySelector('[aria-expanded="true"]') : null;
          if (parentTrigger) parentTrigger.setAttribute('aria-expanded', 'false');
        }
      });

      menu.style.display = 'block';
      trigger.setAttribute('aria-expanded', 'true');
      adjustPosition(trigger, menu);

      // Focus selected item
      var selectedItem = menu.querySelector('.bb-select-item.is-selected') || menu.querySelector('.bb-select-item:not([disabled])');
      if (selectedItem) selectedItem.focus();
    }

    function closeMenu() {
      menu.style.display = 'none';
      menu.classList.remove('dropdown-menu--up');
      menu.classList.remove('bb-select-menu--up');
      trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (menu.style.display === 'block') {
        closeMenu();
      } else {
        openMenu();
      }
    });

    // Keyboard navigation
    wrap.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        closeMenu();
        trigger.focus();
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        if (menu.style.display !== 'block') {
          e.preventDefault();
          openMenu();
        } else {
          e.preventDefault();
          var items = Array.from(menu.querySelectorAll('.bb-select-item:not([disabled])'));
          var curIdx = items.indexOf(document.activeElement);
          if (e.key === 'ArrowDown') {
            var nextIdx = curIdx < items.length - 1 ? curIdx + 1 : 0;
            items[nextIdx].focus();
          } else {
            var prevIdx = curIdx > 0 ? curIdx - 1 : items.length - 1;
            items[prevIdx].focus();
          }
        }
      } else if (e.key === 'Home' && menu.style.display === 'block') {
        e.preventDefault();
        var first = menu.querySelector('.bb-select-item:not([disabled])');
        if (first) first.focus();
      } else if (e.key === 'End' && menu.style.display === 'block') {
        e.preventDefault();
        var all = menu.querySelectorAll('.bb-select-item:not([disabled])');
        if (all.length) all[all.length - 1].focus();
      }
    });

    // Sync when native select changes programmatically
    selectEl.addEventListener('change', updateSelection);

    // Mutation observer for dynamically populated options (e.g. tier-select)
    var observer = new MutationObserver(function () {
      populateOptions();
    });
    observer.observe(selectEl, { childList: true, subtree: true });

    // Initial population
    populateOptions();
  }

  // Auto-init on page load
  document.addEventListener('DOMContentLoaded', function () {
    // 1. Important selects to enhance into full custom themed listboxes
    var targetSelectors = [
      '#top-filter-lang',
      '#req-delivery-mode',
      '#tier-select',
      '#student_grade',
      '#service_mode',
      '.js-custom-select'
    ];

    targetSelectors.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        setupCustomSelect(el);
      });
    });

    // 2. Global outside click handler
    document.addEventListener('click', function (e) {
      document.querySelectorAll('.bb-custom-select-wrap').forEach(function (wrap) {
        if (!wrap.contains(e.target)) {
          var menu = wrap.querySelector('.bb-select-menu');
          var trigger = wrap.querySelector('.bb-select-trigger');
          if (menu && menu.style.display === 'block') {
            menu.style.display = 'none';
            menu.classList.remove('dropdown-menu--up', 'bb-select-menu--up');
          }
          if (trigger) trigger.setAttribute('aria-expanded', 'false');
        }
      });
    });

    // 3. Header nav details[data-nav-dropdown] enhancement (hover, ARIA, keyboard nav)
    var navDropdowns = document.querySelectorAll('.bb8-nav details.bb8-dropdown');
    navDropdowns.forEach(function (det) {
      var summary = det.querySelector('summary');
      var menu = det.querySelector('.nav-dropdown-menu, .bb8-dropdown-menu');
      if (!summary || !menu) return;

      // ARIA setup
      summary.setAttribute('aria-haspopup', 'true');
      summary.setAttribute('aria-expanded', det.open ? 'true' : 'false');
      menu.setAttribute('role', 'menu');
      menu.querySelectorAll('a').forEach(function (a) {
        a.setAttribute('role', 'menuitem');
      });

      // Sync aria-expanded on toggle
      det.addEventListener('toggle', function () {
        summary.setAttribute('aria-expanded', det.open ? 'true' : 'false');
      });

      // Desktop hover bridge & auto open/close
      var isDesktop = function () {
        return window.matchMedia('(min-width: 901px)').matches;
      };

      var closeTimer = null;

      summary.addEventListener('click', function () {
        setTimeout(function () {
          if (det.open) {
            det.dataset.openedByClick = 'true';
            summary.setAttribute('aria-expanded', 'true');
          } else {
            delete det.dataset.openedByClick;
            summary.setAttribute('aria-expanded', 'false');
          }
        }, 10);
      });

      det.addEventListener('mouseenter', function () {
        if (!isDesktop()) return;
        if (closeTimer) {
          clearTimeout(closeTimer);
          closeTimer = null;
        }
        navDropdowns.forEach(function (other) {
          if (other !== det && other.open && other.dataset.openedByClick !== 'true') {
            other.removeAttribute('open');
            delete other.dataset.openedByClick;
            var s = other.querySelector('summary');
            if (s) s.setAttribute('aria-expanded', 'false');
          }
        });
        if (!det.open) {
          det.setAttribute('open', '');
          summary.setAttribute('aria-expanded', 'true');
        }
      });

      det.addEventListener('mouseleave', function () {
        if (!isDesktop()) return;
        if (det.dataset.openedByClick === 'true') {
          return;
        }
        closeTimer = setTimeout(function () {
          if (det.dataset.openedByClick !== 'true') {
            det.removeAttribute('open');
            summary.setAttribute('aria-expanded', 'false');
          }
        }, 120);
      });

      // Keyboard navigation on summary
      summary.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
          if (!det.open) {
            det.setAttribute('open', '');
            summary.setAttribute('aria-expanded', 'true');
          }
          var firstItem = menu.querySelector('a[role="menuitem"]');
          if (firstItem) {
            e.preventDefault();
            firstItem.focus();
          }
        } else if (e.key === 'ArrowUp') {
          if (!det.open) {
            det.setAttribute('open', '');
            summary.setAttribute('aria-expanded', 'true');
          }
          var items = menu.querySelectorAll('a[role="menuitem"]');
          if (items.length) {
            e.preventDefault();
            items[items.length - 1].focus();
          }
        }
      });

      // Keyboard navigation inside menu
      menu.addEventListener('keydown', function (e) {
        var items = Array.from(menu.querySelectorAll('a[role="menuitem"]'));
        var idx = items.indexOf(document.activeElement);

        if (e.key === 'ArrowDown') {
          e.preventDefault();
          var next = idx < items.length - 1 ? idx + 1 : 0;
          items[next].focus();
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          var prev = idx > 0 ? idx - 1 : items.length - 1;
          items[prev].focus();
        } else if (e.key === 'Home') {
          e.preventDefault();
          if (items[0]) items[0].focus();
        } else if (e.key === 'End') {
          e.preventDefault();
          if (items[items.length - 1]) items[items.length - 1].focus();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          det.removeAttribute('open');
          delete det.dataset.openedByClick;
          summary.setAttribute('aria-expanded', 'false');
          summary.focus();
        } else if (e.key === 'Tab') {
          det.removeAttribute('open');
          delete det.dataset.openedByClick;
          summary.setAttribute('aria-expanded', 'false');
        }
      });
    });

    // Close nav dropdowns on outside click
    document.addEventListener('click', function (e) {
      navDropdowns.forEach(function (det) {
        if (det.open && !det.contains(e.target)) {
          det.removeAttribute('open');
          delete det.dataset.openedByClick;
          var s = det.querySelector('summary');
          if (s) s.setAttribute('aria-expanded', 'false');
        }
      });
    });

    // Global Esc listener for open nav dropdowns
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        navDropdowns.forEach(function (det) {
          if (det.open) {
            det.removeAttribute('open');
            delete det.dataset.openedByClick;
            var s = det.querySelector('summary');
            if (s) {
              s.setAttribute('aria-expanded', 'false');
              s.focus();
            }
          }
        });
      }
    });
  });

  // Export helper
  window.bbSetupCustomSelect = setupCustomSelect;
})();
