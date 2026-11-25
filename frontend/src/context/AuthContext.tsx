import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiGet, apiPost } from '../api/client';

export interface User {
  id: number;
  name: string;
  email: string;
  phone?: string;
  dob?: string;
  address?: string;
  is_active?: boolean;
}

export interface ActiveSubscription {
  id: number;
  user_id: number;
  plan_id: number;
  name: string;
  book_limit: number;
  starts_on: string;
  expires_on: string;
  status: string;
}

interface AuthContextType {
  user: User | null;
  activeSubscription: ActiveSubscription | null;
  activeLoansCount: number;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (payload: { name: string; email: string; password: string; phone?: string; dob?: string }) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [activeSubscription, setActiveSubscription] = useState<ActiveSubscription | null>(null);
  const [activeLoansCount, setActiveLoansCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = useCallback(async () => {
    try {
      const res = await apiGet('/api/v1/auth/me');
      if (res.ok && res.data) {
        setUser(res.data.user || null);
        setActiveSubscription(res.data.active_subscription || null);
        setActiveLoansCount(res.data.active_loans_count || 0);
      } else {
        setUser(null);
        setActiveSubscription(null);
        setActiveLoansCount(0);
      }
    } catch {
      setUser(null);
      setActiveSubscription(null);
      setActiveLoansCount(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const res = await apiPost('/api/v1/auth/login', { email, password });
    if (res.ok && res.data) {
      setUser(res.data.user || null);
      setActiveSubscription(res.data.active_subscription || null);
      setActiveLoansCount(res.data.active_loans_count || 0);
      return { success: true };
    }
    return {
      success: false,
      error: res.error?.message || 'Invalid email or password',
    };
  };

  const signup = async (payload: { name: string; email: string; password: string; phone?: string; dob?: string }) => {
    const res = await apiPost('/api/v1/auth/signup', payload);
    if (res.ok && res.data) {
      setUser(res.data.user || null);
      setActiveSubscription(null);
      setActiveLoansCount(0);
      return { success: true };
    }
    return {
      success: false,
      error: res.error?.message || 'Registration failed. Please check your details.',
    };
  };

  const logout = async () => {
    await apiPost('/api/v1/auth/logout');
    setUser(null);
    setActiveSubscription(null);
    setActiveLoansCount(0);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activeSubscription,
        activeLoansCount,
        isLoading,
        refreshUser,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
