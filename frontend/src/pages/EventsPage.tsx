import React, { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Clock, ChevronLeft, ChevronRight, X } from 'lucide-react';
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
  location?: string;
  image_path?: string;
  is_active: number;
}

const getCategoryLabel = (category?: string) => {
  if (!category) return 'Event';
  const c = category.toLowerCase();
  if (c === 'contest' || c === 'contests') return 'Contest';
  if (c === 'reading-circle' || c === 'reading_circle' || c === 'reading-circles') return 'Reading Circle';
  if (c === 'workshop' || c === 'workshops') return 'Workshop';
  return 'Event';
};

export const EventsPage: React.FC = () => {
  const { showToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const view = (searchParams.get('view') === 'past' ? 'past' : 'current') as 'current' | 'past';
  const setView = (newView: 'current' | 'past') => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('view', newView);
      return next;
    });
  };
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [calendarDate, setCalendarDate] = useState<Date>(new Date());
  const [registerEvent, setRegisterEvent] = useState<EventItem | null>(null);

  // Form registration state
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regSeats, setRegSeats] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['events', view, selectedCategory, selectedDate],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (view) params.set('view', view);
      if (selectedCategory) params.set('type', selectedCategory);
      if (selectedDate) params.set('date', selectedDate);
      const res = await apiGet(`/api/v1/events?${params.toString()}`);
      if (!res.ok) throw new Error(res.error?.message || 'Failed to load events');
      return res.data as { events: EventItem[]; count: number; current_count?: number; past_count?: number };
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

  const events = data?.events || [];
  const currentCount = data?.current_count ?? (view === 'current' ? events.length : 0);
  const pastCount = data?.past_count ?? (view === 'past' ? events.length : 0);

  // Calendar calculations
  const year = calendarDate.getFullYear();
  const month = calendarDate.getMonth();
  const monthLabel = calendarDate.toLocaleString('default', { month: 'long', year: 'numeric' });
  const todayStr = new Date().toISOString().slice(0, 10);

  const calendarDays = useMemo(() => {
    const firstDay = new Date(year, month, 1).getDay(); // 0 is Sun
    const adjustedFirstDay = (firstDay + 6) % 7; // 0 is Mon
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const days: (number | null)[] = [];
    for (let i = 0; i < adjustedFirstDay; i++) {
      days.push(null);
    }
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }
    while (days.length % 7 !== 0) {
      days.push(null);
    }
    return days;
  }, [year, month]);

  const handlePrevMonth = () => {
    setCalendarDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCalendarDate(new Date(year, month + 1, 1));
  };

  return (
    <>
      <SEO
        title="Events & Reading Circles | Book Buddy Lending Library"
        description="Discover weekend reading circles, creative writing contests, author interactions, and workshops held at Book Buddy."
      />

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 20px 60px', boxSizing: 'border-box' }}>
        {/* Top Header */}
        <header style={{ marginBottom: '24px' }}>
          <h1 style={{ fontFamily: 'var(--font-heading, "Fraunces", Georgia, serif)', fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 16px' }}>
            Events &amp; Contests
          </h1>

          {/* Top category buttons in one row directly under title */}
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
            {[
              { slug: '', label: 'All' },
              { slug: 'upcoming', label: 'Events' },
              { slug: 'reading-circle', label: 'Reading Circles' },
              { slug: 'contest', label: 'Contests' },
            ].map((cat) => {
              const active = selectedCategory === cat.slug;
              return (
                <button
                  key={cat.slug}
                  onClick={() => setSelectedCategory(cat.slug)}
                  type="button"
                  style={{
                    padding: '8px 18px',
                    borderRadius: '20px',
                    border: active ? '1.5px solid var(--maroon, #740f28)' : '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: active ? 'var(--maroon-tint, rgba(116, 15, 40, 0.08))' : '#ffffff',
                    color: active ? 'var(--maroon, #740f28)' : 'var(--text-main, #1e293b)',
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {cat.label}
                </button>
              );
            })}
          </div>
        </header>

        {/* Layout container */}
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 320px) minmax(0, 1fr)', gap: '28px', alignItems: 'start' }}>
          {/* Left Column: Calendar */}
          <aside style={{ display: 'flex', flexDirection: 'column', gap: 0, alignSelf: 'start' }}>
            {/* Calendar widget */}
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '14px',
                border: '1px solid var(--border-color, #e2e8f0)',
                padding: '18px',
                boxShadow: '0 2px 8px rgba(10, 36, 114, 0.04)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--navy, #061446)', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <Calendar size={16} /> Event Calendar
                </span>
                {selectedDate && (
                  <button
                    onClick={() => setSelectedDate(null)}
                    type="button"
                    style={{ background: 'none', border: 'none', color: 'var(--maroon, #740f28)', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', padding: 0 }}
                  >
                    Show all days
                  </button>
                )}
              </div>

              {/* Month Controls */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <button
                  onClick={handlePrevMonth}
                  type="button"
                  aria-label="Previous month"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '32px',
                    height: '32px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#ffffff',
                    cursor: 'pointer',
                    color: 'var(--navy, #061446)',
                  }}
                >
                  <ChevronLeft size={16} />
                </button>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: 0 }}>
                  {monthLabel}
                </h3>
                <button
                  onClick={handleNextMonth}
                  type="button"
                  aria-label="Next month"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '32px',
                    height: '32px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color, #e2e8f0)',
                    backgroundColor: '#ffffff',
                    cursor: 'pointer',
                    color: 'var(--navy, #061446)',
                  }}
                >
                  <ChevronRight size={16} />
                </button>
              </div>

              {/* 7-column equal square grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px', textAlign: 'center' }}>
                {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => (
                  <span key={i} style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-subtle, #94a3b8)', padding: '4px 0' }}>
                    {d}
                  </span>
                ))}
                {calendarDays.map((day, idx) => {
                  if (day === null) {
                    return <div key={`empty-${idx}`} style={{ aspectRatio: '1 / 1' }} />;
                  }
                  const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                  const isSelected = selectedDate === dateStr;
                  const isToday = dateStr === todayStr;
                  const hasEvents = events.some((e) => e.event_date === dateStr);

                  return (
                    <button
                      key={dateStr}
                      onClick={() => setSelectedDate(isSelected ? null : dateStr)}
                      type="button"
                      style={{
                        aspectRatio: '1 / 1',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRadius: '6px',
                        border: isToday ? '1.5px solid var(--maroon, #740f28)' : 'none',
                        backgroundColor: isSelected
                          ? 'var(--navy, #061446)'
                          : hasEvents
                          ? 'var(--gold-tint, #fef9c3)'
                          : 'transparent',
                        color: isSelected
                          ? '#ffffff'
                          : isToday
                          ? 'var(--maroon, #740f28)'
                          : 'var(--text-main, #1e293b)',
                        fontWeight: isSelected || hasEvents || isToday ? 700 : 500,
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                        padding: 0,
                        position: 'relative',
                      }}
                    >
                      <span>{day}</span>
                      {hasEvents && (
                        <span
                          style={{
                            display: 'block',
                            width: '4px',
                            height: '4px',
                            borderRadius: '50%',
                            backgroundColor: isSelected ? '#ffffff' : 'var(--maroon, #740f28)',
                            marginTop: '2px',
                          }}
                        />
                      )}
                    </button>
                  );
                })}
              </div>

              {selectedDate ? (
                <div style={{ marginTop: '14px', textAlign: 'center' }}>
                  <button
                    onClick={() => setSelectedDate(null)}
                    type="button"
                    style={{
                      background: '#ffffff',
                      border: '1px solid var(--border-color, #e2e8f0)',
                      borderRadius: '6px',
                      padding: '4px 12px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: 'var(--maroon, #740f28)',
                      cursor: 'pointer',
                    }}
                  >
                    &times; Show all days
                  </button>
                </div>
              ) : (
                <p style={{ fontSize: '0.75rem', color: 'var(--text-subtle, #94a3b8)', textAlign: 'center', margin: '12px 0 0' }}>
                  Click any date to filter events
                </p>
              )}
            </div>

          </aside>

          {/* Right Column: Events Content Area */}
          <section id="events-tabpanel" role="tabpanel">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '16px',
                flexWrap: 'wrap',
                marginBottom: '20px',
              }}
            >
              <div>
                <h2 style={{ fontFamily: 'var(--font-heading, "Fraunces", Georgia, serif)', fontSize: '1.5rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: 0 }}>
                  {view === 'past' ? 'Past Events & Contests' : 'Upcoming Events & Contests'}
                </h2>
                {selectedDate && (
                  <p style={{ fontFamily: 'var(--font-body, "Nunito", sans-serif)', fontSize: '0.85rem', color: 'var(--maroon, #740f28)', fontWeight: 600, margin: '6px 0 0' }}>
                    Filtered for date: {selectedDate} —{' '}
                    <button
                      onClick={() => setSelectedDate(null)}
                      type="button"
                      style={{ background: 'none', border: 'none', color: 'var(--navy, #061446)', textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
                    >
                      Show all days
                    </button>
                  </p>
                )}
              </div>

              {/* Compact Segmented Control (Pill Toggle) */}
              <div
                className="events-view-switcher"
                role="tablist"
                aria-label="Event timeframes"
                onKeyDown={(e) => {
                  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    setView(view === 'current' ? 'past' : 'current');
                  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                    e.preventDefault();
                    setView(view === 'current' ? 'past' : 'current');
                  }
                }}
              >
                <button
                  onClick={() => setView('current')}
                  type="button"
                  role="tab"
                  className={`events-view-tab ${view !== 'past' ? 'is-active' : ''}`}
                  aria-selected={view !== 'past'}
                  tabIndex={view !== 'past' ? 0 : -1}
                >
                  <span>Current &amp; Upcoming</span>
                  <span className="count-badge">{currentCount}</span>
                </button>
                <button
                  onClick={() => setView('past')}
                  type="button"
                  role="tab"
                  className={`events-view-tab ${view === 'past' ? 'is-active' : ''}`}
                  aria-selected={view === 'past'}
                  tabIndex={view === 'past' ? 0 : -1}
                >
                  <span>Past Events</span>
                  <span className="count-badge">{pastCount}</span>
                </button>
              </div>
            </div>

            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>Loading events...</div>
            ) : events.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: '4rem 2rem',
                  backgroundColor: '#ffffff',
                  borderRadius: '12px',
                  border: '1px dashed var(--border-color, #e2e8f0)',
                }}
              >
                <Calendar size={36} color="var(--navy, #061446)" style={{ margin: '0 auto 12px', opacity: 0.4 }} />
                <h3 style={{ fontSize: '1.15rem', color: 'var(--navy, #061446)', margin: '0 0 6px' }}>No events found</h3>
                <p style={{ color: 'var(--text-muted)', margin: '0 0 16px', fontSize: '0.875rem' }}>
                  {selectedDate
                    ? `There are no scheduled events on ${selectedDate}.`
                    : view === 'past'
                    ? 'No past events found in this category.'
                    : 'New upcoming events and contests will be posted here soon.'}
                </p>
                <button
                  onClick={() => {
                    setSelectedCategory('');
                    setSelectedDate(null);
                  }}
                  type="button"
                  style={{
                    backgroundColor: 'var(--navy, #061446)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '8px 18px',
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                  }}
                >
                  View All Activities
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {events.map((evt) => {
                  const badgeLabel = getCategoryLabel(evt.category);
                  return (
                    <article
                      key={evt.id}
                      style={{
                        backgroundColor: '#ffffff',
                        borderRadius: '12px',
                        border: '1px solid var(--border-color, #e2e8f0)',
                        padding: '24px',
                        boxShadow: '0 2px 10px rgba(10, 36, 114, 0.04)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 800,
                            backgroundColor: 'var(--navy-tint, rgba(6, 20, 70, 0.08))',
                            color: 'var(--navy, #061446)',
                            padding: '4px 10px',
                            borderRadius: '6px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.04em',
                          }}
                        >
                          {badgeLabel}
                        </span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                          <Calendar size={14} />
                          <span>{evt.event_date}</span>
                        </div>
                      </div>

                      <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: 0 }}>
                        {evt.title}
                      </h3>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        {evt.event_time && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                            <Clock size={14} /> {evt.event_time}
                          </span>
                        )}
                        {evt.location && (
                          <span>&bull; {evt.location}</span>
                        )}
                      </div>

                      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5, margin: 0 }}>
                        {evt.description || 'Join us for an inspiring session at Book Buddy.'}
                      </p>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '14px', borderTop: '1px solid var(--border-color, #e2e8f0)' }}>
                        <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>
                          {evt.fee ? `₹${evt.fee} / seat` : 'Free Admission'}
                        </span>

                        {view === 'current' ? (
                          <button
                            onClick={() => setRegisterEvent(evt)}
                            type="button"
                            className="btn-book-event"
                          >
                            {getCategoryLabel(evt.category) === 'Contest' ? 'Join contest \u2192' : 'Register \u2192'}
                          </button>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', fontStyle: 'italic' }}>
                            Completed on {evt.event_date}
                          </span>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </div>

        {/* Registration Modal */}
        {registerEvent && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(6, 20, 70, 0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 9999,
              padding: '16px',
            }}
          >
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '16px',
                maxWidth: '480px',
                width: '100%',
                padding: '24px',
                position: 'relative',
                boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
              }}
            >
              <button
                onClick={() => setRegisterEvent(null)}
                type="button"
                style={{
                  position: 'absolute',
                  top: '16px',
                  right: '16px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                }}
              >
                <X size={20} />
              </button>

              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 8px' }}>
                Register for {registerEvent.title}
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0 0 20px' }}>
                {registerEvent.event_date} {registerEvent.event_time ? `at ${registerEvent.event_time}` : ''}
              </p>

              <form onSubmit={handleRegisterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--navy)', marginBottom: '4px' }}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.9rem',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--navy)', marginBottom: '4px' }}>
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.9rem',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--navy)', marginBottom: '4px' }}>
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.9rem',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--navy)', marginBottom: '4px' }}>
                    Seats
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={regSeats}
                    onChange={(e) => setRegSeats(Number(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.9rem',
                    }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    backgroundColor: 'var(--navy, #061446)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '12px',
                    fontWeight: 700,
                    fontSize: '0.95rem',
                    cursor: isSubmitting ? 'not-allowed' : 'pointer',
                    marginTop: '8px',
                  }}
                >
                  {isSubmitting ? 'Registering...' : 'Confirm Registration'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
