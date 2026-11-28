import React, { useState, useEffect } from 'react';
import { X, Trash2, MapPin, Truck, AlertCircle, CheckCircle, BookOpen } from 'lucide-react';
import { useCart } from '../../context/CartContext';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';

export const CheckoutModal: React.FC = () => {
  const { items, isOpen, closeCheckout, removeItem, submitCheckout } = useCart();
  const { user, activeSubscription } = useAuth();

  const [deliveryMode, setDeliveryMode] = useState<'pickup' | 'delivery'>('pickup');
  const [address, setAddress] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Esc key closes modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closeCheckout();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, closeCheckout]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setIsSubmitting(true);
    await submitCheckout({
      delivery_mode: deliveryMode,
      address: deliveryMode === 'delivery' ? address : undefined,
      notes: notes.trim() || undefined,
    });
    setIsSubmitting(false);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="checkout-modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        backgroundColor: 'rgba(4, 13, 46, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) closeCheckout();
      }}
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '480px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.25)',
          overflow: 'hidden',
          animation: 'fadeSlideUp 0.2s ease-out',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--border-color, #e2e8f0)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <h2 id="checkout-modal-title" style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy, #061446)' }}>
              Confirm Borrow Request
            </h2>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-muted, #475569)', marginTop: '2px' }}>
              {items.length} {items.length === 1 ? 'book' : 'books'} selected
            </p>
          </div>
          <button
            onClick={closeCheckout}
            type="button"
            aria-label="Close dialog"
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted, #475569)',
              padding: '6px',
              borderRadius: '50%',
              display: 'flex',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body Content */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1 }}>
          {/* Selected Books List */}
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '10px' }}>
              Selected Titles
            </h3>
            {items.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-muted)' }}>
                <BookOpen size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                <p style={{ fontSize: '0.9rem' }}>Your borrow list is empty.</p>
              </div>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {items.map((item) => (
                  <li
                    key={item.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      backgroundColor: 'var(--surface-body, #f8fafc)',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color, #e2e8f0)',
                    }}
                  >
                    <div style={{ maxWidth: '82%', overflow: 'hidden' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--navy, #061446)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                        {item.title}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--maroon, #740f28)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                        {item.author}
                      </div>
                    </div>
                    <button
                      onClick={() => removeItem(item.id)}
                      type="button"
                      aria-label={`Remove ${item.title}`}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-subtle, #64748b)',
                        cursor: 'pointer',
                        padding: '4px',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#dc2626')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-subtle, #64748b)')}
                    >
                      <Trash2 size={16} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* User Auth & Subscription Check */}
          {!user ? (
            <div
              style={{
                backgroundColor: '#fffbeb',
                border: '1px solid #fde68a',
                borderRadius: '8px',
                padding: '14px',
                marginBottom: '18px',
                display: 'flex',
                gap: '10px',
                alignItems: 'flex-start',
              }}
            >
              <AlertCircle size={20} color="#d97706" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ fontSize: '0.9rem', color: '#92400e' }}>Account Required</strong>
                <p style={{ fontSize: '0.825rem', color: '#b45309', margin: '4px 0 8px' }}>
                  Please sign in or create a member account to submit your borrowing request.
                </p>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <Link
                    to="/login"
                    onClick={closeCheckout}
                    style={{
                      padding: '5px 12px',
                      backgroundColor: 'var(--navy, #061446)',
                      color: '#ffffff',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      textDecoration: 'none',
                    }}
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/signup"
                    onClick={closeCheckout}
                    style={{
                      padding: '5px 12px',
                      backgroundColor: '#ffffff',
                      color: 'var(--navy, #061446)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      textDecoration: 'none',
                    }}
                  >
                    Join BookBuddy
                  </Link>
                </div>
              </div>
            </div>
          ) : !activeSubscription ? (
            <div
              style={{
                backgroundColor: '#eff6ff',
                border: '1px solid #bfdbfe',
                borderRadius: '8px',
                padding: '14px',
                marginBottom: '18px',
                display: 'flex',
                gap: '10px',
                alignItems: 'flex-start',
              }}
            >
              <AlertCircle size={20} color="#2563eb" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ fontSize: '0.9rem', color: '#1e40af' }}>Active Subscription Needed</strong>
                <p style={{ fontSize: '0.825rem', color: '#1d4ed8', margin: '4px 0 8px' }}>
                  Your account does not have an active lending subscription to borrow titles.
                </p>
                <Link
                  to="/membership"
                  onClick={closeCheckout}
                  style={{
                    display: 'inline-block',
                    padding: '6px 14px',
                    backgroundColor: 'var(--maroon, #740f28)',
                    color: '#ffffff',
                    borderRadius: '6px',
                    fontSize: '0.825rem',
                    fontWeight: 700,
                    textDecoration: 'none',
                  }}
                >
                  Choose a Plan
                </Link>
              </div>
            </div>
          ) : (
            <div
              style={{
                backgroundColor: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '8px',
                padding: '10px 14px',
                marginBottom: '18px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.825rem',
                color: '#166534',
              }}
            >
              <CheckCircle size={16} color="#16a34a" />
              <span>
                Active Plan: <strong>{activeSubscription.name}</strong> ({activeSubscription.book_limit} books at a time)
              </span>
            </div>
          )}

          {/* Form Options (when logged in with active sub) */}
          {user && activeSubscription && items.length > 0 && (
            <form onSubmit={handleSubmit} id="checkout-form">
              {/* Delivery Mode Toggle */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '8px' }}>
                  Fulfillment Mode
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => setDeliveryMode('pickup')}
                    style={{
                      padding: '10px',
                      borderRadius: '8px',
                      border: deliveryMode === 'pickup' ? '2px solid var(--navy, #061446)' : '1px solid var(--border-color)',
                      backgroundColor: deliveryMode === 'pickup' ? 'var(--navy-tint, rgba(6, 20, 70, 0.06))' : '#fff',
                      color: 'var(--navy, #061446)',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                    }}
                  >
                    <MapPin size={16} />
                    <span>In-Person Pickup</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeliveryMode('delivery')}
                    style={{
                      padding: '10px',
                      borderRadius: '8px',
                      border: deliveryMode === 'delivery' ? '2px solid var(--navy, #061446)' : '1px solid var(--border-color)',
                      backgroundColor: deliveryMode === 'delivery' ? 'var(--navy-tint, rgba(6, 20, 70, 0.06))' : '#fff',
                      color: 'var(--navy, #061446)',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                    }}
                  >
                    <Truck size={16} />
                    <span>Home Delivery</span>
                  </button>
                </div>
              </div>

              {deliveryMode === 'delivery' && (
                <div style={{ marginBottom: '14px' }}>
                  <label htmlFor="delivery-address" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Delivery Address (Chennai within 5km)
                  </label>
                  <textarea
                    id="delivery-address"
                    rows={2}
                    required
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="Enter street name, area, pincode..."
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.875rem',
                      fontFamily: 'inherit',
                    }}
                  />
                </div>
              )}

              <div style={{ marginBottom: '14px' }}>
                <label htmlFor="checkout-notes" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Notes for the Librarian (Optional)
                </label>
                <input
                  id="checkout-notes"
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Will collect Saturday afternoon"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    fontSize: '0.875rem',
                    fontFamily: 'inherit',
                  }}
                />
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--border-color, #e2e8f0)',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '10px',
            backgroundColor: 'var(--surface-body, #f8fafc)',
          }}
        >
          <button
            onClick={closeCheckout}
            type="button"
            style={{
              padding: '9px 18px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              backgroundColor: '#ffffff',
              color: 'var(--text-muted)',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            Close
          </button>
          {user && activeSubscription && items.length > 0 && (
            <button
              form="checkout-form"
              type="submit"
              disabled={isSubmitting}
              style={{
                padding: '9px 20px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: 'var(--maroon, #740f28)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.875rem',
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                opacity: isSubmitting ? 0.7 : 1,
              }}
            >
              {isSubmitting ? 'Submitting...' : 'Confirm Request'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
