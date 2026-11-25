import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Search, ShoppingBag, FileSpreadsheet, FileText, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { BookCard, Book } from '../components/books/BookCard';
import { useCart } from '../context/CartContext';
import { apiGet } from '../api/client';

export const LibraryPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { count, openCheckout } = useCart();

  // Search and filter state from URL params
  const q = searchParams.get('q') || '';
  const audience = searchParams.get('audience') || '';
  const language = searchParams.get('language') || '';
  const collection = searchParams.get('collection') || '';
  const availability = searchParams.get('availability') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);

  const [searchInput, setSearchInput] = useState(q);

  // Local state for wishlisted items
  const [wishlist, setWishlist] = useState<number[]>(() => {
    try {
      const stored = localStorage.getItem('bb_wishlist');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const toggleWishlist = (bookId: number) => {
    setWishlist((prev) => {
      const next = prev.includes(bookId) ? prev.filter((id) => id !== bookId) : [...prev, bookId];
      try {
        localStorage.setItem('bb_wishlist', JSON.stringify(next));
      } catch {
        // ignore
      }
      return next;
    });
  };

  // Query books from /api/v1/books
  const queryString = searchParams.toString();
  const { data, isLoading, isError } = useQuery({
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

  const handleExport = (format: 'xlsx' | 'pdf') => {
    const params = new URLSearchParams(searchParams);
    params.delete('page');
    window.location.href = `/api/v1/books/export/${format}?${params.toString()}`;
  };

  return (
    <>
      <SEO
        title="Book Catalogue | BookBuddy Library"
        description="Browse thousands of curated children, teen, and adult books in Chennai. Add books to your borrow cart for doorstep delivery or pickup."
      />

      <div style={{ maxWidth: '1360px', margin: '0 auto', padding: '2rem 1.5rem 4rem' }}>
        {/* Page Header */}
        <div style={{ marginBottom: '1.75rem' }}>
          <h1 style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: 0 }}>
            Library Catalogue
          </h1>
          <p style={{ color: 'var(--text-muted, #475569)', marginTop: '0.4rem', fontSize: '0.95rem' }}>
            Discover captivating stories, picture books, classics, and reference titles.
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '10px', marginBottom: '1.5rem', maxWidth: '640px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={18} color="var(--text-subtle, #64748b)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by title, author, or ISBN..."
              style={{
                width: '100%',
                padding: '11px 16px 11px 40px',
                borderRadius: '10px',
                border: '1.5px solid var(--border-color, #e2e8f0)',
                fontSize: '0.925rem',
                backgroundColor: '#ffffff',
                outline: 'none',
              }}
            />
          </div>
          <button
            type="submit"
            style={{
              padding: '0 20px',
              backgroundColor: 'var(--navy, #061446)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '10px',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
            }}
          >
            Search
          </button>
        </form>

        {/* Filter Controls Row */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            padding: '14px 18px',
            boxShadow: '0 2px 12px rgba(10, 36, 114, 0.05)',
            marginBottom: '1.75rem',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '14px',
          }}
        >
          {/* Left Controls: Readers filter & quick toggles */}
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-muted)' }}>Readers:</span>
            {['', 'adults', 'kids'].map((aud) => (
              <button
                key={aud}
                type="button"
                onClick={() => updateParam('audience', aud)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '20px',
                  border: audience === aud ? '1.5px solid var(--navy, #061446)' : '1px solid var(--border-color)',
                  backgroundColor: audience === aud ? 'var(--navy, #061446)' : '#ffffff',
                  color: audience === aud ? '#ffffff' : 'var(--text-muted)',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {aud ? aud.charAt(0).toUpperCase() + aud.slice(1) : 'All'}
              </button>
            ))}

            {/* Availability filter */}
            <select
              value={availability}
              onChange={(e) => updateParam('availability', e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                fontSize: '0.8rem',
                color: 'var(--navy)',
                fontWeight: 600,
                backgroundColor: '#fff',
                cursor: 'pointer',
              }}
            >
              <option value="">All Stock</option>
              <option value="available">Available Now</option>
              <option value="waitlist">Waitlist / Loaned</option>
            </select>

            {/* Category / Collection dropdown */}
            {filterOptions.collections && (
              <select
                value={collection}
                onChange={(e) => updateParam('collection', e.target.value)}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.8rem',
                  color: 'var(--navy)',
                  fontWeight: 600,
                  backgroundColor: '#fff',
                  cursor: 'pointer',
                }}
              >
                <option value="">All Collections</option>
                {filterOptions.collections.map((col: string) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Right Group: Exports, Checkout Button, and Language */}
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '10px' }}>
            {/* Export Buttons */}
            <button
              onClick={() => handleExport('xlsx')}
              type="button"
              title="Export catalogue as Excel"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: '#15803d',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <FileSpreadsheet size={15} />
              <span>Excel</span>
            </button>

            <button
              onClick={() => handleExport('pdf')}
              type="button"
              title="Export catalogue as PDF"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: '#b91c1c',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <FileText size={15} />
              <span>PDF</span>
            </button>

            {/* Checkout Button Immediately BEFORE Language */}
            <button
              onClick={openCheckout}
              type="button"
              aria-label="Open borrow cart"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '7px 16px',
                borderRadius: '50px',
                border: 'none',
                backgroundColor: 'var(--maroon, #7b1230)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.825rem',
                cursor: 'pointer',
                boxShadow: '0 3px 8px rgba(123, 18, 48, 0.25)',
              }}
            >
              <ShoppingBag size={16} />
              <span>Checkout</span>
              {count > 0 && (
                <span
                  style={{
                    backgroundColor: '#ffffff',
                    color: 'var(--maroon, #7b1230)',
                    borderRadius: '50%',
                    width: '19px',
                    height: '19px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                  }}
                >
                  {count}
                </span>
              )}
            </button>

            {/* Language filter group */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-muted)' }}>Language:</span>
              {['', 'English', 'Tamil'].map((lang) => (
                <button
                  key={lang}
                  type="button"
                  onClick={() => updateParam('language', lang)}
                  style={{
                    padding: '5px 10px',
                    borderRadius: '16px',
                    border: language === lang ? '1.5px solid var(--navy, #061446)' : '1px solid var(--border-color)',
                    backgroundColor: language === lang ? 'var(--navy, #061446)' : '#ffffff',
                    color: language === lang ? '#ffffff' : 'var(--text-muted)',
                    fontSize: '0.775rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {lang || 'All'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Info & Active Filters */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Showing <strong>{books.length}</strong> of <strong>{totalCount}</strong> books
          </div>
          {(q || audience || language || collection || availability) && (
            <button
              onClick={() => setSearchParams({})}
              type="button"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--maroon, #7b1230)',
                fontSize: '0.825rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <X size={14} /> Clear all filters
            </button>
          )}
        </div>

        {/* Book Grid */}
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '5rem 0', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>Loading catalogue...</div>
          </div>
        ) : isError ? (
          <div style={{ textAlign: 'center', padding: '5rem 0', color: '#dc2626' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>Failed to load books. Please check your connection.</div>
          </div>
        ) : books.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '5rem 2rem',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px dashed var(--border-color)',
            }}
          >
            <h3 style={{ fontSize: '1.2rem', color: 'var(--navy)', marginBottom: '0.5rem' }}>No books found</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Try clearing filters or searching for a different keyword.</p>
          </div>
        ) : (
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
        )}

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div
            style={{
              marginTop: '3rem',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <button
              onClick={() => updateParam('page', String(page - 1))}
              disabled={page <= 1}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '8px 14px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: page <= 1 ? '#cbd5e1' : 'var(--navy)',
                cursor: page <= 1 ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '0.85rem',
              }}
            >
              <ChevronLeft size={16} /> Previous
            </button>

            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Page {page} of {totalPages}
            </span>

            <button
              onClick={() => updateParam('page', String(page + 1))}
              disabled={page >= totalPages}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '8px 14px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: page >= totalPages ? '#cbd5e1' : 'var(--navy)',
                cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '0.85rem',
              }}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>
    </>
  );
};
