import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Clock, Users, X } from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { useToast } from '../context/ToastContext';
import { apiGet, apiPost } from '../api/client';

export interface EventItem {
  id: number;
  title: string;
  description?: string;
  event_date: string;
  event_time?: string;
  category?: string;
  capacity?: number;
  seats_registered?: number;
  seats_left?: number;
  fee?: number;
  is_active: number;
}

export const EventsPage: React.FC = () => {
  const { showToast } = useToast();
  const [view, setView] = useState<'current' | 'past'>('current');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [registerEvent, setRegisterEvent] = useState<EventItem | null>(null);

  // Form registration state
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regSeats, setRegSeats] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['events', view, selectedCategory],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (view) params.set('view', view);
      if (selectedCategory) params.set('type', selectedCategory);
      const res = await apiGet(`/api/v1/events?${params.toString()}`);
      if (!res.ok) throw new Error(res.error?.message || 'Failed to load events');
      return res.data?.events as EventItem[];
    },
  });

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!registerEvent) return;
    setIsSubmitting(true);
    try {
      const res = await apiPost(`/api/v1/events/${registerEvent.id}/register`, {
        name: regName.trim(),
        email: regEmail.trim(),
        phone: regPhone.trim(),
        seats: regSeats,
      });

      if (res.ok) {
        showToast('Registration successful! Check your email for details.', 'success');
        setRegisterEvent(null);
        setRegName('');
        setRegEmail('');
        setRegPhone('');
        setRegSeats(1);
        refetch();
      } else {
        showToast(res.error?.message || 'Could not register for this event.', 'error');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const events = data || [];

  return (
    <>
      <SEO
        title="Events & Reading Circles | BookBuddy Library"
        description="Join weekend storytelling circles, creative author sessions, and literacy contests in Chennai."
      />

      <div style={{ maxWidth: '1160px', margin: '0 auto', padding: '2.5rem 1.5rem 5rem' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: 0 }}>
            Library Events & Circles
          </h1>
          <p style={{ color: 'var(--text-muted, #475569)', marginTop: '0.4rem', fontSize: '0.95rem' }}>
            Inspiring gatherings, storytelling sessions, and weekend workshops for young book lovers.
          </p>
        </div>

        {/* View & Category Toggles */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            marginBottom: '2rem',
            backgroundColor: '#ffffff',
            padding: '14px 18px',
            borderRadius: '12px',
            boxShadow: '0 2px 10px rgba(10, 36, 114, 0.05)',
          }}
        >
          {/* Upcoming vs Past */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setView('current')}
              type="button"
              style={{
                padding: '7px 16px',
                borderRadius: '8px',
                border: view === 'current' ? 'none' : '1px solid var(--border-color)',
                backgroundColor: view === 'current' ? 'var(--navy, #061446)' : '#ffffff',
                color: view === 'current' ? '#ffffff' : 'var(--text-muted)',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              Upcoming Events
            </button>
            <button
              onClick={() => setView('past')}
              type="button"
              style={{
                padding: '7px 16px',
                borderRadius: '8px',
                border: view === 'past' ? 'none' : '1px solid var(--border-color)',
                backgroundColor: view === 'past' ? 'var(--navy, #061446)' : '#ffffff',
                color: view === 'past' ? '#ffffff' : 'var(--text-muted)',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              Past Events
            </button>
          </div>

          {/* Categories */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {[
              { slug: '', label: 'All Activities' },
              { slug: 'reading-circle', label: 'Reading Circles' },
              { slug: 'contest', label: 'Contests' },
              { slug: 'upcoming', label: 'Workshops' },
            ].map((cat) => (
              <button
                key={cat.slug}
                onClick={() => setSelectedCategory(cat.slug)}
                type="button"
                style={{
                  padding: '6px 12px',
                  borderRadius: '20px',
                  border: selectedCategory === cat.slug ? '1.5px solid var(--maroon, #740f28)' : '1px solid var(--border-color)',
                  backgroundColor: selectedCategory === cat.slug ? 'var(--maroon-tint, rgba(116, 15, 40, 0.08))' : '#ffffff',
                  color: selectedCategory === cat.slug ? 'var(--maroon, #740f28)' : 'var(--text-muted)',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Events Grid */}
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '5rem 0', color: 'var(--text-muted)' }}>Loading events...</div>
        ) : events.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '4rem 2rem',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px dashed var(--border-color)',
            }}
          >
            <Calendar size={40} color="var(--navy)" style={{ margin: '0 auto 12px', opacity: 0.5 }} />
            <h3 style={{ fontSize: '1.2rem', color: 'var(--navy)', margin: '0 0 6px' }}>No events scheduled</h3>
            <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.9rem' }}>
              Check back soon or explore our previous reading circles!
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: '20px',
            }}
          >
            {events.map((evt) => (
              <div
                key={evt.id}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '14px',
                  padding: '24px',
                  boxShadow: '0 4px 18px rgba(10, 36, 114, 0.06)',
                  display: 'flex',
                  flexDirection: 'column',
                  borderTop: '4px solid var(--navy, #061446)',
                }}
              >
                {/* Date & Category header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--navy)', fontWeight: 700, fontSize: '0.85rem' }}>
                    <Calendar size={15} />
                    <span>{evt.event_date}</span>
                  </div>
                  {evt.category && (
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        backgroundColor: 'var(--navy-tint)',
                        color: 'var(--navy)',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        textTransform: 'uppercase',
                      }}
                    >
                      {evt.category}
                    </span>
                  )}
                </div>

                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--navy)', margin: '0 0 8px', lineHeight: 1.3 }}>
                  {evt.title}
                </h3>

                {evt.event_time && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '12px' }}>
                    <Clock size={15} />
                    <span>{evt.event_time}</span>
                  </div>
                )}

                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: 1.5, margin: '0 0 20px', flex: 1 }}>
                  {evt.description || 'Join us for an interactive, community-led literacy session.'}
                </p>

                {/* Bottom Row */}
                <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)', paddingTop: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.825rem', color: 'var(--text-subtle)' }}>
                    <Users size={15} />
                    <span>{evt.seats_left !== undefined ? `${evt.seats_left} seats remaining` : 'Open'}</span>
                  </div>

                  {view === 'current' && (
                    <button
                      onClick={() => setRegisterEvent(evt)}
                      type="button"
                      style={{
                        padding: '7px 16px',
                        borderRadius: '8px',
                        border: 'none',
                        backgroundColor: 'var(--maroon, #740f28)',
                        color: '#ffffff',
                        fontWeight: 700,
                        fontSize: '0.825rem',
                        cursor: 'pointer',
                      }}
                    >
                      Register Free
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Event Registration Modal */}
        {registerEvent && (
          <div
            role="dialog"
            aria-modal="true"
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
          >
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '16px',
                width: '100%',
                maxWidth: '440px',
                padding: '24px',
                boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--navy)', margin: 0 }}>
                  Event Registration
                </h3>
                <button
                  onClick={() => setRegisterEvent(null)}
                  type="button"
                  style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '4px' }}
                >
                  <X size={20} />
                </button>
              </div>

              <div style={{ marginBottom: '16px', backgroundColor: 'var(--surface-body)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontWeight: 700, color: 'var(--navy)', fontSize: '0.95rem' }}>{registerEvent.title}</div>
                <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {registerEvent.event_date} {registerEvent.event_time && `• ${registerEvent.event_time}`}
                </div>
              </div>

              <form onSubmit={handleRegisterSubmit}>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Participant Name
                  </label>
                  <input
                    type="text"
                    required
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    placeholder="Full name"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  />
                </div>

                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="email@example.com"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  />
                </div>

                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                    placeholder="+91 9876543210"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  />
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Number of Attendees
                  </label>
                  <select
                    value={regSeats}
                    onChange={(e) => setRegSeats(Number(e.target.value))}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>
                        {n} {n === 1 ? 'attendee' : 'attendees'}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => setRegisterEvent(null)}
                    type="button"
                    style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-color)', backgroundColor: '#fff', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    style={{
                      padding: '8px 20px',
                      borderRadius: '8px',
                      border: 'none',
                      backgroundColor: 'var(--maroon, #740f28)',
                      color: '#ffffff',
                      fontWeight: 700,
                      cursor: isSubmitting ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {isSubmitting ? 'Registering...' : 'Confirm'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
