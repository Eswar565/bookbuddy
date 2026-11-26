import React, { useState } from 'react';
import { Heart, Plus, Check } from 'lucide-react';
import { useCart } from '../../context/CartContext';
import { Link } from 'react-router-dom';

export interface Book {
  id: number;
  title: string;
  author: string;
  collection?: string;
  language?: string;
  age_group?: string;
  available_copies: number;
  stock?: number;
  image_url?: string;
  image_path?: string;
  is_new_arrival?: boolean;
}

interface BookCardProps {
  book: Book;
  isWishlisted: boolean;
  onToggleWishlist: (bookId: number) => void;
  isAlreadyLoaned?: boolean;
}

export const BookCard: React.FC<BookCardProps> = ({
  book,
  isWishlisted,
  onToggleWishlist,
  isAlreadyLoaned = false,
}) => {
  const { addItem, isInCart } = useCart();
  const [imageError, setImageError] = useState(false);

  const coverUrl = book.image_url || book.image_path || '';
  const isAvailable = (book.available_copies ?? 0) > 0;
  const inCart = isInCart(book.id);

  const handleAddClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAvailable || isAlreadyLoaned) return;
    addItem({
      id: book.id,
      title: book.title,
      author: book.author || 'Unknown Author',
    });
  };

  const handleHeartClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onToggleWishlist(book.id);
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        padding: '10px',
        boxShadow: '0 4px 18px rgba(10, 36, 114, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        minWidth: 0,
        boxSizing: 'border-box',
        position: 'relative',
        transition: 'transform 0.18s ease, box-shadow 0.18s ease, border-bottom 0.18s ease',
        borderBottom: '3px solid transparent',
        height: '100%',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-3px)';
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(10, 36, 114, 0.14)';
        e.currentTarget.style.borderBottom = '3px solid var(--maroon, #7b1230)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 4px 18px rgba(10, 36, 114, 0.08)';
        e.currentTarget.style.borderBottom = '3px solid transparent';
      }}
    >
      {/* Cover Container */}
      <Link
        to={`/library/${book.id}`}
        style={{
          display: 'block',
          position: 'relative',
          width: '100%',
          minWidth: 0,
          boxSizing: 'border-box',
          aspectRatio: '3/4',
          maxHeight: '210px',
          backgroundColor: '#e1e6f0',
          borderRadius: '8px',
          overflow: 'hidden',
          textDecoration: 'none',
        }}
      >
        {coverUrl && !imageError ? (
          <img
            src={coverUrl.startsWith('/') ? coverUrl : `/${coverUrl}`}
            alt={book.title}
            loading="lazy"
            onError={() => setImageError(true)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              display: 'block',
            }}
          />
        ) : (
          <div
            style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--navy, #0a2472)',
              fontWeight: 800,
              fontSize: '0.85rem',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
            }}
          >
            No Cover
          </div>
        )}

        {/* Wishlist Heart Button */}
        <button
          onClick={handleHeartClick}
          type="button"
          aria-label={isWishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
          aria-pressed={isWishlisted}
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 2px 6px rgba(0,0,0,0.12)',
            zIndex: 2,
            transition: 'transform 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.1)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1.0)')}
        >
          <Heart
            size={16}
            color={isWishlisted ? 'var(--maroon, #7b1230)' : '#94a3b8'}
            fill={isWishlisted ? 'var(--maroon, #7b1230)' : 'none'}
          />
        </button>

        {book.is_new_arrival && (
          <span
            style={{
              position: 'absolute',
              bottom: '6px',
              left: '6px',
              backgroundColor: 'var(--gold, #d97706)',
              color: '#ffffff',
              fontSize: '0.65rem',
              fontWeight: 800,
              padding: '2px 6px',
              borderRadius: '4px',
              textTransform: 'uppercase',
            }}
          >
            New
          </span>
        )}
      </Link>

      {/* Meta: Title & Author */}
      <div style={{ marginTop: '8px', marginBottom: '8px', flex: '0 0 auto', minWidth: 0, width: '100%', boxSizing: 'border-box' }}>
        <Link
          to={`/library/${book.id}`}
          title={book.title}
          style={{
            display: 'block',
            fontWeight: 700,
            fontSize: '0.9rem',
            color: 'var(--navy, #0a2472)',
            whiteSpace: 'nowrap',
            textOverflow: 'ellipsis',
            overflow: 'hidden',
            textDecoration: 'none',
            minWidth: 0,
          }}
        >
          {book.title}
        </Link>
        <div
          title={book.author}
          style={{
            fontSize: '0.8rem',
            color: 'var(--maroon, #7b1230)',
            whiteSpace: 'nowrap',
            textOverflow: 'ellipsis',
            overflow: 'hidden',
            marginTop: '2px',
            minWidth: 0,
          }}
        >
          {book.author || 'Unknown Author'}
        </div>
      </div>

      {/* Card footer (replace the current bottom row: stacked layout) */}
      <div className="book-card__footer">
        {!isAvailable ? (
          <span className="book-card__status book-card__status--unavailable">
            Unavailable
          </span>
        ) : isAlreadyLoaned ? (
          <>
            <span className="book-card__status">
              Available: {book.available_copies ?? 0}
            </span>
            <button
              type="button"
              disabled
              className="book-card__action"
              title="Already in your active requests or loans"
            >
              Active Request
            </button>
          </>
        ) : (
          <>
            <span className="book-card__status">
              Available: {book.available_copies ?? 0}
            </span>

            <button
              onClick={handleAddClick}
              type="button"
              className={`book-card__action ${inCart ? 'book-card__action--added' : 'book-card__action--add'}`}
              aria-label={inCart ? `Remove ${book.title} from cart` : `Add ${book.title} to cart`}
              aria-pressed={inCart}
            >
              {inCart ? (
                <>
                  <Check size={14} strokeWidth={2.5} style={{ flexShrink: 0 }} />
                  <span>Added</span>
                </>
              ) : (
                <>
                  <Plus size={14} strokeWidth={2.5} style={{ flexShrink: 0 }} />
                  <span>Add</span>
                </>
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
};
