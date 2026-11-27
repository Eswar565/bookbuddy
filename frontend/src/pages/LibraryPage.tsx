import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams, Link } from 'react-router-dom';
import {
  ShoppingBag,
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  X,
  Heart,
  Sliders,
  Plus,
  Trash2,
} from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { BookCard, Book } from '../components/books/BookCard';
import { useCart } from '../context/CartContext';
import { useToast } from '../context/ToastContext';
import { apiGet, apiPost, apiDelete } from '../api/client';

export const LibraryPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { count, openCheckout, addItem } = useCart();
  const { showToast } = useToast();

  // Search and filter state from URL params
  const q = searchParams.get('q') || '';
  const audience = searchParams.get('audience') || '';
  const language = searchParams.get('language') || searchParams.get('lang') || '';
  const category = searchParams.get('category') || '';
  const isNew = searchParams.get('new') === '1';
  const sort = searchParams.get('sort') || 'newest';
  const page = parseInt(searchParams.get('page') || '1', 10);

  const [searchInput, setSearchInput] = useState(q);
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState(false);
  const [isFavsOpen, setIsFavsOpen] = useState(false);
  const [isSortOpen, setIsSortOpen] = useState(false);
  const [isCatOpen, setIsCatOpen] = useState(false);
  const [isLangSubmenuOpen, setIsLangSubmenuOpen] = useState(false);
  const [isSortUp, setIsSortUp] = useState(false);
  const [isCatUp, setIsCatUp] = useState(false);
  const sortBtnRef = useRef<HTMLButtonElement>(null);
  const catBtnRef = useRef<HTMLButtonElement>(null);

  const toggleSort = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsCatOpen(false);
    if (!isSortOpen && sortBtnRef.current) {
      const rect = sortBtnRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;
      setIsSortUp(spaceBelow < 130 && spaceAbove > spaceBelow);
    }
    setIsSortOpen((prev) => !prev);
  };

  const toggleCat = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsSortOpen(false);
    if (!isCatOpen && catBtnRef.current) {
      const rect = catBtnRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;
      setIsCatUp(spaceBelow < 328 && spaceAbove > spaceBelow);
    }
    setIsCatOpen((prev) => !prev);
  };

  // Debounce search input sync
  useEffect(() => {
    setSearchInput(q);
  }, [q]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput.trim() !== q) {
        updateParam('q', searchInput.trim());
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Outside click & escape listener for dropdowns
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.sidebar-sort-container')) {
        setIsSortOpen(false);
      }
      if (!target.closest('.sidebar-cat-container')) {
        setIsCatOpen(false);
        setIsLangSubmenuOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsSortOpen(false);
        setIsCatOpen(false);
        setIsLangSubmenuOpen(false);
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        const activeMenu = document.querySelector('.dropdown-menu[role="menu"]');
        if (activeMenu) {
          e.preventDefault();
          const items = Array.from(activeMenu.querySelectorAll<HTMLButtonElement>('.dropdown-item:not([disabled])'));
          const curIndex = items.indexOf(document.activeElement as HTMLButtonElement);
          if (e.key === 'ArrowDown') {
            const next = curIndex < items.length - 1 ? curIndex + 1 : 0;
            items[next]?.focus();
          } else {
            const prev = curIndex > 0 ? curIndex - 1 : items.length - 1;
            items[prev]?.focus();
          }
        }
      }
    };
    document.addEventListener('click', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Local & Remote Favourites State
  const [wishlist, setWishlist] = useState<number[]>(() => {
    try {
      const stored = localStorage.getItem('bb_wishlist');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Query favourite books details for the favourites drawer
  const {
    data: favsData,
    refetch: refetchFavs,
    isLoading: isFavsLoading,
    isError: isFavsError,
  } = useQuery({
    queryKey: ['favourites', wishlist.join(',')],
    queryFn: async () => {
      const param = wishlist.length > 0 ? `?ids=${wishlist.join(',')}` : '';
      const res = await apiGet(`/api/v1/library/favourites${param}`);
      if (!res.ok) {
        throw new Error(res.error?.message || 'Failed to fetch favourites');
      }
      if (res.data) {
        if (!res.data.is_guest && res.data.book_ids) {
          const serverIds = res.data.book_ids as number[];
          setWishlist(serverIds);
          try {
            localStorage.setItem('bb_wishlist', JSON.stringify(serverIds));
          } catch {}
        }
        return res.data;
      }
      return { favourites: [], book_ids: [], count: 0, is_guest: true };
    },
  });

  // Sync localStorage favourites with server if user logs in
  useEffect(() => {
    try {
      const raw = localStorage.getItem('bb_wishlist');
      const localIds: number[] = raw ? JSON.parse(raw) : [];
      if (localIds.length > 0 && favsData && !favsData.is_guest) {
        apiPost('/api/v1/library/favourites/sync', { book_ids: localIds });
      }
    } catch {}
  }, [favsData]);

  const toggleWishlist = async (bookId: number) => {
    const isAdding = !wishlist.includes(bookId);
    const next = isAdding ? [...wishlist, bookId] : wishlist.filter((id) => id !== bookId);
    setWishlist(next);
    try {
      localStorage.setItem('bb_wishlist', JSON.stringify(next));
      localStorage.setItem('bb_favourites', JSON.stringify(next));
    } catch {}

    showToast(isAdding ? 'Added to favourites' : 'Removed from favourites', 'success');

    try {
      if (favsData && !favsData.is_guest) {
        if (isAdding) {
          const res = await apiPost('/api/v1/library/favourites', { book_id: bookId });
          if (!res.ok) throw new Error(res.error?.message || 'Failed to add favourite');
        } else {
          const res = await apiDelete(`/api/v1/library/favourites/${bookId}`);
          if (!res.ok) throw new Error(res.error?.message || 'Failed to remove favourite');
        }
      }
      refetchFavs();
    } catch {
      if (favsData && !favsData.is_guest) {
        setWishlist(wishlist);
        try {
          localStorage.setItem('bb_wishlist', JSON.stringify(wishlist));
          localStorage.setItem('bb_favourites', JSON.stringify(wishlist));
        } catch {}
        showToast('Failed to update favourites. Please try again.', 'error');
      }
    }
  };

  // Query books from /api/v1/books
  const queryString = searchParams.toString();
  const { data, isLoading } = useQuery({
    queryKey: ['books', queryString],
    queryFn: async () => {
      const res = await apiGet(`/api/v1/books?${queryString}`);
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch catalogue');
      return res.data;
    },
  });

  const books: Book[] = data?.books || [];
  const filterOptions = data?.filter_options || {};
  const totalCount = data?.total_count || 0;
  const totalPages = data?.total_pages || 1;

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
      if (key === 'lang') next.delete('language');
      if (key === 'language') next.delete('lang');
    } else {
      next.delete(key);
      if (key === 'lang') next.delete('language');
      if (key === 'language') next.delete('lang');
    }
    next.set('page', '1');
    setSearchParams(next);
  };

  const updateMultipleParams = (updates: Record<string, string>) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([k, v]) => {
      if (v) {
        next.set(k, v);
        if (k === 'lang') next.delete('language');
        if (k === 'language') next.delete('lang');
      } else {
        next.delete(k);
        if (k === 'lang') next.delete('language');
        if (k === 'language') next.delete('lang');
      }
    });
    next.set('page', '1');
    setSearchParams(next);
  };

  const hasActiveSidebarFilters = Boolean(
    q || isNew || (sort && sort !== 'newest') || (category && category.toLowerCase() !== 'all') || language
  );

  const handleClearSidebarFilters = () => {
    setSearchInput('');
    updateMultipleParams({
      q: '',
      new: '',
      sort: '',
      category: '',
      lang: '',
      language: '',
    });
  };

  const handleClearAll = () => {
    setSearchInput('');
    setSearchParams({});
  };

  const handleExport = (format: 'xlsx') => {
    const params = new URLSearchParams(searchParams);
    params.delete('page');
    window.location.href = `/api/v1/books/export/${format}?${params.toString()}`;
  };

  // Construct active filter chips
  const activeChips: { key: string; label: string }[] = [];
  if (q) activeChips.push({ key: 'q', label: `Search: "${q}"` });
  if (audience) activeChips.push({ key: 'audience', label: `Reader: ${audience === 'kids' ? 'Kids' : 'Adults'}` });
  if (isNew) activeChips.push({ key: 'new', label: 'New Arrivals' });
  if (category && category.toLowerCase() !== 'all') activeChips.push({ key: 'category', label: `Category: ${category}` });
  if (language) activeChips.push({ key: 'language', label: `Language: ${language}` });
  if (sort && sort !== 'newest') activeChips.push({ key: 'sort', label: `Sort: ${sort === 'az' ? 'A–Z' : 'Z–A'}` });


  // Favourites list for the drawer
  const favBooksList: Book[] = favsData?.favourites?.length
    ? favsData.favourites
    : books.filter((b) => wishlist.includes(b.id));

  return (
    <>
      <SEO
        title="Book Catalogue | BookBuddy Library"
        description="Browse thousands of curated children, teen, and adult books in Chennai. Add books to your borrow cart for doorstep delivery or pickup."
      />

      <div style={{ maxWidth: '1360px', margin: '0 auto', padding: '1.5rem 1.5rem 4rem' }}>
        {/* Single compact heading row */}
        <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: 0, lineHeight: 1.2 }}>
            Book Catalogue
          </h1>
          <Link
            to="/members/dashboard"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              border: '1px solid var(--border-color, #e2e8f0)',
              backgroundColor: '#ffffff',
              color: 'var(--navy, #061446)',
              fontSize: '0.85rem',
              fontWeight: 600,
              textDecoration: 'none',
            }}
          >
            My Borrowed Books &rarr;
          </Link>
        </div>

        {/* Top Filter Bar (Exact Order: Readers | Download as Excel | Language (dropdown) | Favourites | Checkout) */}
        <nav
          aria-label="Quick filters and actions"
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            padding: '12px 18px',
            border: '1px solid var(--border-color, #e2e8f0)',
            boxShadow: '0 2px 10px rgba(10, 36, 114, 0.04)',
            marginBottom: '1.5rem',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '14px',
          }}
        >
          {/* Left group: Readers and Excel Download */}
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>Readers:</span>
            {['', 'adults', 'kids'].map((aud) => (
              <button
                key={aud}
                type="button"
                onClick={() => updateParam('audience', aud)}
                style={{
                  height: '38px',
                  padding: '0 14px',
                  borderRadius: '6px',
                  border: audience === aud ? '1.5px solid var(--navy, #061446)' : '1px solid var(--border-color, #e2e8f0)',
                  backgroundColor: audience === aud ? 'var(--navy, #061446)' : '#ffffff',
                  color: audience === aud ? '#ffffff' : 'var(--navy, #061446)',
                  fontSize: '0.85rem',
                  fontWeight: audience === aud ? 700 : 500,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                }}
              >
                {aud ? (aud === 'adults' ? 'Adults' : 'Kids') : 'All'}
              </button>
            ))}

            {/* Download as Excel */}
            <button
              onClick={() => handleExport('xlsx')}
              type="button"
              title="Download currently filtered list as Excel spreadsheet"
              style={{
                height: '38px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '0 14px',
                borderRadius: '6px',
                border: '1px solid var(--border-color, #e2e8f0)',
                backgroundColor: '#ffffff',
                color: '#15803d',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <FileSpreadsheet size={16} />
              <span>Download as Excel</span>
            </button>
          </div>

          {/* Right group: Language (dropdown) | Favourites | Checkout */}
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '12px' }}>
            {/* Language dropdown */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label htmlFor="top-filter-lang" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>
                Language:
              </label>
              <select
                id="top-filter-lang"
                value={language}
                onChange={(e) => updateParam('language', e.target.value)}
                style={{
                  height: '38px',
                  padding: '0 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color, #e2e8f0)',
                  backgroundColor: '#ffffff',
                  color: 'var(--navy, #061446)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="">All Languages</option>
                {(filterOptions.languages || filterOptions.language || []).map((lang: string) => (
                  <option key={lang} value={lang}>
                    {lang}
                  </option>
                ))}
              </select>
            </div>

            {/* Favourites Button with Count Badge */}
            <button
              onClick={() => setIsFavsOpen(true)}
              type="button"
              title="View your saved favourite books"
              style={{
                height: '38px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '0 14px',
                borderRadius: '6px',
                border: '1px solid var(--border-color, #e2e8f0)',
                backgroundColor: '#ffffff',
                color: 'var(--navy, #061446)',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Heart size={16} color="var(--maroon, #7b1230)" fill={wishlist.length > 0 ? 'var(--maroon, #7b1230)' : 'none'} />
              <span>Favourites</span>
              {wishlist.length > 0 && (
                <span
                  style={{
                    backgroundColor: 'var(--maroon, #7b1230)',
                    color: '#ffffff',
                    borderRadius: '999px',
                    padding: '2px 7px',
                    fontSize: '0.725rem',
                    fontWeight: 800,
                  }}
                >
                  {wishlist.length}
                </span>
              )}
            </button>

            {/* Checkout Button */}
            <button
              onClick={openCheckout}
              type="button"
              aria-label="Open borrow cart checkout"
              style={{
                height: '38px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '0 18px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: 'var(--navy, #061446)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              <ShoppingBag size={16} />
              <span>Checkout</span>
              {count > 0 && (
                <span
                  style={{
                    backgroundColor: '#ff4757',
                    color: '#ffffff',
                    borderRadius: '999px',
                    padding: '2px 7px',
                    fontSize: '0.725rem',
                    fontWeight: 800,
                  }}
                >
                  {count}
                </span>
              )}
            </button>
          </div>
        </nav>

        {/* Mobile Filters Toggle Button */}
        <div style={{ display: 'none', marginBottom: '1.25rem' }} className="mobile-only-filter-btn">
          <button
            onClick={() => setIsMobileFilterOpen(true)}
            type="button"
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '12px',
              backgroundColor: 'var(--navy, #061446)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
            }}
          >
            <Sliders size={18} />
            <span>Filters</span>
          </button>
        </div>

        {/* Main Two-Column Layout (Sticky Sidebar + Books Grid) */}
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '28px', alignItems: 'start' }} className="catalogue-desktop-grid">
          {/* Left Sticky Sidebar */}
          <aside
            style={{
              position: 'sticky',
              top: '88px',
              alignSelf: 'start',
              maxHeight: 'calc(100vh - 104px)',
              overflow: 'visible',
              zIndex: 30,
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              padding: '16px',
              border: '1px solid var(--border-color, #e2e8f0)',
              boxShadow: '0 2px 12px rgba(10, 36, 114, 0.04)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {/* Top Heading Row: Filters title + Clear all link */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: '12px',
                borderBottom: '1px solid var(--border-color, #e2e8f0)',
                width: '100%',
                boxSizing: 'border-box',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={18} color="var(--maroon, #7b1230)" />
                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--maroon, #7b1230)', lineHeight: 1.2 }}>
                  Filters
                </h2>
              </div>
              {hasActiveSidebarFilters && (
                <button
                  type="button"
                  onClick={handleClearSidebarFilters}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: 'var(--maroon, #7b1230)',
                    cursor: 'pointer',
                  }}
                  aria-label="Clear all filters"
                >
                  Clear all
                </button>
              )}
            </div>

            {/* 1. Search Box */}
            <div style={{ position: 'relative', width: '100%' }}>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input
                  id="react-sidebar-q"
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      updateParam('q', searchInput.trim());
                    }
                  }}
                  placeholder="Search title or author..."
                  aria-label="Search books"
                  style={{
                    width: '100%',
                    height: '44px',
                    padding: '0 32px 0 12px',
                    fontSize: '13px',
                    fontFamily: 'inherit',
                    borderRadius: '8px',
                    border: '1.5px solid var(--border-color, #e2e8f0)',
                    outline: 'none',
                    boxSizing: 'border-box',
                    color: 'var(--navy, #061446)',
                  }}
                />
                {searchInput && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchInput('');
                      updateParam('q', '');
                    }}
                    aria-label="Clear search"
                    style={{
                      position: 'absolute',
                      right: '8px',
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      border: 'none',
                      backgroundColor: '#f1f5f9',
                      color: '#64748b',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    <X size={12} />
                  </button>
                )}
              </div>
            </div>

            {/* 2. New Arrivals Toggle Button */}
            <div style={{ width: '100%' }}>
              <button
                type="button"
                aria-label="New arrivals"
                aria-pressed={isNew}
                onClick={() => updateParam('new', isNew ? '' : '1')}
                style={{
                  width: '100%',
                  height: '44px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '13px',
                  fontWeight: 700,
                  fontFamily: 'inherit',
                  borderRadius: '8px',
                  border: `1.5px solid ${isNew ? 'var(--maroon, #7b1230)' : 'var(--border-color, #e2e8f0)'}`,
                  backgroundColor: isNew ? 'var(--maroon, #7b1230)' : '#ffffff',
                  color: isNew ? '#ffffff' : 'var(--navy, #061446)',
                  cursor: 'pointer',
                  boxSizing: 'border-box',
                  transition: 'all 0.15s ease',
                  textAlign: 'center',
                }}
              >
                New Arrivals
              </button>
            </div>

            {/* 3. Sort By Dropdown */}
            <div className="sidebar-sort-container" style={{ position: 'relative', width: '100%' }}>
              <button
                ref={sortBtnRef}
                type="button"
                id="sidebar-sort-btn"
                aria-label="Sort by"
                aria-haspopup="true"
                aria-expanded={isSortOpen}
                onClick={toggleSort}
                style={{
                  width: '100%',
                  height: '44px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0 12px',
                  fontSize: '13px',
                  fontWeight: 700,
                  fontFamily: 'inherit',
                  borderRadius: '8px',
                  border: '1.5px solid var(--border-color, #e2e8f0)',
                  backgroundColor: '#ffffff',
                  color: 'var(--navy, #061446)',
                  cursor: 'pointer',
                  boxSizing: 'border-box',
                }}
              >
                <span id="sidebar-sort-label">
                  Sort By: {sort === 'az' ? 'A–Z' : sort === 'za' ? 'Z–A' : 'Newest'}
                </span>
                <ChevronDown size={14} />
              </button>

              {isSortOpen && (
                <div
                  id="sidebar-sort-menu"
                  role="menu"
                  className={`dropdown-menu sidebar-menu ${isSortUp ? 'dropdown-menu--up' : ''}`}
                >
                  {[
                    { val: 'newest', label: 'Newest' },
                    { val: 'az', label: 'A–Z' },
                    { val: 'za', label: 'Z–A' },
                  ].map((item) => {
                    const isSelected = (!sort && item.val === 'newest') || sort === item.val;
                    return (
                      <button
                        key={item.val}
                        type="button"
                        role="menuitem"
                        aria-checked={isSelected}
                        className={`dropdown-item js-sort-opt ${isSelected ? 'is-selected' : ''}`}
                        onClick={() => {
                          updateParam('sort', item.val);
                          setIsSortOpen(false);
                        }}
                      >
                        <span>{item.label}</span>
                        {isSelected && (
                          <svg className="check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* 4. Categories Dropdown */}
            <div className="sidebar-cat-container" style={{ position: 'relative', width: '100%' }}>
              <button
                ref={catBtnRef}
                type="button"
                id="sidebar-cat-btn"
                aria-label="Categories"
                aria-haspopup="true"
                aria-expanded={isCatOpen}
                onClick={toggleCat}
                style={{
                  width: '100%',
                  height: '44px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0 12px',
                  fontSize: '13px',
                  fontWeight: 700,
                  fontFamily: 'inherit',
                  borderRadius: '8px',
                  border: '1.5px solid var(--border-color, #e2e8f0)',
                  backgroundColor: '#ffffff',
                  color: 'var(--navy, #061446)',
                  cursor: 'pointer',
                  boxSizing: 'border-box',
                }}
              >
                <span id="sidebar-cat-label">
                  {category && category.toLowerCase() !== 'all'
                    ? `${category}${language ? ` (${language})` : ''}`
                    : 'Categories'}
                </span>
                <ChevronDown size={14} />
              </button>

              {isCatOpen && (
                <div
                  id="sidebar-cat-menu"
                  role="menu"
                  className={`dropdown-menu sidebar-menu ${isCatUp ? 'dropdown-menu--up' : ''}`}
                >
                  {/* All Option */}
                  <button
                    type="button"
                    role="menuitem"
                    aria-checked={!category || category.toLowerCase() === 'all'}
                    className={`dropdown-item js-cat-opt ${(!category || category.toLowerCase() === 'all') ? 'is-selected' : ''}`}
                    onClick={() => {
                      updateMultipleParams({ category: '', language: '', lang: '' });
                      setIsCatOpen(false);
                    }}
                  >
                    <span>All</span>
                    {(!category || category.toLowerCase() === 'all') && (
                      <svg className="check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                    )}
                  </button>

                  {['Baby', 'Toddler', 'Junior', 'Middle Grade', 'Young Adults', 'Adults', 'Fiction', 'Non Fiction'].map((cat) => {
                    const isSelected = category.toLowerCase() === cat.toLowerCase();
                    return (
                      <button
                        key={cat}
                        type="button"
                        role="menuitem"
                        aria-checked={isSelected}
                        className={`dropdown-item js-cat-opt ${isSelected ? 'is-selected' : ''}`}
                        onClick={() => {
                          updateMultipleParams({ category: cat, language: '', lang: '' });
                          setIsCatOpen(false);
                        }}
                      >
                        <span>{cat}</span>
                        {isSelected && (
                          <svg className="check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        )}
                      </button>
                    );
                  })}

                  {/* Languages Option with Submenu */}
                  <div style={{ position: 'relative', width: '100%' }}>
                    <button
                      type="button"
                      id="sidebar-languages-trigger"
                      role="menuitem"
                      aria-haspopup="true"
                      aria-expanded={isLangSubmenuOpen}
                      aria-checked={category.toLowerCase() === 'languages' || Boolean(language)}
                      className={`dropdown-item js-lang-trigger ${(category.toLowerCase() === 'languages' || language) ? 'is-selected' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsLangSubmenuOpen((prev) => !prev);
                      }}
                    >
                      <span>Languages</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        {language && <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--maroon, #7b1230)' }}>{language}</span>}
                        <ChevronRight size={12} />
                      </div>
                    </button>

                    {isLangSubmenuOpen && (
                      <div
                        id="sidebar-languages-submenu"
                        role="menu"
                        style={{
                          paddingLeft: '10px',
                          background: 'var(--surface-body, #f8fafc)',
                          borderRadius: '6px',
                          margin: '2px 0',
                        }}
                      >
                        <button
                          type="button"
                          role="menuitem"
                          aria-checked={!language}
                          className={`dropdown-item js-sublang-opt ${!language ? 'is-selected' : ''}`}
                          onClick={() => {
                            updateMultipleParams({ category: '', language: '', lang: '' });
                            setIsCatOpen(false);
                            setIsLangSubmenuOpen(false);
                          }}
                          style={{ fontSize: '0.85rem' }}
                        >
                          <span>All Languages</span>
                          {!language && (
                            <svg className="check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                              <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                          )}
                        </button>

                        {(filterOptions.languages || filterOptions.language || ['English', 'Tamil', 'Hindi', 'French', 'German']).map((langItem: string) => {
                          const isSelected = language.toLowerCase() === langItem.toLowerCase();
                          return (
                            <button
                              key={langItem}
                              type="button"
                              role="menuitem"
                              aria-checked={isSelected}
                              className={`dropdown-item js-sublang-opt ${isSelected ? 'is-selected' : ''}`}
                              onClick={() => {
                                updateMultipleParams({ category: 'Languages', language: langItem, lang: langItem });
                                setIsCatOpen(false);
                                setIsLangSubmenuOpen(false);
                              }}
                              style={{ fontSize: '0.85rem' }}
                            >
                              <span>{langItem}</span>
                              {isSelected && (
                                <svg className="check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                  <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </aside>

          {/* Right Main Column: Active Chips + Grid + Pagination */}
          <main style={{ minWidth: 0 }}>
            {/* Active Chips Row */}
            {activeChips.length > 0 && (
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: '#ffffff',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color, #e2e8f0)',
                  marginBottom: '1.25rem',
                }}
              >
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted, #64748b)' }}>Active:</span>
                {activeChips.map((chip) => (
                  <span
                    key={chip.key}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      backgroundColor: 'rgba(6, 20, 70, 0.06)',
                      color: 'var(--navy, #061446)',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '0.775rem',
                      fontWeight: 600,
                    }}
                  >
                    <span>{chip.label}</span>
                    <button
                      type="button"
                      onClick={() => updateParam(chip.key, '')}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'var(--navy, #061446)', display: 'inline-flex' }}
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
                <button
                  type="button"
                  onClick={handleClearAll}
                  style={{ background: 'none', border: 'none', color: 'var(--maroon, #7b1230)', fontSize: '0.775rem', fontWeight: 700, cursor: 'pointer', marginLeft: 'auto' }}
                >
                  Clear All
                </button>
              </div>
            )}

            {/* Books Count */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-muted, #64748b)', fontWeight: 500 }}>
                Showing <strong>{books.length}</strong> of <strong>{totalCount}</strong> books
              </span>
            </div>

            {/* Books Grid */}
            {isLoading ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: '16px' }}>
                {[...Array(12)].map((_, idx) => (
                  <div key={idx} style={{ height: '320px', backgroundColor: '#e2e8f0', borderRadius: '12px', animation: 'pulse 1.5s infinite' }} />
                ))}
              </div>
            ) : books.length > 0 ? (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))',
                  gap: '16px',
                }}
              >
                {books.map((book) => (
                  <BookCard
                    key={book.id}
                    book={book}
                    isWishlisted={wishlist.includes(book.id)}
                    onToggleWishlist={toggleWishlist}
                  />
                ))}
              </div>
            ) : (
              <div
                style={{
                  backgroundColor: '#ffffff',
                  padding: '48px 24px',
                  textAlign: 'center',
                  borderRadius: '12px',
                  border: '1px dashed var(--border-color, #e2e8f0)',
                }}
              >
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 8px' }}>
                  {category && category.toLowerCase() !== 'all' ? 'No books found in this category' : 'No matching books found'}
                </h2>
                <p style={{ color: 'var(--text-muted, #64748b)', margin: '0 0 16px', fontSize: '0.9rem' }}>
                  {category && category.toLowerCase() !== 'all'
                    ? 'Try choosing another category or clearing your active filters to explore our shelves.'
                    : 'Try adjusting your filters or search keywords to find titles.'}
                </p>
                <button
                  type="button"
                  onClick={handleClearAll}
                  style={{
                    padding: '8px 18px',
                    borderRadius: '6px',
                    backgroundColor: 'var(--navy, #061446)',
                    color: '#ffffff',
                    border: 'none',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  Reset All Filters
                </button>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '14px', marginTop: '36px' }}>
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => updateParam('page', String(page - 1))}
                  style={{
                    height: '36px',
                    padding: '0 14px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#ffffff',
                    color: page <= 1 ? '#94a3b8' : 'var(--navy, #061446)',
                    cursor: page <= 1 ? 'not-allowed' : 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  <ChevronLeft size={16} /> Previous
                </button>

                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted, #64748b)' }}>
                  Page {page} of {totalPages}
                </span>

                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => updateParam('page', String(page + 1))}
                  style={{
                    height: '36px',
                    padding: '0 14px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#ffffff',
                    color: page >= totalPages ? '#94a3b8' : 'var(--navy, #061446)',
                    cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            )}
          </main>
        </div>

        {/* Mobile Filter Drawer (Bottom Sheet) */}
        {isMobileFilterOpen && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.5)',
              zIndex: 9998,
              display: 'flex',
              alignItems: 'flex-end',
            }}
            onClick={() => setIsMobileFilterOpen(false)}
          >
            <div
              style={{
                width: '100%',
                maxHeight: '85vh',
                overflowY: 'auto',
                backgroundColor: '#ffffff',
                borderTopLeftRadius: '20px',
                borderTopRightRadius: '20px',
                padding: '16px',
                boxShadow: '0 -10px 40px rgba(0,0,0,0.2)',
                zIndex: 9999,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingBottom: '12px',
                  borderBottom: '1px solid var(--border-color, #e2e8f0)',
                  marginBottom: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sliders size={18} color="var(--maroon, #7b1230)" />
                  <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--maroon, #7b1230)' }}>
                    Filters
                  </h3>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginLeft: 'auto' }}>
                  {hasActiveSidebarFilters && (
                    <button
                      type="button"
                      onClick={() => {
                        handleClearSidebarFilters();
                        setIsMobileFilterOpen(false);
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        padding: 0,
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        color: 'var(--maroon, #7b1230)',
                        cursor: 'pointer',
                      }}
                      aria-label="Clear all filters"
                    >
                      Clear all
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setIsMobileFilterOpen(false)}
                    style={{ background: 'none', border: 'none', padding: '4px', cursor: 'pointer', color: 'var(--navy, #061446)' }}
                    aria-label="Close filters"
                  >
                    <X size={20} />
                  </button>
                </div>
              </div>

              {/* Mobile controls list */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* 1. Search */}
                <div>
                  <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                    <input
                      id="mobile-search-q"
                      type="text"
                      value={searchInput}
                      onChange={(e) => setSearchInput(e.target.value)}
                      placeholder="Search title or author..."
                      aria-label="Search books"
                      style={{
                        width: '100%',
                        height: '44px',
                        padding: '0 32px 0 12px',
                        borderRadius: '8px',
                        border: '1.5px solid var(--border-color)',
                        fontSize: '13px',
                        boxSizing: 'border-box',
                      }}
                    />
                    {searchInput && (
                      <button
                        type="button"
                        onClick={() => {
                          setSearchInput('');
                          updateParam('q', '');
                        }}
                        aria-label="Clear search"
                        style={{
                          position: 'absolute',
                          right: '8px',
                          background: '#f1f5f9',
                          border: 'none',
                          borderRadius: '50%',
                          width: '20px',
                          height: '20px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          cursor: 'pointer',
                        }}
                      >
                        <X size={12} />
                      </button>
                    )}
                  </div>
                </div>

                {/* 2. Highlights (New Arrivals) */}
                <div>
                  <button
                    type="button"
                    aria-label="New arrivals"
                    aria-pressed={isNew}
                    onClick={() => updateParam('new', isNew ? '' : '1')}
                    style={{
                      width: '100%',
                      height: '44px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: '8px',
                      border: `1.5px solid ${isNew ? 'var(--maroon, #7b1230)' : 'var(--border-color, #e2e8f0)'}`,
                      backgroundColor: isNew ? 'var(--maroon, #7b1230)' : '#ffffff',
                      color: isNew ? '#ffffff' : 'var(--navy, #061446)',
                      fontWeight: 700,
                      fontSize: '13px',
                      cursor: 'pointer',
                      textAlign: 'center',
                    }}
                  >
                    New Arrivals
                  </button>
                </div>

                {/* 3. Ordering (Sort By) */}
                <div>
                  <select
                    value={sort}
                    onChange={(e) => updateParam('sort', e.target.value)}
                    aria-label="Sort by"
                    style={{ width: '100%', height: '44px', padding: '0 10px', borderRadius: '8px', border: '1.5px solid var(--border-color)', fontSize: '13px', backgroundColor: '#ffffff' }}
                  >
                    <option value="newest">Sort By: Newest</option>
                    <option value="az">Sort By: A–Z</option>
                    <option value="za">Sort By: Z–A</option>
                  </select>
                </div>

                {/* 4. Categories */}
                <div>
                  <select
                    value={language ? `lang:${language}` : (category || 'all')}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val.startsWith('lang:')) {
                        const chosenLang = val.replace('lang:', '');
                        updateMultipleParams({ category: 'Languages', language: chosenLang, lang: chosenLang });
                      } else if (val === 'all') {
                        updateMultipleParams({ category: '', language: '', lang: '' });
                      } else {
                        updateMultipleParams({ category: val, language: '', lang: '' });
                      }
                    }}
                    aria-label="Categories"
                    style={{ width: '100%', height: '44px', padding: '0 10px', borderRadius: '8px', border: '1.5px solid var(--border-color)', fontSize: '13px', backgroundColor: '#ffffff' }}
                  >
                    <option value="all">All Categories</option>
                    {['Baby', 'Toddler', 'Junior', 'Middle Grade', 'Young Adults', 'Adults', 'Fiction', 'Non Fiction'].map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                    <optgroup label="Languages">
                      {(filterOptions.languages || filterOptions.language || ['English', 'Tamil', 'Hindi', 'French', 'German']).map((langItem: string) => (
                        <option key={langItem} value={`lang:${langItem}`}>
                          {langItem}
                        </option>
                      ))}
                    </optgroup>
                  </select>
                </div>

                <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                  <button
                    type="button"
                    onClick={() => setIsMobileFilterOpen(false)}
                    style={{
                      flex: 1,
                      padding: '12px',
                      backgroundColor: 'var(--navy, #061446)',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '8px',
                      fontWeight: 700,
                      fontSize: '0.95rem',
                      cursor: 'pointer',
                    }}
                  >
                    Apply Filters
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      handleClearAll();
                      setIsMobileFilterOpen(false);
                    }}
                    style={{
                      padding: '12px 18px',
                      backgroundColor: '#f1f5f9',
                      color: 'var(--navy, #061446)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Reset
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Favourites Drawer / Panel */}
        {isFavsOpen && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.5)',
              zIndex: 9998,
              display: 'flex',
              justifyContent: 'flex-end',
            }}
            onClick={() => setIsFavsOpen(false)}
          >
            <div
              style={{
                width: '100%',
                maxWidth: '420px',
                height: '100%',
                backgroundColor: '#ffffff',
                boxShadow: '-4px 0 25px rgba(0,0,0,0.15)',
                display: 'flex',
                flexDirection: 'column',
                zIndex: 9999,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Drawer Header */}
              <div
                style={{
                  padding: '20px',
                  borderBottom: '1px solid var(--border-color, #e2e8f0)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Heart size={20} color="var(--maroon, #7b1230)" fill="var(--maroon, #7b1230)" />
                  <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy, #061446)' }}>
                    My Favourites ({wishlist.length})
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setIsFavsOpen(false)}
                  style={{ background: 'none', border: 'none', padding: '4px', cursor: 'pointer', color: '#64748b' }}
                >
                  <X size={20} />
                </button>
              </div>

              {/* Guest Banner */}
              {favsData?.is_guest && (
                <div
                  style={{
                    backgroundColor: '#fef3c7',
                    borderBottom: '1px solid #fde68a',
                    color: '#92400e',
                    padding: '10px 16px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '8px',
                  }}
                >
                  <span>Log in to save your favourites to your account</span>
                  <Link
                    to="/login"
                    style={{
                      backgroundColor: '#92400e',
                      color: '#ffffff',
                      padding: '4px 10px',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      textDecoration: 'none',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    Log In
                  </Link>
                </div>
              )}

              {/* Drawer Book List */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
                {isFavsError ? (
                  <div style={{ textAlign: 'center', padding: '32px 16px', color: '#991b1b', backgroundColor: '#fef2f2', borderRadius: '8px' }}>
                    <p style={{ margin: '0 0 10px', fontSize: '0.875rem', fontWeight: 600 }}>
                      Something went wrong loading your favourites.
                    </p>
                    <button
                      type="button"
                      onClick={() => refetchFavs()}
                      style={{
                        padding: '6px 14px',
                        backgroundColor: '#991b1b',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      Retry
                    </button>
                  </div>
                ) : isFavsLoading ? (
                  <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-muted, #64748b)' }}>
                    Loading favourites...
                  </div>
                ) : favBooksList.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    {favBooksList.map((b) => {
                      const isAvail = (b.available_copies ?? b.stock ?? 1) > 0;
                      return (
                        <div
                          key={b.id}
                          style={{
                            display: 'flex',
                            gap: '12px',
                            padding: '10px',
                            borderRadius: '8px',
                            border: '1px solid var(--border-color, #e2e8f0)',
                            backgroundColor: '#f8fafc',
                            alignItems: 'center',
                          }}
                        >
                          <img
                            src={b.image_url || b.image_path || '/static/img/placeholder-book.png'}
                            alt={b.title}
                            style={{ width: '48px', height: '64px', objectFit: 'cover', borderRadius: '4px', backgroundColor: '#e2e8f0' }}
                            onError={(e) => {
                              (e.target as HTMLElement).style.display = 'none';
                            }}
                          />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <h4
                              style={{
                                margin: '0 0 2px',
                                fontSize: '0.875rem',
                                fontWeight: 700,
                                color: 'var(--navy, #061446)',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                              }}
                            >
                              {b.title}
                            </h4>
                            <p
                              style={{
                                margin: '0 0 4px',
                                fontSize: '0.775rem',
                                color: 'var(--maroon, #7b1230)',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                              }}
                            >
                              {b.author || 'Author not listed'}
                            </p>
                            <div style={{ marginBottom: '6px' }}>
                              <span
                                style={{
                                  display: 'inline-block',
                                  fontSize: '0.7rem',
                                  fontWeight: 700,
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  backgroundColor: isAvail ? 'var(--color-secondary, #15803d)' : '#6b7280',
                                  color: '#ffffff',
                                }}
                              >
                                {isAvail ? `Available: ${b.available_copies ?? b.stock ?? 1}` : 'Unavailable'}
                              </span>
                            </div>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                              <button
                                type="button"
                                disabled={!isAvail}
                                onClick={() => {
                                  addItem({ id: b.id, title: b.title, author: b.author || 'Author not listed' });
                                }}
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  backgroundColor: isAvail ? 'var(--navy, #061446)' : '#94a3b8',
                                  color: '#ffffff',
                                  border: 'none',
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                  cursor: isAvail ? 'pointer' : 'not-allowed',
                                }}
                              >
                                <Plus size={12} /> Add
                              </button>
                              <button
                                type="button"
                                onClick={() => toggleWishlist(b.id)}
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                  padding: '4px 6px',
                                  borderRadius: '4px',
                                  backgroundColor: 'transparent',
                                  color: '#ef4444',
                                  border: 'none',
                                  fontSize: '0.75rem',
                                  cursor: 'pointer',
                                }}
                              >
                                <Trash2 size={13} /> Remove
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--text-muted, #64748b)' }}>
                    <Heart size={40} color="#cbd5e1" style={{ marginBottom: '12px' }} />
                    <p style={{ margin: '0 0 8px', fontWeight: 700, color: 'var(--navy, #061446)' }}>
                      No favourites yet. Tap the heart on a book to save it.
                    </p>
                    <p style={{ margin: 0, fontSize: '0.85rem' }}>
                      Click the heart button on any book card to save it to your reading list.
                    </p>
                  </div>
                )}
              </div>

              {/* Drawer Footer */}
              <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-color, #e2e8f0)', display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => {
                    setIsFavsOpen(false);
                    openCheckout();
                  }}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--navy, #061446)',
                    color: '#ffffff',
                    border: 'none',
                    fontWeight: 700,
                    fontSize: '0.9rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  <ShoppingBag size={16} /> Open Checkout
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @media (max-width: 1023px) {
          .catalogue-desktop-grid {
            grid-template-columns: 1fr !important;
          }
          .catalogue-desktop-grid aside {
            display: none !important;
          }
          .mobile-only-filter-btn {
            display: block !important;
          }
        }
      `}</style>
    </>
  );
};
