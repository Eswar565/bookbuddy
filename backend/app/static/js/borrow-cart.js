/**
 * BookBuddy Borrow Cart & Checkout Controller
 *
 * Provides a unified cart state (localStorage key: 'bb_cart' with in-memory fallback),
 * event delegation on document, cross-tab synchronization, and unified UI rendering.
 */
(function () {
  'use strict';

  var CART_KEY = 'bb_cart';
  var WISHLIST_KEY = 'bb_wishlist';
  var memoryCart = [];
  var memoryWishlist = [];
  var toastTimeout = null;

  // Safe localStorage detector
  var hasLocalStorage = (function () {
    try {
      var testKey = '__bb_test__';
      window.localStorage.setItem(testKey, testKey);
      window.localStorage.removeItem(testKey);
      return true;
    } catch (e) {
      return false;
    }
  })();

  // 1. Shared Cart State Module (window.BookBuddyCart)
  var BookBuddyCart = {
    items: function () {
      if (hasLocalStorage) {
        try {
          var raw = window.localStorage.getItem(CART_KEY);
          var parsed = raw ? JSON.parse(raw) : [];
          return Array.isArray(parsed) ? parsed : [];
        } catch (e) {
          return memoryCart.slice();
        }
      }
      return memoryCart.slice();
    },

    count: function () {
      return this.items().length;
    },

    has: function (bookId) {
      var id = parseInt(bookId, 10);
      return this.items().some(function (item) {
        return item.id === id;
      });
    },

    add: function (book) {
      if (!book || typeof book.id === 'undefined') return;
      var id = parseInt(book.id, 10);
      var current = this.items();
      if (!this.has(id)) {
        current.push({
          id: id,
          title: String(book.title || 'Untitled'),
          author: String(book.author || 'Author not listed'),
          available: typeof book.available !== 'undefined' ? parseInt(book.available, 10) : 1
        });
        this._save(current);
      }
    },

    remove: function (bookId) {
      var id = parseInt(bookId, 10);
      var current = this.items().filter(function (item) {
        return item.id !== id;
      });
      this._save(current);
    },

    clear: function () {
      this._save([]);
    },

    _save: function (items) {
      memoryCart = items.slice();
      if (hasLocalStorage) {
        try {
          window.localStorage.setItem(CART_KEY, JSON.stringify(items));
        } catch (e) {
          // In-memory fallback retained
        }
      }
      document.dispatchEvent(new CustomEvent('bb-cart-change', {
        detail: { items: items, count: items.length }
      }));
    }
  };

  // Expose module globally
  window.BookBuddyCart = BookBuddyCart;

  // 2. Safe Wishlist Access
  function getWishlist() {
    if (hasLocalStorage) {
      try {
        var raw = window.localStorage.getItem(WISHLIST_KEY);
        var parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
      } catch (e) {
        return memoryWishlist.slice();
      }
    }
    return memoryWishlist.slice();
  }

  function saveWishlist(list) {
    memoryWishlist = list.slice();
    if (hasLocalStorage) {
      try {
        window.localStorage.setItem(WISHLIST_KEY, JSON.stringify(list));
      } catch (e) {}
    }
    updateWishlistUI();
  }

  function toggleWishlist(bookId) {
    var id = parseInt(bookId, 10);
    if (isNaN(id)) return;
    var list = getWishlist();
    var idx = list.indexOf(id);
    var willAdd = (idx === -1);
    if (willAdd) {
      list.push(id);
    } else {
      list.splice(idx, 1);
    }
    saveWishlist(list);

    // Sync with backend if logged in
    var token = (config && config.csrfToken) || '';
    if (willAdd) {
      fetch('/api/v1/library/favourites/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': token,
          'X-CSRF-Token': token
        },
        credentials: 'include',
        body: JSON.stringify({ book_id: id, csrf_token: token })
      }).catch(function() {});
    } else {
      fetch('/api/v1/library/favourites/' + id + '/', {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': token,
          'X-CSRF-Token': token
        },
        credentials: 'include'
      }).catch(function() {});
    }
  }

  function updateWishlistUI() {
    var list = getWishlist();
    var buttons = document.querySelectorAll('.js-wishlist-btn');
    buttons.forEach(function (btn) {
      var id = parseInt(btn.dataset.bookId, 10);
      var active = list.indexOf(id) !== -1;
      var svg = btn.querySelector('svg');
      if (active) {
        btn.classList.add('is-active');
        btn.setAttribute('aria-pressed', 'true');
        btn.setAttribute('aria-label', 'Remove from favourites');
        if (svg) {
          svg.setAttribute('fill', 'var(--maroon, #7b1230)');
          svg.setAttribute('stroke', 'var(--maroon, #7b1230)');
        }
      } else {
        btn.classList.remove('is-active');
        btn.setAttribute('aria-pressed', 'false');
        btn.setAttribute('aria-label', 'Add to favourites');
        if (svg) {
          svg.setAttribute('fill', 'none');
          svg.setAttribute('stroke', 'currentColor');
        }
      }
    });

    // Update favourites badges
    var badges = document.querySelectorAll('.js-fav-badge, #bb-filter-fav-badge');
    badges.forEach(function(badge) {
      badge.textContent = list.length;
      badge.style.display = list.length > 0 ? 'inline-block' : 'none';
    });
  }

  function syncWishlistFromServer() {
    fetch('/api/v1/library/favourites/', { credentials: 'include' })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (!data || !data.ok || !data.data) return;
        var serverIds = data.data.book_ids || [];
        var localList = getWishlist();
        if (data.data.is_guest) {
          updateWishlistUI();
        } else {
          var toMerge = [];
          localList.forEach(function(id) {
            if (serverIds.indexOf(id) === -1) toMerge.push(id);
          });
          if (toMerge.length > 0) {
            var token = (config && config.csrfToken) || '';
            fetch('/api/v1/library/favourites/sync/', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token,
                'X-CSRF-Token': token
              },
              credentials: 'include',
              body: JSON.stringify({ book_ids: toMerge, csrf_token: token })
            }).then(function() {
              var merged = [];
              serverIds.concat(localList).forEach(function(x) {
                if (merged.indexOf(x) === -1) merged.push(x);
              });
              saveWishlist(merged);
            }).catch(function() {
              saveWishlist(serverIds);
            });
          } else {
            saveWishlist(serverIds);
          }
        }
      })
      .catch(function() {
        updateWishlistUI();
      });
  }

  // Helper: HTML escaping
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // 3. UI Helpers
  function showToast(message) {
    var toast = document.getElementById('bb-cart-toast');
    if (!toast) return;
    toast.textContent = message;
    toast.style.display = 'block';
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(function () {
      toast.style.display = 'none';
    }, 3500);
  }

  function triggerBadgeBump() {
    var badges = document.querySelectorAll('.js-cart-badge, .bb-cart-badge');
    badges.forEach(function (b) {
      b.classList.remove('bb-badge-bump');
      void b.offsetWidth;
      b.classList.add('bb-badge-bump');
    });
  }

  // Configuration from DOM
  function getConfig() {
    var cfgEl = document.getElementById('borrow-cart-config');
    return {
      isLoggedIn: cfgEl && cfgEl.dataset.isLoggedIn === '1',
      hasPlan: cfgEl && cfgEl.dataset.hasPlan === '1',
      planName: cfgEl ? (cfgEl.dataset.planName || '') : '',
      planLimit: cfgEl ? parseInt(cfgEl.dataset.planLimit, 10) || 2 : 2,
      activeLoans: cfgEl ? parseInt(cfgEl.dataset.activeLoans, 10) || 0 : 0,
      remainingSlots: cfgEl ? parseInt(cfgEl.dataset.remainingSlots, 10) || 0 : 0,
      csrfToken: cfgEl ? (cfgEl.dataset.csrfToken || '') : '',
      pickupAddr: cfgEl ? (cfgEl.dataset.pickupAddr || '') : '',
      deliveryArea: cfgEl ? (cfgEl.dataset.deliveryArea || '') : ''
    };
  }

  function checkFloatingCheckoutVisibility() {
    var filterBtn = document.getElementById('bb-filter-checkout-btn');
    var floatBtn = document.getElementById('bb-floating-checkout');
    if (!floatBtn) return;
    var cart = BookBuddyCart.items();
    if (cart.length === 0 || window.innerWidth > 768) {
      floatBtn.style.display = 'none';
      return;
    }
    if (filterBtn) {
      var rect = filterBtn.getBoundingClientRect();
      floatBtn.style.display = rect.bottom < 0 ? 'block' : 'none';
    } else {
      floatBtn.style.display = 'block';
    }
  }

  // 4. Unified render() Function
  function render() {
    var cart = BookBuddyCart.items();
    var count = cart.length;
    var config = getConfig();

    // (a) Update Checkout badges
    var filterBadge = document.getElementById('bb-filter-cart-badge');
    var floatBadge = document.getElementById('bb-floating-cart-badge');
    if (filterBadge) {
      filterBadge.textContent = count;
      filterBadge.style.display = count > 0 ? 'inline-flex' : 'none';
    }
    if (floatBadge) {
      floatBadge.textContent = count;
    }

    // (b) Update book card buttons
    var cardButtons = document.querySelectorAll('[data-add-to-cart], .js-cart-btn');
    cardButtons.forEach(function (btn) {
      var id = parseInt(btn.dataset.bookId, 10);
      var inCart = BookBuddyCart.has(id);
      var labelEl = btn.querySelector('.cart-btn-label');
      var checkIcon = btn.querySelector('.cart-check-icon');

      if (inCart) {
        btn.classList.add('is-in-cart');
        btn.setAttribute('aria-pressed', 'true');
        if (checkIcon) checkIcon.style.display = 'inline-block';
        if (labelEl) labelEl.textContent = 'Added';
      } else {
        btn.classList.remove('is-in-cart');
        btn.setAttribute('aria-pressed', 'false');
        if (checkIcon) checkIcon.style.display = 'none';
        if (labelEl) labelEl.textContent = 'Add';
      }
    });

    // (c) Re-render modal items list
    var itemsListEl = document.getElementById('bb-modal-items-list');
    var itemsCountEl = document.getElementById('bb-items-count');
    var submitBtn = document.getElementById('bb-modal-submit-btn');
    var limitErrorEl = document.getElementById('bb-limit-error');

    if (itemsCountEl) itemsCountEl.textContent = count;

    if (itemsListEl) {
      if (count === 0) {
        itemsListEl.innerHTML = '<p style="color:var(--text-muted); font-size:13px; margin:8px 0; text-align:center;">No books selected yet. Add books from the catalogue.</p>';
        if (submitBtn) submitBtn.disabled = true;
        if (limitErrorEl) limitErrorEl.style.display = 'none';
      } else {
        var html = '';
        cart.forEach(function (item) {
          html += '<div class="bb-modal-item">' +
            '<div class="bb-modal-item-title">' + escapeHtml(item.title) + '</div>' +
            '<button type="button" class="bb-modal-item-remove js-remove-modal-item" data-remove-id="' + item.id + '" data-remove-from-cart="' + item.id + '" aria-label="Remove ' + escapeHtml(item.title) + '">&times;</button>' +
          '</div>';
        });
        itemsListEl.innerHTML = html;

        // Plan limits validation
        if (config.isLoggedIn && config.hasPlan) {
          if (count > config.remainingSlots) {
            if (limitErrorEl) {
              limitErrorEl.textContent = 'You have selected ' + count + ' book(s), but only ' + config.remainingSlots + ' remaining slot(s) are available.';
              limitErrorEl.style.display = 'block';
            }
            if (submitBtn) submitBtn.disabled = true;
          } else {
            if (limitErrorEl) limitErrorEl.style.display = 'none';
            if (submitBtn) submitBtn.disabled = false;
          }
        } else if (!config.isLoggedIn) {
          if (submitBtn) submitBtn.disabled = true;
        } else {
          if (submitBtn) submitBtn.disabled = false;
        }
      }
    }

    // (d) Update floating checkout visibility
    checkFloatingCheckoutVisibility();
  }

  // 5. Modal Controllers
  var modal = null;
  var lastFocusedEl = null;

  function openModal() {
    modal = document.getElementById('bb-checkout-modal');
    if (!modal) return;
    lastFocusedEl = document.activeElement;
    render();
    var submitErrorEl = document.getElementById('bb-modal-submit-error');
    if (submitErrorEl) submitErrorEl.style.display = 'none';

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    var focusable = modal.querySelectorAll('input:not([disabled]):not([readonly]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])');
    if (focusable.length > 0) {
      focusable[0].focus();
    } else {
      var dialog = document.getElementById('bb-modal-dialog');
      if (dialog) dialog.focus();
    }
  }

  function closeModal() {
    modal = document.getElementById('bb-checkout-modal');
    if (!modal) return;
    modal.style.display = 'none';
    document.body.style.overflow = '';
    if (lastFocusedEl && typeof lastFocusedEl.focus === 'function') {
      lastFocusedEl.focus();
    }
  }

  // 6. Global Event Delegation on document
  document.addEventListener('click', function (e) {
    // A. Card Add/Added button delegation
    var addBtn = e.target.closest('[data-add-to-cart], .js-cart-btn');
    if (addBtn) {
      e.preventDefault();
      e.stopPropagation();

      var bookId = parseInt(addBtn.dataset.bookId, 10);
      var bookTitle = addBtn.dataset.title || addBtn.dataset.bookTitle || '';
      var bookAuthor = addBtn.dataset.author || addBtn.dataset.bookAuthor || '';
      var available = typeof addBtn.dataset.available !== 'undefined' ? parseInt(addBtn.dataset.available, 10) : 1;

      if (available < 1) {
        showToast('This book is currently unavailable.');
        return;
      }

      var config = getConfig();

      if (BookBuddyCart.has(bookId)) {
        BookBuddyCart.remove(bookId);
        showToast('Removed from checkout');
        triggerBadgeBump();
      } else {
        // Enforce plan limits
        if (config.isLoggedIn && config.hasPlan) {
          if (BookBuddyCart.count() >= config.remainingSlots) {
            showToast('Your plan allows ' + config.planLimit + ' books at a time. Remaining slots: ' + config.remainingSlots + '.');
            return;
          }
        } else if (!config.isLoggedIn) {
          if (BookBuddyCart.count() >= 4) {
            showToast('You have selected 4 titles. Log in to check out.');
            return;
          }
        }

        BookBuddyCart.add({
          id: bookId,
          title: bookTitle,
          author: bookAuthor,
          available: available
        });
        showToast('Added to checkout');
        triggerBadgeBump();
      }
      return;
    }

    // B. Modal item remove button delegation
    var removeBtn = e.target.closest('.js-remove-modal-item, [data-remove-from-cart]');
    if (removeBtn) {
      e.preventDefault();
      e.stopPropagation();
      var removeId = parseInt(removeBtn.dataset.removeId || removeBtn.dataset.removeFromCart, 10);
      BookBuddyCart.remove(removeId);
      showToast('Removed from checkout');
      triggerBadgeBump();
      return;
    }

    // C. Wishlist heart toggle delegation
    var wishBtn = e.target.closest('.js-wishlist-btn');
    if (wishBtn) {
      e.preventDefault();
      e.stopPropagation();
      var wishId = parseInt(wishBtn.dataset.bookId, 10);
      toggleWishlist(wishId);
      return;
    }

    // D. Checkout trigger buttons
    var triggerBtn = e.target.closest('.js-checkout-trigger, #bb-filter-checkout-btn, #bb-checkout-trigger');
    if (triggerBtn) {
      e.preventDefault();
      openModal();
      return;
    }

    // E. Modal close / cancel / backdrop clicks
    if (e.target.closest('#bb-modal-close-btn, #bb-modal-cancel-btn, #bb-modal-backdrop')) {
      e.preventDefault();
      closeModal();
      return;
    }
  });

  // 7. Modal Keyboard Accessibility (Escape to close, Tab trap)
  document.addEventListener('keydown', function (e) {
    var activeModal = document.getElementById('bb-checkout-modal');
    if (!activeModal || activeModal.style.display === 'none') return;

    if (e.key === 'Escape') {
      closeModal();
      return;
    }

    if (e.key === 'Tab') {
      var focusable = activeModal.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])');
      if (focusable.length === 0) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          last.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === last) {
          first.focus();
          e.preventDefault();
        }
      }
    }
  });

  // 8. Delivery Mode Change Handling
  document.addEventListener('change', function (e) {
    if (e.target && e.target.id === 'req-delivery-mode') {
      var mode = e.target.value;
      var deliveryGroup = document.getElementById('delivery-address-group');
      var deliveryAddressInput = document.getElementById('req-address');
      var deliveryHint = document.getElementById('delivery-mode-hint');
      var config = getConfig();

      if (mode === 'online') {
        if (deliveryGroup) deliveryGroup.style.display = 'block';
        if (deliveryAddressInput) deliveryAddressInput.required = true;
        if (deliveryHint) deliveryHint.textContent = 'Doorstep drop & collect (' + config.deliveryArea + ')';
      } else {
        if (deliveryGroup) deliveryGroup.style.display = 'none';
        if (deliveryAddressInput) deliveryAddressInput.required = false;
        if (deliveryHint) deliveryHint.textContent = 'Self-pickup at ' + config.pickupAddr;
      }
    }
  });

  // 9. Checkout Form Submission
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (form && form.id === 'bb-checkout-form') {
      e.preventDefault();
      var cart = BookBuddyCart.items();
      if (cart.length === 0) {
        showToast('Please add books to your cart first.');
        return;
      }

      var submitBtn = document.getElementById('bb-modal-submit-btn');
      var submitErrorEl = document.getElementById('bb-modal-submit-error');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting request...';
      }
      if (submitErrorEl) submitErrorEl.style.display = 'none';

      var config = getConfig();
      var formData = new FormData(form);
      var payload = {
        book_ids: cart.map(function (item) { return item.id; }),
        name: formData.get('name') || '',
        phone: formData.get('phone') || '',
        delivery_mode: formData.get('delivery_mode') || 'offline',
        address: formData.get('address') || '',
        csrf_token: config.csrfToken
      };

      fetch('/library/checkout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': config.csrfToken
        },
        body: JSON.stringify(payload)
      })
      .then(function (res) {
        return res.json().then(function (data) {
          return { status: res.status, data: data };
        });
      })
      .then(function (result) {
        if (result.data && result.data.ok) {
          BookBuddyCart.clear();
          closeModal();

          // Disable buttons for these books
          payload.book_ids.forEach(function (id) {
            var btn = document.querySelector('[data-add-to-cart][data-book-id="' + id + '"], .js-cart-btn[data-book-id="' + id + '"]');
            if (btn) {
              btn.disabled = true;
              btn.classList.add('btn-cart-disabled');
              btn.classList.remove('is-in-cart', 'js-cart-btn');
              var lbl = btn.querySelector('.cart-btn-label');
              if (lbl) lbl.textContent = 'Active Request';
            }
          });

          showToast(result.data.message || 'Request submitted successfully!');
          setTimeout(function () {
            window.location.href = '/members/dashboard/';
          }, 1800);
        } else {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Confirm Request';
          }
          var errList = (result.data && result.data.errors) ? result.data.errors.join(' ') : 'Unable to submit your request. Please review your details and try again.';
          if (submitErrorEl) {
            submitErrorEl.textContent = errList;
            submitErrorEl.style.display = 'block';
          } else {
            showToast(errList);
          }
        }
      })
      .catch(function () {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Confirm Request';
        }
        if (submitErrorEl) {
          submitErrorEl.textContent = 'Connection error. Please try again.';
          submitErrorEl.style.display = 'block';
        } else {
          showToast('Connection error. Please try again.');
        }
      });
    }
  });

  // 10. Listen to Cart Changes & Storage Events
  document.addEventListener('bb-cart-change', function () {
    render();
  });

  window.addEventListener('storage', function (e) {
    if (e.key === CART_KEY) {
      render();
    } else if (e.key === WISHLIST_KEY) {
      updateWishlistUI();
    }
  });

  window.addEventListener('scroll', checkFloatingCheckoutVisibility, { passive: true });
  window.addEventListener('resize', checkFloatingCheckoutVisibility, { passive: true });

  // 11. Initial execution
  document.addEventListener('DOMContentLoaded', function () {
    render();
    updateWishlistUI();
    syncWishlistFromServer();

    // Mobile filter drawer toggle
    var toggleBtn = document.getElementById('filter-drawer-toggle');
    var sidebar = document.getElementById('catalogue-sidebar');
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener('click', function () {
        var isOpen = sidebar.classList.toggle('is-open');
        toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });
    }
  });

  if (document.readyState !== 'loading') {
    render();
    updateWishlistUI();
    syncWishlistFromServer();
  }
})();
