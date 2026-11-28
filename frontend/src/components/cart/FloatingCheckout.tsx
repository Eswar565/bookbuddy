import React from 'react';
import { Icon } from '../ui/Icon';
import { useCart } from '../../context/CartContext';

export const FloatingCheckout: React.FC = () => {
  const { count, openCheckout } = useCart();

  if (count === 0) return null;

  return (
    <button
      onClick={openCheckout}
      type="button"
      aria-label={`Open borrow cart with ${count} items`}
      style={{
        position: 'fixed',
        bottom: '28px',
        right: '28px',
        zIndex: 900,
        backgroundColor: 'var(--maroon, #740f28)',
        color: '#ffffff',
        border: 'none',
        borderRadius: '50px',
        padding: '12px 22px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        fontWeight: 700,
        fontSize: '0.95rem',
        boxShadow: '0 8px 24px rgba(116, 15, 40, 0.35)',
        cursor: 'pointer',
        transition: 'transform 0.15s ease, box-shadow 0.15s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 12px 28px rgba(116, 15, 40, 0.45)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(116, 15, 40, 0.35)';
      }}
    >
      <Icon name="shopping-bag" size={20} />
      <span>Checkout</span>
      <span
        style={{
          backgroundColor: '#ffffff',
          color: 'var(--maroon, #740f28)',
          borderRadius: '50%',
          width: '22px',
          height: '22px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.8rem',
          fontWeight: 800,
        }}
      >
        {count}
      </span>
    </button>
  );
};
