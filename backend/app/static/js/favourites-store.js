/**
 * Book Buddy - Unified Favourites Store
 * Manages favourites state across cards, badges, and views (guest & member).
 */
(function (window, document) {
  'use strict';

  var STORAGE_KEY = 'bb_wishlist';
  var ALT_KEY = 'bb_favourites';
  var memoryStore = [];
  var isGuestUser = true;
  var csrfTokenVal = '';

  function getLocalIds() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY) || window.localStorage.getItem(ALT_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          return parsed.map(function (n) { return parseInt(n, 10); }).filter(function (n) { return !isNaN(n); });
        }
      }
    } catch (e) {}
    return memoryStore.slice();
  }

  function setLocalIds(ids) {
    var unique = [];
    (ids || []).forEach(function (id) {
      var n = parseInt(id, 10);
      if (!isNaN(n) && unique.indexOf(n) === -1) {
        unique.push(n);
      }
    });
    memoryStore = unique.slice();
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(unique));
      window.localStorage.setItem(ALT_KEY, JSON.stringify(unique));
    } catch (e) {}
    return unique;
  }

  function showToast(message, isError) {
    var toast = document.getElementById('bb-cart-toast') || document.getElementById('bb-fav-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'bb-fav-toast';
      toast.className = 'bb-cart-toast';
      toast.setAttribute('role', 'status');
      toast.setAttribute('aria-live', 'polite');
      toast.style.cssText = 'position:fixed; bottom:24px; right:24px; z-index:10000; padding:12px 20px; border-radius:8px; font-weight:600; font-size:14px; box-shadow:0 4px 16px rgba(0,0,0,0.18); transition:opacity 0.2s ease;';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.background = isError ? '#991b1b' : 'var(--navy, #0a2472)';
    toast.style.color = '#ffffff';
    toast.style.display = 'block';
    toast.style.opacity = '1';

    if (toast._timer) clearTimeout(toast._timer);
    toast._timer = setTimeout(function () {
      toast.style.opacity = '0';
      setTimeout(function () {
        toast.style.display = 'none';
      }, 200);
    }, 2500);
  }

  function dispatchFavChange(action, bookId, ids) {
    try {
      var event = new CustomEvent('bb-fav-change', {
        bubbles: true,
        detail: {
          action: action,
          id: bookId,
          ids: ids,
          count: ids.length
        }
      });
      window.dispatchEvent(event);
      document.dispatchEvent(event);
    } catch (e) {}
  }

  var FavStore = {
    _initialized: false,
    _eventsBound: false,

    init: function (options) {
      options = options || {};
      if (options.csrfToken) csrfTokenVal = options.csrfToken;
      if (typeof options.isGuest === 'boolean') isGuestUser = options.isGuest;
      else if (typeof options.isLoggedIn === 'boolean') isGuestUser = !options.isLoggedIn;

      if (!csrfTokenVal) {
        var cfg = document.getElementById('borrow-cart-config');
        if (cfg) {
          if (cfg.dataset.csrfToken) csrfTokenVal = cfg.dataset.csrfToken;
          if (cfg.dataset.isLoggedIn) isGuestUser = (cfg.dataset.isLoggedIn !== '1');
        }
      }

      this._bindEvents();
      this.hydrate();
      this.render();
      this._initialized = true;
    },

    hydrate: function () {
      var self = this;
      fetch('/api/v1/library/favourites', { credentials: 'include' })
        .then(function (res) { return res.json(); })
        .then(function (res) {
          if (!res || !res.ok || !res.data) return;
          var data = res.data;
          isGuestUser = Boolean(data.is_guest);

          if (!isGuestUser) {
            // Member logged in: DB is source of truth
            var serverIds = (data.book_ids || []).map(function (n) { return parseInt(n, 10); });
            var localIds = getLocalIds();

            var toMerge = [];
            localIds.forEach(function (id) {
              if (serverIds.indexOf(id) === -1) toMerge.push(id);
            });

            if (toMerge.length > 0) {
              fetch('/api/v1/library/favourites/sync', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-CSRF-Token': csrfTokenVal,
                  'X-CSRFToken': csrfTokenVal
                },
                credentials: 'include',
                body: JSON.stringify({ book_ids: toMerge, csrf_token: csrfTokenVal })
              })
                .then(function (sRes) { return sRes.json(); })
                .then(function (sData) {
                  if (sData && sData.ok && sData.data && sData.data.book_ids) {
                    serverIds = sData.data.book_ids.map(function (n) { return parseInt(n, 10); });
                  } else {
                    toMerge.forEach(function (id) { serverIds.push(id); });
                  }
                  setLocalIds(serverIds);
                  self.render();
                  dispatchFavChange('sync', null, serverIds);
                })
                .catch(function () {
                  setLocalIds(serverIds);
                  self.render();
                  dispatchFavChange('sync', null, serverIds);
                });
            } else {
              setLocalIds(serverIds);
              self.render();
              dispatchFavChange('sync', null, serverIds);
            }
          } else {
            // Guest: render current local IDs
            var current = getLocalIds();
            setLocalIds(current);
            self.render();
            dispatchFavChange('sync', null, current);
          }
        })
        .catch(function () {
          self.render();
        });
    },

    ids: function () {
      return getLocalIds();
    },

    count: function () {
      return getLocalIds().length;
    },

    has: function (id) {
      var n = parseInt(id, 10);
      return !isNaN(n) && getLocalIds().indexOf(n) !== -1;
    },

    add: function (id) {
      var n = parseInt(id, 10);
      if (isNaN(n)) return Promise.resolve(false);
      if (this.has(n)) return Promise.resolve(true);

      var prevIds = getLocalIds();
      var nextIds = prevIds.concat([n]);
      setLocalIds(nextIds);
      this.render();
      dispatchFavChange('add', n, nextIds);
      showToast('Added to favourites');

      var self = this;
      if (!isGuestUser) {
        return fetch('/api/v1/library/favourites', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfTokenVal,
            'X-CSRFToken': csrfTokenVal
          },
          credentials: 'include',
          body: JSON.stringify({ book_id: n, csrf_token: csrfTokenVal })
        })
          .then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
          })
          .then(function (json) {
            if (!json.ok) throw new Error((json.error && json.error.message) || 'Failed to add favourite');
            return true;
          })
          .catch(function (err) {
            // Roll back on failure
            setLocalIds(prevIds);
            self.render();
            dispatchFavChange('remove', n, prevIds);
            showToast('Failed to save favourite. Please try again.', true);
            return false;
          });
      }
      return Promise.resolve(true);
    },

    remove: function (id) {
      var n = parseInt(id, 10);
      if (isNaN(n)) return Promise.resolve(false);
      if (!this.has(n)) return Promise.resolve(true);

      var prevIds = getLocalIds();
      var nextIds = prevIds.filter(function (x) { return x !== n; });
      setLocalIds(nextIds);
      this.render();
      dispatchFavChange('remove', n, nextIds);
      showToast('Removed from favourites');

      var self = this;
      if (!isGuestUser) {
        return fetch('/api/v1/library/favourites/' + n, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfTokenVal,
            'X-CSRFToken': csrfTokenVal
          },
          credentials: 'include'
        })
          .then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
          })
          .then(function (json) {
            if (!json.ok) throw new Error((json.error && json.error.message) || 'Failed to remove favourite');
            return true;
          })
          .catch(function (err) {
            // Roll back on failure
            setLocalIds(prevIds);
            self.render();
            dispatchFavChange('add', n, prevIds);
            showToast('Failed to remove favourite. Please try again.', true);
            return false;
          });
      }
      return Promise.resolve(true);
    },

    toggle: function (id) {
      var n = parseInt(id, 10);
      if (isNaN(n)) return Promise.resolve(false);
      return this.has(n) ? this.remove(n) : this.add(n);
    },

    render: function () {
      var ids = getLocalIds();
      var count = ids.length;

      // 1. Update all heart buttons
      var buttons = document.querySelectorAll('[data-fav-toggle], .js-wishlist-btn, .js-wishlist-toggle, .bb-card-wishlist');
      buttons.forEach(function (btn) {
        var rawId = btn.dataset.bookId || btn.getAttribute('data-book-id');
        var bId = parseInt(rawId, 10);
        if (isNaN(bId)) return;
        var active = ids.indexOf(bId) !== -1;
        btn.classList.toggle('is-active', active);
        btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        btn.setAttribute('aria-label', active ? 'Remove from favourites' : 'Add to favourites');

        var svg = btn.querySelector('svg');
        if (svg) {
          if (active) {
            svg.setAttribute('fill', 'var(--maroon, #7b1230)');
            svg.setAttribute('stroke', 'var(--maroon, #7b1230)');
          } else {
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', 'currentColor');
          }
        }
      });

      // 2. Update all badge counts
      var badges = document.querySelectorAll('.js-fav-badge, #bb-filter-fav-badge, [data-fav-badge]');
      badges.forEach(function (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
      });

      // 3. Update Favourites view if present
      var favContainer = document.getElementById('bb-favs-container');
      if (favContainer) {
        var emptyEl = document.getElementById('bb-favs-empty');
        var gridEl = document.getElementById('bb-favs-grid');
        if (count === 0) {
          if (emptyEl) emptyEl.style.display = 'block';
          if (gridEl) gridEl.style.display = 'none';
        } else {
          if (emptyEl) emptyEl.style.display = 'none';
          if (gridEl) {
            gridEl.style.display = '';
            var cards = gridEl.querySelectorAll('.bb-book-card, .book-card');
            cards.forEach(function (card) {
              var cId = parseInt(card.dataset.bookId || card.getAttribute('data-book-id'), 10);
              if (!isNaN(cId) && ids.indexOf(cId) === -1) {
                card.remove();
              }
            });
            if (gridEl.querySelectorAll('.bb-book-card, .book-card').length === 0 && window.loadFavourites) {
              window.loadFavourites();
            }
          }
        }
      }
    },

    _bindEvents: function () {
      var self = this;
      if (this._eventsBound) return;
      this._eventsBound = true;

      document.addEventListener('click', function (e) {
        var favBtn = e.target.closest('[data-fav-toggle], .js-wishlist-btn, .js-wishlist-toggle');
        if (!favBtn) return;
        e.preventDefault();
        e.stopPropagation();

        var bookId = parseInt(favBtn.dataset.bookId || favBtn.getAttribute('data-book-id'), 10);
        if (bookId) {
          self.toggle(bookId);
        }
      });

      window.addEventListener('storage', function (e) {
        if (e.key === STORAGE_KEY || e.key === ALT_KEY) {
          self.render();
          dispatchFavChange('sync', null, getLocalIds());
        }
      });
    }
  };

  window.BookBuddyFavs = FavStore;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      FavStore.init();
    });
  } else {
    FavStore.init();
  }
})(window, document);

