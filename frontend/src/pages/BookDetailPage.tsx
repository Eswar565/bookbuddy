import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Plus, Check, ShoppingBag, Heart } from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { useCart } from '../context/CartContext';
import { apiGet } from '../api/client';

export const BookDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { addItem, isInCart, openCheckout } = useCart();
  const [imageError, setImageError] = useState(false);

  // Local wishlist check
  const [isWishlisted, setIsWishlisted] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem('bb_wishlist');
      const list: number[] = stored ? JSON.parse(stored) : [];
      return list.includes(Number(id));
    } catch {
      return false;
    }
  });

  const toggleWishlist = () => {
    if (!id) return;
    const numId = Number(id);
    try {
      const stored = localStorage.getItem('bb_wishlist');
      const list: number[] = stored ? JSON.parse(stored) : [];
      const next = list.includes(numId) ? list.filter((i) => i !== numId) : [...list, numId];
      localStorage.setItem('bb_wishlist', JSON.stringify(next));
      setIsWishlisted(next.includes(numId));
    } catch {
      // ignore
    }
  };

  const { data, isLoading, isError } = useQuery({
    queryKey: ['book', id],
    queryFn: async () => {
      const res = await apiGet(`/api/v1/books/${id}`);
      if (!res.ok) throw new Error(res.error?.message || 'Book not found');
      return res.data?.book;
    },
    enabled: Boolean(id),
  });

  if (isLoading) {
    return (
      <div style={{ maxWidth: '960px', margin: '4rem auto', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading book details...
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div style={{ maxWidth: '640px', margin: '5rem auto', textAlign: 'center', padding: '0 1rem' }}>
        <h2 style={{ color: 'var(--navy)', marginBottom: '1rem' }}>Book Not Found</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          This book may have been archived or is no longer available.
        </p>
        <Link
          to="/library"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            color: 'var(--maroon)',
            fontWeight: 700,
            textDecoration: 'none',
          }}
        >
          <ArrowLeft size={16} /> Return to Catalogue
        </Link>
      </div>
    );
  }

  const book = data;
  const isAvailable = (book.available_copies ?? 0) > 0;
  const inCart = isInCart(book.id);
  const coverUrl = book.image_url || book.image_path || '';

  return (
    <>
      <SEO title={`${book.title} | BookBuddy Library`} description={book.description || `Read ${book.title} by ${book.author} at BookBuddy.`} />

      <div style={{ maxWidth: '1040px', margin: '0 auto', padding: '2rem 1.5rem 5rem' }}>
        <Link
          to="/library"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            color: 'var(--navy, #061446)',
            fontSize: '0.875rem',
            fontWeight: 700,
            textDecoration: 'none',
            marginBottom: '2rem',
          }}
        >
          <ArrowLeft size={16} /> Back to Catalogue
        </Link>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '40px',
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            padding: '32px',
            boxShadow: '0 6px 24px rgba(10, 36, 114, 0.08)',
          }}
        >
          {/* Left: Cover */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div
              style={{
                width: '100%',
                maxWidth: '280px',
                aspectRatio: '3/4',
                backgroundColor: '#e1e6f0',
                borderRadius: '12px',
                overflow: 'hidden',
                boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                position: 'relative',
              }}
            >
              {coverUrl && !imageError ? (
                <img
                  src={coverUrl.startsWith('/') ? coverUrl : `/${coverUrl}`}
                  alt={book.title}
                  onError={() => setImageError(true)}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <div
                  style={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--navy)',
                    fontWeight: 800,
                    fontSize: '1.1rem',
                  }}
                >
                  No Cover
                </div>
              )}
            </div>

            <button
              onClick={toggleWishlist}
              type="button"
              style={{
                marginTop: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'transparent',
                border: '1px solid var(--border-color)',
                borderRadius: '24px',
                padding: '8px 18px',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: isWishlisted ? 'var(--maroon)' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              <Heart size={16} color={isWishlisted ? 'var(--maroon)' : '#64748b'} fill={isWishlisted ? 'var(--maroon)' : 'none'} />
              <span>{isWishlisted ? 'Saved to Wishlist' : 'Add to Wishlist'}</span>
            </button>
          </div>

          {/* Right: Details */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {book.collection && (
              <span
                style={{
                  display: 'inline-block',
                  backgroundColor: 'var(--navy-tint, rgba(6, 20, 70, 0.06))',
                  color: 'var(--navy, #061446)',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  marginBottom: '12px',
                  width: 'fit-content',
                }}
              >
                {book.collection}
              </span>
            )}

            <h1 style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--navy, #061446)', lineHeight: 1.25, margin: '0 0 8px' }}>
              {book.title}
            </h1>

            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--maroon, #7b1230)', marginBottom: '20px' }}>
              by {book.author || 'Unknown Author'}
            </div>

            {/* Availability Badge */}
            <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  padding: '6px 14px',
                  borderRadius: '20px',
                  fontSize: '0.825rem',
                  fontWeight: 700,
                  backgroundColor: isAvailable ? 'var(--navy, #061446)' : '#f1f5f9',
                  color: isAvailable ? '#ffffff' : '#64748b',
                }}
              >
                {isAvailable ? `Available Copies: ${book.available_copies}` : 'Currently Unavailable'}
              </span>
            </div>

            {/* Metadata Badges */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px', marginBottom: '24px' }}>
              {book.language && (
                <div style={{ padding: '10px 14px', backgroundColor: 'var(--surface-body, #f8fafc)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Language</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--navy)' }}>{book.language}</div>
                </div>
              )}
              {book.age_group && (
                <div style={{ padding: '10px 14px', backgroundColor: 'var(--surface-body, #f8fafc)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Recommended Age</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--navy)' }}>{book.age_group} yrs</div>
                </div>
              )}
            </div>

            {/* Description */}
            {book.description && (
              <div style={{ marginBottom: '28px' }}>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy)', marginBottom: '8px' }}>About this Book</h3>
                <p style={{ fontSize: '0.925rem', lineHeight: 1.6, color: 'var(--text-muted)', whiteSpace: 'pre-line', margin: 0 }}>
                  {book.description}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ marginTop: 'auto', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <button
                onClick={() =>
                  addItem({
                    id: book.id,
                    title: book.title,
                    author: book.author || 'Unknown Author',
                  })
                }
                disabled={!isAvailable}
                type="button"
                style={{
                  flex: 1,
                  minWidth: '180px',
                  padding: '12px 24px',
                  borderRadius: '10px',
                  border: 'none',
                  backgroundColor: inCart ? '#059669' : isAvailable ? 'var(--maroon, #7b1230)' : '#cbd5e1',
                  color: '#ffffff',
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  cursor: isAvailable ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {inCart ? (
                  <>
                    <Check size={18} />
                    <span>Added to Cart</span>
                  </>
                ) : (
                  <>
                    <Plus size={18} />
                    <span>Add to Borrow Cart</span>
                  </>
                )}
              </button>

              {inCart && (
                <button
                  onClick={openCheckout}
                  type="button"
                  style={{
                    padding: '12px 22px',
                    borderRadius: '10px',
                    border: '1.5px solid var(--navy, #061446)',
                    backgroundColor: '#ffffff',
                    color: 'var(--navy, #061446)',
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <ShoppingBag size={18} />
                  <span>View Cart</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
