import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams, Link } from 'react-router-dom';
import {
  ShoppingBag,
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight,
  X,
  Heart,
  Sliders,
  Trash2,
  Plus,
} from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { BookCard, Book } from '../components/books/BookCard';
import { useCart } from '../context/CartContext';
import { apiGet, apiPost, apiDelete } from '../api/client';

export const LibraryPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { count, openCheckout, addItem } = useCart();

  // Search and filter state from URL params
  const q = searchParams.get('q') || '';
  const audience = searchParams.get('audience') || '';
  const language = searchParams.get('language') || '';
  const collection = searchParams.get('collection') || '';
  const age_group = searchParams.get('age_group') || '';
  const author = searchParams.get('author') || '';
  const availability = searchParams.get('availability') || '';
  const sort = searchParams.get('sort') || 'newest';
  const page = parseInt(searchParams.get('page') || '1', 10);

  const [searchInput, setSearchInput] = useState(q);
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState(false);
  const [isFavsOpen, setIsFavsOpen] = useState(false);

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
  const { data: favsData, refetch: refetchFavs } = useQuery({
    queryKey: ['favourites'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/library/favourites');
      if (res.ok && res.data) {
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
    } catch {}

    try {
      if (isAdding) {
        await apiPost('/api/v1/library/favourites', { book_id: bookId });
      } else {
        await apiDelete(`/api/v1/library/favourites/${bookId}`);
      }
      refetchFavs();
    } catch {
      // Local state fallback preserved
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
    } else {
      next.delete(key);
    }
    next.set('page', '1');
    setSearchParams(next);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateParam('q', searchInput.trim());
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
  if (age_group) activeChips.push({ key: 'age_group', label: `Age: ${age_group} yrs` });
  if (language) activeChips.push({ key: 'language', label: `Language: ${language}` });
  if (collection) activeChips.push({ key: 'collection', label: `Category: ${collection}` });
  if (author) activeChips.push({ key: 'author', label: `Author: ${author}` });
  if (availability) activeChips.push({ key: 'availability', label: availability === 'available' ? 'Available Now' : 'Waitlist' });

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
                {filterOptions.language?.map((lang: string) => (
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
            <span>Filter &amp; Sort Catalogue</span>
          </button>
        </div>

        {/* Main Two-Column Layout (Sticky Sidebar + Books Grid) */}
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '28px', alignItems: 'start' }} className="catalogue-desktop-grid">
          {/* Left Sticky Sidebar */}
          <aside
            style={{
              position: 'sticky',
              top: '88px',
              maxHeight: 'calc(100vh - 104px)',
              overflowY: 'auto',
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              padding: '20px',
              border: '1px solid var(--border-color, #e2e8f0)',
              boxShadow: '0 2px 12px rgba(10, 36, 114, 0.04)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--navy, #061446)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sliders size={16} /> Refine Catalogue
              </h3>
              <button
                type="button"
                onClick={handleClearAll}
                style={{ background: 'none', border: 'none', color: 'var(--maroon, #7b1230)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Clear All
              </button>
            </div>

            <form onSubmit={handleSearchSubmit}>
              {/* 1. Search */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main, #1e293b)', marginBottom: '4px' }}>
                  Search
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="search"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Title, author, keyword..."
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      fontSize: '0.85rem',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color, #e2e8f0)',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              </div>

              {/* 2. Reader Type */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main, #1e293b)', marginBottom: '4px' }}>
                  Reader Type
                </label>
                <select
                  value={audience}
                  onChange={(e) => updateParam('audience', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    fontSize: '0.85rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#fff',
                    boxSizing: 'border-box',
                  }}
                >
                  <option value="">All Readers</option>
                  <option value="adults">Adults &amp; Parents</option>
                  <option value="kids">Children &amp; Young Readers</option>
                </select>
              </div>

              {/* 3. Age Group */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main, #1e293b)', marginBottom: '4px' }}>
                  Age Group
                </label>
                <select
                  value={age_group}
                  onChange={(e) => updateParam('age_group', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    fontSize: '0.85rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#fff',
                    boxSizing: 'border-box',
                  }}
                >
                  <option value="">All Age Groups</option>
                  {filterOptions.age_group?.map((age: string) => (
                    <option key={age} value={age}>
                      {age} yrs
                    </option>
                  ))}
                </select>
              </div>

              {/* 4. Genre / Category */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main, #1e293b)', marginBottom: '4px' }}>
                  Genre / Category
                </label>
                <select
                  value={collection}
                  onChange={(e) => updateParam('collection', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    fontSize: '0.85rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#fff',
                    boxSizing: 'border-box',
                  }}
                >
                  <option value="">All Categories</option>
                  {filterOptions.collections?.map((col: string) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </div>

              {/* 5. Author */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main, #1e293b)', marginBottom: '4px' }}>
                  Author
                </label>
                <select
                  value={author}
                  onChange={(e) => updateParam('author', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    fontSize: '0.85rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#fff',
                    boxSizing: 'border-box',
                  }}
                >
                  <option value="">All Authors</option>
                  {filterOptions.author?.map((auth: string) => (
                    <option key={auth} value={auth}>
                      {auth}
                    </option>
                  ))}
                </select>
              </div>

              {/* 6. Availability */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main, #1e293b)', marginBottom: '4px' }}>
                  Availability
                </label>
                <select
                  value={availability}
                  onChange={(e) => updateParam('availability', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    fontSize: '0.85rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#fff',
                    boxSizing: 'border-box',
                  }}
                >
                  <option value="">All Collection</option>
                  <option value="available">Available Now</option>
                  <option value="waitlist">On Loan / Waitlist</option>
                </select>
              </div>

              {/* 7. Sort By */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main, #1e293b)', marginBottom: '4px' }}>
                  Sort By
                </label>
                <select
                  value={sort}
                  onChange={(e) => updateParam('sort', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    fontSize: '0.85rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#fff',
                    boxSizing: 'border-box',
                  }}
                >
                  <option value="newest">Newest Arrivals</option>
                  <option value="title">Title (A–Z)</option>
                  <option value="author">Author (A–Z)</option>
                </select>
              </div>

              {/* 8. Clear & Apply */}
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="submit"
                  style={{
                    flex: 1,
                    padding: '10px',
                    backgroundColor: 'var(--navy, #061446)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Apply
                </button>
                <button
                  type="button"
                  onClick={handleClearAll}
                  style={{
                    padding: '10px 14px',
                    backgroundColor: '#f1f5f9',
                    color: 'var(--navy, #061446)',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Clear
                </button>
              </div>
            </form>
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
                  No matching books found
                </h2>
                <p style={{ color: 'var(--text-muted, #64748b)', margin: '0 0 16px', fontSize: '0.9rem' }}>
                  Try adjusting your filters or search keywords to find titles.
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
                padding: '24px 20px',
                boxShadow: '0 -10px 40px rgba(0,0,0,0.2)',
                zIndex: 9999,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>
                  Filters &amp; Sort
                </h3>
                <button
                  type="button"
                  onClick={() => setIsMobileFilterOpen(false)}
                  style={{ background: 'none', border: 'none', padding: '4px', cursor: 'pointer' }}
                >
                  <X size={20} />
                </button>
              </div>

              {/* Mobile controls list */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                    Reader Type
                  </label>
                  <select
                    value={audience}
                    onChange={(e) => updateParam('audience', e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  >
                    <option value="">All Readers</option>
                    <option value="adults">Adults &amp; Parents</option>
                    <option value="kids">Children &amp; Young Readers</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                    Age Group
                  </label>
                  <select
                    value={age_group}
                    onChange={(e) => updateParam('age_group', e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  >
                    <option value="">All Age Groups</option>
                    {filterOptions.age_group?.map((age: string) => (
                      <option key={age} value={age}>
                        {age} yrs
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                    Genre / Category
                  </label>
                  <select
                    value={collection}
                    onChange={(e) => updateParam('collection', e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  >
                    <option value="">All Categories</option>
                    {filterOptions.collections?.map((col: string) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                    Sort By
                  </label>
                  <select
                    value={sort}
                    onChange={(e) => updateParam('sort', e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  >
                    <option value="newest">Newest Arrivals</option>
                    <option value="title">Title (A–Z)</option>
                    <option value="author">Author (A–Z)</option>
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

              {/* Drawer Book List */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
                {favBooksList.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    {favBooksList.map((b) => (
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
                              margin: '0 0 6px',
                              fontSize: '0.775rem',
                              color: 'var(--maroon, #7b1230)',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                            }}
                          >
                            {b.author || 'Author not listed'}
                          </p>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <button
                              type="button"
                              onClick={() => {
                                addItem({ id: b.id, title: b.title, author: b.author || 'Author not listed' });
                              }}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                backgroundColor: 'var(--navy, #061446)',
                                color: '#ffffff',
                                border: 'none',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                              }}
                            >
                              <Plus size={12} /> Add to Cart
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
                    ))}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--text-muted, #64748b)' }}>
                    <Heart size={40} color="#cbd5e1" style={{ marginBottom: '12px' }} />
                    <p style={{ margin: '0 0 8px', fontWeight: 700, color: 'var(--navy, #061446)' }}>No favourites saved yet</p>
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
        @media (max-width: 899px) {
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
