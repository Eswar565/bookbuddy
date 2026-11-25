import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Check, ShieldCheck } from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { apiGet, apiPost } from '../api/client';
import { Link, useNavigate } from 'react-router-dom';

export interface LendingPlan {
  id: number;
  name: string;
  book_limit: number;
  duration_months: number;
  price: number;
  description?: string;
  is_active: number;
}

export const MembershipPage: React.FC = () => {
  const { user, activeSubscription, refreshUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [subscribingId, setSubscribingId] = useState<number | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['membership-plans'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/memberships/plans');
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch plans');
      return res.data?.plans as LendingPlan[];
    },
  });

  const handleSubscribe = async (plan: LendingPlan) => {
    if (!user) {
      navigate('/login?next=/membership');
      return;
    }

    setSubscribingId(plan.id);
    try {
      const res = await apiPost('/api/v1/memberships/subscribe', { plan_id: plan.id });
      if (res.ok) {
        await refreshUser();
        showToast(`Selected "${plan.name}" plan! Subscription registered.`, 'success');
      } else {
        showToast(res.error?.message || 'Could not subscribe to plan.', 'error');
      }
    } finally {
      setSubscribingId(null);
    }
  };

  const plans = data || [];

  return (
    <>
      <SEO
        title="Membership & Lending Plans | BookBuddy"
        description="Choose a flexible reading plan that fits your family. Enjoy curated children books, unlimited swaps, and doorstep delivery across Chennai."
      />

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '3rem 1.5rem 5rem' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 3.5rem' }}>
          <span
            style={{
              display: 'inline-block',
              backgroundColor: 'var(--maroon-tint, rgba(116, 15, 40, 0.08))',
              color: 'var(--maroon, #740f28)',
              fontSize: '0.8rem',
              fontWeight: 800,
              padding: '6px 14px',
              borderRadius: '20px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '12px',
            }}
          >
            Flexible Lending Plans
          </span>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 12px' }}>
            Nurture Lifelong Reading Habits
          </h1>
          <p style={{ color: 'var(--text-muted, #475569)', fontSize: '1.05rem', lineHeight: 1.6, margin: 0 }}>
            Borrow verified, age-appropriate children and young adult books with simple doorstep exchange in Chennai.
          </p>
        </div>

        {/* Current Subscription Status Banner */}
        {user && activeSubscription && (
          <div
            style={{
              backgroundColor: '#f0fdf4',
              border: '1.5px solid #86efac',
              borderRadius: '12px',
              padding: '16px 20px',
              marginBottom: '2.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShieldCheck size={24} color="#16a34a" />
              <div>
                <strong style={{ color: '#166534', fontSize: '0.95rem' }}>
                  Current Active Plan: {activeSubscription.name}
                </strong>
                <div style={{ fontSize: '0.825rem', color: '#15803d', marginTop: '2px' }}>
                  Allows up to {activeSubscription.book_limit} books at a time. Active until {activeSubscription.expires_on}.
                </div>
              </div>
            </div>
            <Link
              to="/library"
              style={{
                backgroundColor: 'var(--navy, #061446)',
                color: '#ffffff',
                padding: '8px 16px',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.85rem',
                textDecoration: 'none',
              }}
            >
              Browse Catalogue
            </Link>
          </div>
        )}

        {/* Plans Grid */}
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>Loading plans...</div>
        ) : plans.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>No plans published currently.</div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '24px',
            }}
          >
            {plans.map((plan, idx) => {
              const isFeatured = idx === 1 || plan.name.toLowerCase().includes('standard') || plan.name.toLowerCase().includes('popular');
              const isCurrentPlan = activeSubscription?.plan_id === plan.id;

              return (
                <div
                  key={plan.id}
                  style={{
                    backgroundColor: '#ffffff',
                    borderRadius: '16px',
                    padding: '32px 28px',
                    border: isFeatured ? '2px solid var(--maroon, #740f28)' : '1px solid var(--border-color)',
                    boxShadow: isFeatured ? '0 12px 32px rgba(116, 15, 40, 0.12)' : '0 4px 18px rgba(10, 36, 114, 0.05)',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                  }}
                >
                  {isFeatured && (
                    <span
                      style={{
                        position: 'absolute',
                        top: '-12px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        backgroundColor: 'var(--maroon, #740f28)',
                        color: '#ffffff',
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        textTransform: 'uppercase',
                        padding: '4px 14px',
                        borderRadius: '20px',
                        letterSpacing: '0.5px',
                      }}
                    >
                      Most Popular
                    </span>
                  )}

                  <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 6px' }}>
                    {plan.name}
                  </h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', minHeight: '38px', margin: '0 0 16px' }}>
                    {plan.description || `Ideal for eager young readers exploring stories.`}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', margin: '0 0 24px' }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--navy, #061446)' }}>
                      ₹{plan.price}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      / {plan.duration_months} {plan.duration_months === 1 ? 'month' : 'months'}
                    </span>
                  </div>

                  {/* Feature Checklist */}
                  <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 32px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                      <Check size={18} color="var(--maroon, #740f28)" />
                      <span><strong>{plan.book_limit} books</strong> at a time</span>
                    </li>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                      <Check size={18} color="var(--maroon, #740f28)" />
                      <span>Unlimited book swaps across term</span>
                    </li>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                      <Check size={18} color="var(--maroon, #740f28)" />
                      <span>Doorstep delivery & pickup available</span>
                    </li>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                      <Check size={18} color="var(--maroon, #740f28)" />
                      <span>Access to reader circles & contests</span>
                    </li>
                  </ul>

                  {/* Subscribe / Action Button */}
                  <div style={{ marginTop: 'auto' }}>
                    {isCurrentPlan ? (
                      <button
                        disabled
                        type="button"
                        style={{
                          width: '100%',
                          padding: '12px',
                          borderRadius: '10px',
                          border: '1.5px solid #16a34a',
                          backgroundColor: '#f0fdf4',
                          color: '#16a34a',
                          fontWeight: 700,
                          fontSize: '0.9rem',
                          cursor: 'default',
                        }}
                      >
                        Your Current Plan
                      </button>
                    ) : (
                      <button
                        onClick={() => handleSubscribe(plan)}
                        disabled={subscribingId === plan.id}
                        type="button"
                        style={{
                          width: '100%',
                          padding: '12px',
                          borderRadius: '10px',
                          border: 'none',
                          backgroundColor: isFeatured ? 'var(--maroon, #740f28)' : 'var(--navy, #061446)',
                          color: '#ffffff',
                          fontWeight: 700,
                          fontSize: '0.925rem',
                          cursor: subscribingId === plan.id ? 'not-allowed' : 'pointer',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                        }}
                      >
                        {subscribingId === plan.id ? 'Processing...' : user ? 'Select Plan' : 'Sign In to Join'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
};
