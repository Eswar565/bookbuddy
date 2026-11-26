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
        title="Membership & Lending Plans | BookBuddy"
        description="Choose a flexible reading plan that fits your family. Enjoy curated children books, unlimited swaps, and doorstep delivery across Chennai."
      />

      <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '1.5rem 1rem 2rem' }}>
        {/* Compact Header */}
        <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 1.25rem' }}>
          <span
            style={{
              display: 'inline-block',
              backgroundColor: 'var(--maroon-tint, rgba(116, 15, 40, 0.08))',
              color: 'var(--maroon, #740f28)',
              fontSize: '0.75rem',
              fontWeight: 800,
              padding: '4px 12px',
              borderRadius: '20px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '6px',
            }}
          >
            Flexible Lending Plans
          </span>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 6px' }}>
            Nurture Lifelong Reading Habits
          </h1>
          <p style={{ color: 'var(--text-muted, #475569)', fontSize: '0.925rem', lineHeight: 1.45, margin: 0 }}>
            Pick the plan that fits your family's reading appetite.
          </p>
        </div>

        {/* Current Subscription Status Banner */}
        {user && activeSubscription && (
          <div
            style={{
              backgroundColor: '#f0fdf4',
              border: '1.5px solid #86efac',
              borderRadius: '10px',
              padding: '10px 16px',
              marginBottom: '1.25rem',
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

        {/* Split Layout: Left = Service Modes, Right = Plan Comparison Table / Cards */}
        <div className="bb-mem-split-layout">
          {/* LEFT: Flexible Service Modes (Stacked Vertically) */}
          <aside className="bb-modes-col" aria-labelledby="react-service-modes-heading">
            <div className="bb-modes-header">
              <h2 className="bb-modes-title" id="react-service-modes-heading">Flexible Service Modes</h2>
              <p className="bb-modes-subtitle">Choose how you'd like your books delivered.</p>
            </div>

            <div className="bb-modes-stack">
              {/* Mode 1: Offline Self-Pickup */}
              <article className="bb-mode-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>Offline (Self-Pickup)</h3>
                  <span className="bb-mode-badge bb-badge-offline">Included Free</span>
                </div>
                <p className="bb-mode-desc">
                  Visit our welcoming library to browse curated shelves and pick up books in person.
                </p>
                <div className="bb-mode-meta">
                  <div className="bb-mode-meta-item">
                    <MapPin size={15} color="var(--maroon, #740f28)" />
                    <span><strong>Address:</strong> Velachery, Chennai - 600042</span>
                  </div>
                  <div className="bb-mode-meta-item">
                    <Check size={15} color="var(--status-green, #059669)" />
                    <span><strong>Logistics fee:</strong> Free (included in plan)</span>
                  </div>
                </div>
              </article>

              {/* Mode 2: Online Doorstep Delivery */}
              <article className="bb-mode-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>Online (Doorstep Delivery)</h3>
                  <span className="bb-mode-badge bb-badge-online">+₹150/month</span>
                </div>
                <p className="bb-mode-desc">
                  Enjoy fixed weekly book deliveries and returns right to your doorstep across Chennai.
                </p>
                <div className="bb-mode-meta">
                  <div className="bb-mode-meta-item">
                    <Truck size={15} color="var(--maroon, #740f28)" />
                    <span><strong>Area:</strong> Greater Chennai City limits</span>
                  </div>
                  <div className="bb-mode-meta-item">
                    <Calendar size={15} color="var(--maroon, #740f28)" />
                    <span><strong>Schedule:</strong> Every Wednesday &amp; Saturday</span>
                  </div>
                  <div className="bb-mode-meta-item">
                    <Sparkles size={15} color="var(--maroon, #740f28)" />
                    <span><strong>Logistics fee:</strong> +₹150 / month</span>
                  </div>
                </div>
              </article>
            </div>
          </aside>

          {/* RIGHT: Compact Plans Grid / Comparison */}
          <section className="bb-plan-table-col" aria-label="Membership plans">
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>Loading plans...</div>
            ) : plans.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>No plans published currently.</div>
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '14px',
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
                        padding: '18px 16px',
                        border: isFeatured ? '2px solid var(--maroon, #740f28)' : '1px solid var(--border-color, #e5e7eb)',
                        boxShadow: isFeatured ? '0 6px 20px rgba(116, 15, 40, 0.1)' : '0 2px 10px rgba(10, 36, 114, 0.04)',
                        display: 'flex',
                        flexDirection: 'column',
                        position: 'relative',
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
                          Best Value
                        </span>
                      )}

                      <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 4px', textAlign: 'center' }}>
                        {plan.name}
                      </h3>
                      <p style={{ color: 'var(--text-muted, #64748b)', fontSize: '0.78rem', minHeight: '30px', margin: '0 0 10px', textAlign: 'center', lineHeight: 1.35 }}>
                        {plan.description || `Ideal for eager young readers exploring stories.`}
                      </p>

                      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '3px', margin: '0 0 14px' }}>
                        <span style={{ fontSize: '1.6rem', fontWeight: 900, color: 'var(--maroon, #740f28)' }}>
                          ₹{plan.price}
                        </span>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted, #64748b)' }}>
                          / {plan.duration_months} mo
                        </span>
                      </div>

                      {/* Feature Checklist */}
                      <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--text-main, #1e293b)' }}>
                          <Check size={15} color="var(--maroon, #740f28)" />
                          <span><strong>{plan.book_limit} books</strong> at a time</span>
                        </li>
                        <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--text-main, #1e293b)' }}>
                          <Check size={15} color="var(--maroon, #740f28)" />
                          <span>Unlimited book swaps</span>
                        </li>
                        <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--text-main, #1e293b)' }}>
                          <Check size={15} color="var(--maroon, #740f28)" />
                          <span>Doorstep pickup available</span>
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
        </div>
      </div>
    </>
  );
};
