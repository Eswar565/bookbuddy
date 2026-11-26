import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Check, ShieldCheck, MapPin, Truck, Calendar, Sparkles } from 'lucide-react';
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

  const rawPlans = data || [];
  // Ensure "Summer Special" is renamed to "Beginner Plan" if coming from any legacy cache/API
  const plans = rawPlans.map(p => ({
    ...p,
    name: p.name.replace(/Summer Special/gi, 'Beginner Plan'),
    description: p.description?.replace(/Summer Special/gi, 'Beginner Plan'),
  }));

  return (
    <>
      <SEO
        title="Membership &amp; Lending Plans | BookBuddy"
        description="Choose a flexible reading plan that fits your family. Enjoy curated children books, unlimited swaps, and doorstep delivery across Chennai."
      />
      <h1 className="sr-only">Membership Plans</h1>

      <div style={{ maxWidth: '1100px', width: '92%', margin: '0 auto', padding: '24px 0 48px' }}>
        {/* Current Subscription Status Banner */}
        {user && activeSubscription && (
          <div
            style={{
              backgroundColor: '#f0fdf4',
              border: '1.5px solid #86efac',
              borderRadius: '10px',
              padding: '10px 16px',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={20} color="#16a34a" />
              <div>
                <strong style={{ color: '#166534', fontSize: '0.9rem' }}>
                  Current Active Plan: {activeSubscription.name.replace(/Summer Special/gi, 'Beginner Plan')}
                </strong>
                <span style={{ fontSize: '0.8rem', color: '#15803d', marginLeft: '8px' }}>
                  ({activeSubscription.book_limit} books at a time · Active until {activeSubscription.expires_on})
                </span>
              </div>
            </div>
            <Link
              to="/library"
              style={{
                backgroundColor: 'var(--navy, #061446)',
                color: '#ffffff',
                padding: '6px 12px',
                borderRadius: '6px',
                fontWeight: 700,
                fontSize: '0.8rem',
                textDecoration: 'none',
              }}
            >
              Browse Catalogue
            </Link>
          </div>
        )}

        {/* 1. Plans Section (Top) */}
        <section aria-label="Membership plans">
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>Loading plans...</div>
          ) : plans.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>No plans published currently.</div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '16px',
                alignItems: 'stretch',
              }}
            >
              {plans.map((plan, idx) => {
                const isFeatured = idx === 1 || plan.name.toLowerCase().includes('popular') || plan.name.toLowerCase().includes('annual') || plan.name.toLowerCase().includes('9 months');
                const isCurrentPlan = activeSubscription?.plan_id === plan.id;

                return (
                  <div
                    key={plan.id}
                    style={{
                      backgroundColor: '#ffffff',
                      borderRadius: '12px',
                      padding: '16px 14px',
                      border: isFeatured ? '2px solid var(--maroon, #740f28)' : '1px solid var(--border-color, #e5e7eb)',
                      boxShadow: isFeatured ? '0 4px 16px rgba(116, 15, 40, 0.08)' : '0 2px 8px rgba(10, 36, 114, 0.04)',
                      display: 'flex',
                      flexDirection: 'column',
                      position: 'relative',
                      minWidth: 0,
                    }}
                  >
                    {isFeatured && (
                      <span
                        style={{
                          position: 'absolute',
                          top: '-10px',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          backgroundColor: 'var(--maroon, #740f28)',
                          color: '#ffffff',
                          fontSize: '0.68rem',
                          fontWeight: 800,
                          textTransform: 'uppercase',
                          padding: '2px 10px',
                          borderRadius: '20px',
                          letterSpacing: '0.5px',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        BEST VALUE
                      </span>
                    )}

                    <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 2px', textAlign: 'center', wordBreak: 'break-word' }}>
                      {plan.name}
                    </h3>
                    <p style={{ color: 'var(--text-muted, #64748b)', fontSize: '0.78rem', minHeight: '26px', margin: '0 0 8px', textAlign: 'center', lineHeight: 1.35 }}>
                      {plan.description || `Ideal for eager young readers exploring stories.`}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '3px', margin: '0 0 12px' }}>
                      <span style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--maroon, #740f28)' }}>
                        ₹{plan.price}
                      </span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted, #64748b)' }}>
                        / {plan.duration_months} mo
                      </span>
                    </div>

                    {/* Feature Checklist */}
                    <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-main, #1e293b)' }}>
                        <Check size={15} color="var(--maroon, #740f28)" />
                        <span><strong>{plan.book_limit} books</strong> at a time</span>
                      </li>
                      <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-main, #1e293b)' }}>
                        <Check size={15} color="var(--maroon, #740f28)" />
                        <span>Unlimited book swaps</span>
                      </li>
                      <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-main, #1e293b)' }}>
                        <Check size={15} color="var(--maroon, #740f28)" />
                        <span>Doorstep delivery available</span>
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
                            padding: '8px',
                            borderRadius: '8px',
                            border: '1.5px solid #16a34a',
                            backgroundColor: '#f0fdf4',
                            color: '#16a34a',
                            fontWeight: 700,
                            fontSize: '0.82rem',
                            cursor: 'default',
                          }}
                        >
                          Current Plan
                        </button>
                      ) : (
                        <button
                          onClick={() => handleSubscribe(plan)}
                          disabled={subscribingId === plan.id}
                          type="button"
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '8px',
                            border: 'none',
                            backgroundColor: isFeatured ? 'var(--maroon, #740f28)' : 'var(--navy, #061446)',
                            color: '#ffffff',
                            fontWeight: 700,
                            fontSize: '0.85rem',
                            cursor: subscribingId === plan.id ? 'not-allowed' : 'pointer',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                          }}
                        >
                          {subscribingId === plan.id ? 'Processing...' : user ? 'Subscribe' : 'Join Now'}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* 2. Flexible Service Modes Section (Below Plans, 32px gap) */}
        <section aria-labelledby="react-service-modes-heading" style={{ marginTop: '32px' }}>
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <h2 id="react-service-modes-heading" style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 4px' }}>
              Flexible Service Modes
            </h2>
            <p style={{ color: 'var(--text-muted, #64748b)', fontSize: '0.925rem', lineHeight: 1.45, margin: 0 }}>
              Choose how you'd like your books delivered — in person or to your doorstep.
            </p>
          </div>

          <div className="bb-react-modes-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'stretch' }}>
            {/* Mode 1: Offline Self-Pickup */}
            <article className="bb-mode-card" style={{ background: '#ffffff', border: '1px solid var(--border-color, #e5e7eb)', borderRadius: '12px', padding: '16px 20px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>Offline (Self-Pickup)</h3>
                <span className="bb-mode-badge bb-badge-offline" style={{ fontSize: '0.75rem', fontWeight: 800, padding: '3px 8px', borderRadius: '6px', backgroundColor: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0' }}>INCLUDED FREE</span>
              </div>
              <p style={{ color: 'var(--text-muted, #4b5563)', fontSize: '0.95rem', lineHeight: 1.5, margin: '0 0 12px' }}>
                Visit our welcoming library to browse curated shelves, participate in quiet reading, and pick up books in person.
              </p>
              <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.9rem', lineHeight: 1.45, color: '#374151' }}>
                  <MapPin size={16} color="var(--maroon, #740f28)" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <span><strong>Address:</strong> Velachery, Chennai - 600042</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.9rem', lineHeight: 1.45, color: '#374151' }}>
                  <Check size={16} color="var(--status-green, #059669)" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <span><strong>Logistics fee:</strong> Free (included in plan)</span>
                </div>
              </div>
            </article>

            {/* Mode 2: Online Doorstep Delivery */}
            <article className="bb-mode-card" style={{ background: '#ffffff', border: '1px solid var(--border-color, #e5e7eb)', borderRadius: '12px', padding: '16px 20px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>Online (Doorstep Delivery)</h3>
                <span className="bb-mode-badge bb-badge-online" style={{ fontSize: '0.75rem', fontWeight: 800, padding: '3px 8px', borderRadius: '6px', backgroundColor: '#eff6ff', color: '#1e40af', border: '1px solid #bfdbfe' }}>+₹150/MONTH</span>
              </div>
              <p style={{ color: 'var(--text-muted, #4b5563)', fontSize: '0.95rem', lineHeight: 1.5, margin: '0 0 12px' }}>
                Enjoy fixed weekly book deliveries and returns right to your home in Chennai.
              </p>
              <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.9rem', lineHeight: 1.45, color: '#374151' }}>
                  <Truck size={16} color="var(--maroon, #740f28)" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <span><strong>Area:</strong> Greater Chennai City limits</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.9rem', lineHeight: 1.45, color: '#374151' }}>
                  <Calendar size={16} color="var(--maroon, #740f28)" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <span><strong>Schedule:</strong> Every Wednesday &amp; Saturday</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.9rem', lineHeight: 1.45, color: '#374151' }}>
                  <Sparkles size={16} color="var(--maroon, #740f28)" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <span><strong>Logistics fee:</strong> +₹150 / month</span>
                </div>
              </div>
            </article>
          </div>
        </section>
      </div>

      <style>{`
        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
        }
        @media (max-width: 767px) {
          .bb-react-modes-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </>
  );
};
