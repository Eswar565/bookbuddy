import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { useToast } from './ToastContext';
import { apiPost } from '../api/client';

export interface CartItem {
  id: number;
  title: string;
  author: string;
}

interface CartContextType {
  items: CartItem[];
  count: number;
  isOpen: boolean;
  openCheckout: () => void;
  closeCheckout: () => void;
  addItem: (book: { id: number; title: string; author: string }) => boolean;
  removeItem: (bookId: number) => void;
  clearCart: () => void;
  isInCart: (bookId: number) => boolean;
  submitCheckout: (payload: { delivery_mode: string; address?: string; notes?: string }) => Promise<{ success: boolean; error?: string }>;
  maxAllowed: number;
  remainingAllowance: number;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

const CART_STORAGE_KEY = 'bb_cart';

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, activeSubscription, activeLoansCount, refreshUser } = useAuth();
  const { showToast } = useToast();

  const [items, setItems] = useState<CartItem[]>(() => {
    try {
      const stored = localStorage.getItem(CART_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const [isOpen, setIsOpen] = useState(false);

  // Sync state to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
    } catch {
      // ignore localStorage quota errors
    }
  }, [items]);

  const planLimit = activeSubscription ? activeSubscription.book_limit : 2;
  const maxAllowed = Math.max(0, planLimit - activeLoansCount);
  const remainingAllowance = Math.max(0, maxAllowed - items.length);

  const isInCart = useCallback(
    (bookId: number) => items.some((item) => item.id === bookId),
    [items]
  );

  const addItem = useCallback(
    (book: { id: number; title: string; author: string }): boolean => {
      if (items.some((item) => item.id === book.id)) {
        // Toggle remove if already added
        setItems((prev) => prev.filter((i) => i.id !== book.id));
        showToast(`Removed "${book.title}" from your request`, 'info');
        return false;
      }

      if (user && activeSubscription) {
        if (items.length + activeLoansCount >= planLimit) {
          showToast(`Your ${activeSubscription.name} plan allows ${planLimit} books at a time.`, 'error');
          return false;
        }
      } else if (!user) {
        // Guest limit preview
        if (items.length >= 2) {
          showToast('Sign in with an active membership plan to add more books.', 'error');
          return false;
        }
      }

      setItems((prev) => [...prev, { id: book.id, title: book.title, author: book.author }]);
      showToast(`Added "${book.title}" to your borrow list`, 'success');
      return true;
    },
    [items, user, activeSubscription, activeLoansCount, planLimit, showToast]
  );

  const removeItem = useCallback(
    (bookId: number) => {
      setItems((prev) => prev.filter((item) => item.id !== bookId));
    },
    []
  );

  const clearCart = useCallback(() => {
    setItems([]);
    try {
      localStorage.removeItem(CART_STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  const openCheckout = useCallback(() => setIsOpen(true), []);
  const closeCheckout = useCallback(() => setIsOpen(false), []);

  const submitCheckout = async (payload: { delivery_mode: string; address?: string; notes?: string }) => {
    if (items.length === 0) {
      return { success: false, error: 'Your cart is empty.' };
    }

    const res = await apiPost('/api/v1/checkout', {
      items,
      delivery_mode: payload.delivery_mode,
      address: payload.address,
      notes: payload.notes,
    });

    if (res.ok) {
      clearCart();
      closeCheckout();
      await refreshUser();
      showToast('Borrow request placed successfully! Our librarians are processing it.', 'success');
      return { success: true };
    }

    const errorMsg = res.error?.message || 'Failed to submit borrow request. Please try again.';
    showToast(errorMsg, 'error');
    return { success: false, error: errorMsg };
  };

  return (
    <CartContext.Provider
      value={{
        items,
        count: items.length,
        isOpen,
        openCheckout,
        closeCheckout,
        addItem,
        removeItem,
        clearCart,
        isInCart,
        submitCheckout,
        maxAllowed,
        remainingAllowance,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
