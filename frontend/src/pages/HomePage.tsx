import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Icon } from '../components/ui/Icon';
import { SEO } from '../components/common/SEO';
import { BookCard, Book } from '../components/books/BookCard';
import { apiGet } from '../api/client';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [keyword, setKeyword] = useState('');

  // Fetch featured / new books
  const { data: booksData } = useQuery({
    queryKey: ['featured-books'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/books?page_size=8');
      return res.data?.books as Book[];
    },
  });

  // Fetch upcoming events
  const { data: eventsData } = useQuery({
    queryKey: ['upcoming-events-home'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/events?view=current');
      return (res.data?.events || []).slice(0, 3);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (keyword.trim()) {
      navigate(`/library?q=${encodeURIComponent(keyword.trim())}`);
    } else {
      navigate('/library');
    }
  };

  const featuredBooks = booksData || [];
  const upcomingEvents = eventsData || [];

  return (
    <>
      <SEO
        title="BookBuddy | Children Lending Library & Reading Community Chennai"
        description="Discover thousands of curated books for kids, teens, and families. Flexible lending plans with doorstep delivery in Saligramam and surrounding areas."
      />

      {/* Hero Section */}
      <section
        style={{
          background: 'linear-gradient(135deg, var(--navy-dark, #040d2e) 0%, var(--navy, #061446) 60%, #152c6e 100%)',
          color: '#ffffff',
          padding: '4.5rem 1.5rem 5.5rem',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ maxWidth: '1160px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 2 }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(255, 255, 255, 0.12)',
              color: '#fde047',
              fontSize: '0.8rem',
              fontWeight: 800,
              padding: '6px 16px',
              borderRadius: '20px',
              textTransform: 'uppercase',
              letterSpacing: '0.6px',
              marginBottom: '20px',
              backdropFilter: 'blur(4px)',
            }}
          >
            <Icon name="sparkle" size={14} /> Saligramam, Chennai Lending Library
          </span>

          <h1
            style={{
              fontSize: 'clamp(2.2rem, 5vw, 3.4rem)',
              fontWeight: 900,
              lineHeight: 1.15,
              margin: '0 auto 18px',
              maxWidth: '840px',
              letterSpacing: '-0.5px',
            }}
          >
            A Lending Library for Curious Young Minds
          </h1>

          <p
            style={{
              fontSize: 'clamp(1rem, 2vw, 1.2rem)',
              color: 'rgba(255, 255, 255, 0.85)',
              maxWidth: '680px',
              margin: '0 auto 32px',
              lineHeight: 1.6,
            }}
          >
            Discover thousands of captivating illustrated picture books, timeless classics, and young adult novels with doorstep exchanges across Chennai.
          </p>

          {/* Quick Search */}
          <form
            onSubmit={handleSearch}
            style={{
              maxWidth: '580px',
              margin: '0 auto 24px',
              display: 'flex',
              backgroundColor: '#ffffff',
              borderRadius: '50px',
              padding: '6px 8px 6px 20px',
              boxShadow: '0 12px 36px rgba(0,0,0,0.3)',
            }}
          >
            <input
              type="search"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Search books by title, author, or keyword..."
              style={{
                flex: 1,
                border: 'none',
                outline: 'none',
                fontSize: '0.95rem',
                color: 'var(--text-main)',
                backgroundColor: 'transparent',
              }}
            />
            <button
              type="submit"
              style={{
                backgroundColor: 'var(--maroon, #740f28)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '50px',
                padding: '10px 22px',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <Icon name="magnifying-glass" size={16} />
              <span>Explore</span>
            </button>
          </form>

          {/* Quick action buttons */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <Link
              to="/library"
              style={{
                padding: '11px 24px',
                backgroundColor: 'var(--maroon, #740f28)',
                color: '#ffffff',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.925rem',
                textDecoration: 'none',
              }}
            >
              Browse Catalogue
            </Link>
            <Link
              to="/membership"
              style={{
                padding: '11px 24px',
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                color: '#ffffff',
                border: '1.5px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.925rem',
                textDecoration: 'none',
                backdropFilter: 'blur(4px)',
              }}
            >
              Membership Plans
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section style={{ maxWidth: '1160px', margin: '-30px auto 4rem', padding: '0 1.5rem', position: 'relative', zIndex: 10 }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '18px',
          }}
        >
          {([
            { icon: 'book-open' as const, title: 'Thousands of Books', desc: 'Age-appropriate curated picture books, fiction, and non-fiction.' },
            { icon: 'truck' as const, title: 'Doorstep Delivery', desc: 'Regular book drops and collections directly to your doorstep in Chennai.' },
            { icon: 'calendar-blank' as const, title: 'Weekend Circles', desc: 'Storytelling circles, literary contests, and creative sessions.' },
            { icon: 'seal-check' as const, title: 'Hassle-Free Swaps', desc: 'Exchange titles as often as your reader finishes them.' },
          ]).map((card, i) => {
            return (
              <div
                key={i}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '14px',
                  padding: '24px 20px',
                  boxShadow: '0 8px 24px rgba(10, 36, 114, 0.08)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    backgroundColor: 'var(--navy-tint, rgba(6, 20, 70, 0.06))',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '14px',
                    color: 'var(--navy, #061446)',
                  }}
                >
                  <Icon name={card.icon} size={22} weight="duotone" aria-hidden="true" />
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--navy)', margin: '0 0 6px' }}>{card.title}</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.5 }}>{card.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Featured Books Section */}
      {featuredBooks.length > 0 && (
        <section style={{ maxWidth: '1280px', margin: '0 auto 5rem', padding: '0 1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '24px' }}>
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--maroon)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Curated Selection
              </span>
              <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--navy)', margin: '4px 0 0' }}>
                Popular on the Shelves
              </h2>
            </div>
            <Link
              to="/library"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                color: 'var(--maroon, #740f28)',
                fontWeight: 700,
                fontSize: '0.9rem',
                textDecoration: 'none',
              }}
            >
              <span>View Full Catalogue</span>
              <Icon name="arrow-right" size={16} />
            </Link>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))',
              gap: '16px',
            }}
          >
            {featuredBooks.slice(0, 6).map((book) => (
              <BookCard key={book.id} book={book} isWishlisted={false} onToggleWishlist={() => {}} />
            ))}
          </div>
        </section>
      )}

      {/* Upcoming Events Highlights */}
      {upcomingEvents.length > 0 && (
        <section style={{ backgroundColor: 'var(--surface-body, #f8fafc)', padding: '4.5rem 1.5rem', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ maxWidth: '1160px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '28px' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--maroon)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Community Gatherings
                </span>
                <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--navy)', margin: '4px 0 0' }}>
                  Upcoming Library Events
                </h2>
              </div>
              <Link
                to="/events"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: 'var(--maroon, #740f28)',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  textDecoration: 'none',
                }}
              >
                <span>View All Events</span>
                <Icon name="arrow-right" size={16} />
              </Link>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
              {upcomingEvents.map((evt: any) => (
                <div
                  key={evt.id}
                  style={{
                    backgroundColor: '#ffffff',
                    borderRadius: '12px',
                    padding: '22px',
                    boxShadow: '0 4px 18px rgba(10, 36, 114, 0.05)',
                    borderLeft: '4px solid var(--maroon, #740f28)',
                  }}
                >
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--navy)', marginBottom: '8px' }}>
                    {evt.event_date} {evt.event_time && `• ${evt.event_time}`}
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy)', margin: '0 0 8px' }}>{evt.title}</h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: '0 0 16px' }}>
                    {evt.description || 'Interactive storytelling circle.'}
                  </p>
                  <Link
                    to="/events"
                    style={{
                      fontSize: '0.825rem',
                      fontWeight: 700,
                      color: 'var(--maroon)',
                      textDecoration: 'none',
                    }}
                  >
                    Register Free →
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
};
