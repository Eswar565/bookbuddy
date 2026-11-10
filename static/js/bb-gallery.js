/**
 * Accessible Gallery Lightbox
 * Features:
 * - Keyboard navigation (Esc to close, ArrowLeft / ArrowRight to step)
 * - Focus trap within lightbox
 * - Focus restoration to triggering element on close
 * - Touch swipe on mobile devices
 * - Counter indicator (e.g. 3 / 12)
 * - Zero captions/titles
 */
document.addEventListener('DOMContentLoaded', function () {
  const lightbox = document.getElementById('bb-lightbox');
  if (!lightbox) return;

  const lightboxImg = lightbox.querySelector('.bb-lightbox-media');
  const counterEl = lightbox.querySelector('.bb-lightbox-counter');
  const closeBtn = lightbox.querySelector('.bb-lightbox-close');
  const prevBtn = lightbox.querySelector('.bb-lightbox-prev');
  const nextBtn = lightbox.querySelector('.bb-lightbox-next');
  const tiles = Array.from(document.querySelectorAll('[data-gallery-tile]'));

  if (!tiles.length) return;

  let currentIndex = 0;
  let lastActiveElement = null;

  // Gather image data
  const items = tiles.map((btn, idx) => {
    btn.dataset.index = idx;
    return {
      full: btn.getAttribute('data-full-image') || btn.querySelector('img')?.src || '',
      alt: btn.querySelector('img')?.alt || 'Book Buddy gallery photo'
    };
  });

  function openLightbox(index) {
    if (index < 0 || index >= items.length) return;
    currentIndex = index;
    lastActiveElement = document.activeElement;

    updateLightbox();

    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    // Focus close button initially
    closeBtn.focus();
  }

  function closeLightbox() {
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';

    if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
      lastActiveElement.focus();
    }
  }

  function updateLightbox() {
    const item = items[currentIndex];
    if (!item) return;

    lightboxImg.src = item.full;
    lightboxImg.alt = item.alt;

    if (counterEl) {
      counterEl.textContent = `${currentIndex + 1} / ${items.length}`;
    }

    // Toggle button visibility if single item
    if (items.length <= 1) {
      if (prevBtn) prevBtn.style.display = 'none';
      if (nextBtn) nextBtn.style.display = 'none';
    } else {
      if (prevBtn) prevBtn.style.display = '';
      if (nextBtn) nextBtn.style.display = '';
    }
  }

  function showPrev() {
    currentIndex = (currentIndex - 1 + items.length) % items.length;
    updateLightbox();
  }

  function showNext() {
    currentIndex = (currentIndex + 1) % items.length;
    updateLightbox();
  }

  // Attach click handlers to tiles
  tiles.forEach((tile) => {
    tile.addEventListener('click', function (e) {
      e.preventDefault();
      const idx = parseInt(tile.dataset.index, 10);
      openLightbox(idx);
    });
  });

  // Controls
  if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
  if (prevBtn) prevBtn.addEventListener('click', showPrev);
  if (nextBtn) nextBtn.addEventListener('click', showNext);

  // Click outside image to close
  lightbox.addEventListener('click', function (e) {
    if (e.target === lightbox || e.target.classList.contains('bb-lightbox-dialog')) {
      closeLightbox();
    }
  });

  // Keyboard navigation & Focus Trap
  document.addEventListener('keydown', function (e) {
    if (!lightbox.classList.contains('is-open')) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      closeLightbox();
      return;
    }

    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      showPrev();
      return;
    }

    if (e.key === 'ArrowRight') {
      e.preventDefault();
      showNext();
      return;
    }

    // Focus Trap
    if (e.key === 'Tab') {
      const focusables = [closeBtn, prevBtn, nextBtn].filter(el => el && el.style.display !== 'none');
      if (!focusables.length) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  });

  // Touch swipe support on mobile
  let touchStartX = 0;
  let touchStartY = 0;
  let touchEndX = 0;
  let touchEndY = 0;

  lightbox.addEventListener('touchstart', function (e) {
    if (e.changedTouches.length === 1) {
      touchStartX = e.changedTouches[0].screenX;
      touchStartY = e.changedTouches[0].screenY;
    }
  }, { passive: true });

  lightbox.addEventListener('touchend', function (e) {
    if (e.changedTouches.length === 1) {
      touchEndX = e.changedTouches[0].screenX;
      touchEndY = e.changedTouches[0].screenY;
      handleSwipe();
    }
  }, { passive: true });

  function handleSwipe() {
    const diffX = touchEndX - touchStartX;
    const diffY = touchEndY - touchStartY;
    // Ensure horizontal swipe is dominant and exceeds threshold
    if (Math.abs(diffX) > 40 && Math.abs(diffX) > Math.abs(diffY)) {
      if (diffX < 0) {
        showNext();
      } else {
        showPrev();
      }
    }
  }
});

