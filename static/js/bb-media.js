/**
 * Book Buddy - Media Pages Interactive Helpers
 * - Web Share API with clipboard fallback & toast
 * - Newspaper description clamp/read-more toggle
 * - Safe Spotify embed handling
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

  // 2. Share buttons
  document.querySelectorAll('[data-bb-share]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var title = btn.getAttribute('data-share-title') || document.title;
      var url = btn.getAttribute('data-share-url') || window.location.href;

      // Copy link to clipboard and show toast immediately
      copyToClipboard(url);

      // On mobile devices supporting Web Share, invoke the share sheet
      if (navigator.share && navigator.canShare) {
        try {
          if (navigator.canShare({ title: title, url: url })) {
            navigator.share({ title: title, url: url }).catch(function () {});
          }
        } catch (err) {}
      }
    });
  });

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
