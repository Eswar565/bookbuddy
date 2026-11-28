/**
 * Book Buddy - Media Pages Interactive Helpers
 * - Accessible Share Popover Menu (Copy Link, WhatsApp, Email)
 * - Native Web Share API (navigator.share) on supported mobile devices
 * - Clipboard Copy with animated toast notification
 * - Newspaper description clamp/read-more toggle
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Toast helper
  function showToast(message) {
    let toast = document.getElementById('bb-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'bb-toast';
      toast.className = 'bb-toast';
      toast.setAttribute('role', 'status');
      toast.setAttribute('aria-live', 'polite');
      document.body.appendChild(toast);
    }
    toast.textContent = message || 'Link copied to clipboard!';
    toast.classList.add('is-visible');
    setTimeout(function () {
      toast.classList.remove('is-visible');
    }, 2500);
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        showToast('Link copied to clipboard!');
      }).catch(function () {
        legacyCopy(text);
      });
    } else {
      legacyCopy(text);
    }
  }

  function legacyCopy(text) {
    var input = document.createElement('input');
    input.value = text;
    input.style.position = 'fixed';
    input.style.opacity = '0';
    document.body.appendChild(input);
    input.select();
    try {
      document.execCommand('copy');
    } catch (e) {}
    document.body.removeChild(input);
    showToast('Link copied to clipboard!');
  }

  function closeAllShareMenus() {
    document.querySelectorAll('.bb-share-menu.is-open').forEach(function (m) {
      m.classList.remove('is-open');
      var trg = m.closest('.bb-share-dropdown-wrap')?.querySelector('.bb-share-trigger, [data-bb-share]');
      if (trg) trg.setAttribute('aria-expanded', 'false');
    });
  }

  // 2. Share button click handling
  document.querySelectorAll('[data-bb-share]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();

      var title = btn.getAttribute('data-share-title') || document.title;
      var url = btn.getAttribute('data-share-url') || window.location.href;

      // Check if Web Share API is available and device is mobile / touch
      var isMobile = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (window.innerWidth <= 768);
      if (navigator.share && navigator.canShare && isMobile) {
        try {
          if (navigator.canShare({ title: title, url: url })) {
            navigator.share({ title: title, text: title, url: url }).catch(function () {});
            return;
          }
        } catch (err) {}
      }

      // Desktop / Fallback: Toggle the accessible share popover menu
      var wrap = btn.closest('.bb-share-dropdown-wrap');
      var menu = wrap ? wrap.querySelector('.bb-share-menu') : null;
      if (!menu) {
        // Direct copy if no dropdown menu attached
        copyToClipboard(url);
        return;
      }

      var isOpen = menu.classList.contains('is-open');
      closeAllShareMenus();
      if (!isOpen) {
        menu.classList.add('is-open');
        btn.setAttribute('aria-expanded', 'true');
        var firstItem = menu.querySelector('button, a');
        if (firstItem) firstItem.focus();
      }
    });
  });

  // Copy link action inside share popover menu
  document.querySelectorAll('[data-share-action="copy"]').forEach(function (copyBtn) {
    copyBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var wrap = copyBtn.closest('.bb-share-dropdown-wrap');
      var trigger = wrap ? wrap.querySelector('[data-bb-share]') : null;
      var url = trigger ? (trigger.getAttribute('data-share-url') || window.location.href) : window.location.href;
      copyToClipboard(url);
      closeAllShareMenus();
      if (trigger) trigger.focus();
    });
  });

  // Dismiss menu on outside click
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.bb-share-dropdown-wrap')) {
      closeAllShareMenus();
    }
  });

  // Dismiss menu on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeAllShareMenus();
    }
  });

  // 3. Read more toggle for Newspaper descriptions
  document.querySelectorAll('[data-read-more-btn]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const targetId = btn.getAttribute('data-target');
      const descEl = document.getElementById(targetId);
      if (!descEl) return;

      const isClamped = descEl.classList.contains('clamped');
      if (isClamped) {
        descEl.classList.remove('clamped');
        btn.textContent = 'Show less';
      } else {
        descEl.classList.add('clamped');
        btn.textContent = 'Read more';
      }
    });
  });
});


// ==========================================================================
// Filter Editions live update with URL sync (Shared Component)
// ==========================================================================
(function initEditionFilters() {
  function setup() {
    const form = document.querySelector('.filter-sidebar-form');
    if (!form) return;

    const yearSelect = form.querySelector('select[name="year"]');
    const monthSelect = form.querySelector('select[name="month"]');
    const clearLink = document.querySelector('#filter-clear-btn');
    const container = document.querySelector('#editions-container');
    const countDisplay = document.querySelector('#filter-results-count');

    function updateFilters(pushToHistory) {
      if (typeof pushToHistory === 'undefined') pushToHistory = true;

      const year = yearSelect ? yearSelect.value.trim() : '';
      const month = monthSelect ? monthSelect.value.trim() : '';

      const params = new URLSearchParams();
      if (year) params.set('year', year);
      if (month) params.set('month', month);

      const queryString = params.toString();
      const targetUrl = window.location.pathname + (queryString ? '?' + queryString : '');

      if (pushToHistory) {
        window.history.pushState({ year: year, month: month }, '', targetUrl);
      }

      if (clearLink) {
        clearLink.style.display = (year || month) ? 'inline-block' : 'none';
      }

      if (container) {
        container.style.opacity = '0.5';
        container.style.pointerEvents = 'none';
      }

      fetch(targetUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.text();
        })
        .then(function (html) {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');

          const newContainer = doc.querySelector('#editions-container');
          if (newContainer && container) {
            container.innerHTML = newContainer.innerHTML;
          }

          const newCount = doc.querySelector('#filter-results-count');
          if (newCount && countDisplay) {
            countDisplay.innerHTML = newCount.innerHTML;
          }
        })
        .catch(function (err) {
          console.error('Filter live update failed, falling back to submit:', err);
          form.submit();
        })
        .finally(function () {
          if (container) {
            container.style.opacity = '1';
            container.style.pointerEvents = '';
          }
        });
    }

    if (yearSelect) {
      yearSelect.addEventListener('change', function () {
        updateFilters(true);
      });
    }

    if (monthSelect) {
      monthSelect.addEventListener('change', function () {
        updateFilters(true);
      });
    }

    if (clearLink) {
      clearLink.addEventListener('click', function (e) {
        e.preventDefault();
        if (yearSelect) yearSelect.value = '';
        if (monthSelect) monthSelect.value = '';
        updateFilters(true);
      });
    }

    document.addEventListener('click', function (e) {
      if (e.target && e.target.id === 'empty-clear-btn') {
        e.preventDefault();
        if (yearSelect) yearSelect.value = '';
        if (monthSelect) monthSelect.value = '';
        updateFilters(true);
      }
    });

    window.addEventListener('popstate', function () {
      const params = new URLSearchParams(window.location.search);
      if (yearSelect) yearSelect.value = params.get('year') || '';
      if (monthSelect) monthSelect.value = params.get('month') || '';
      updateFilters(false);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }
})();
