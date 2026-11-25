import React from 'react';
import { Link } from 'react-router-dom';
import { SEO } from '../components/common/SEO';
import { BookOpen, Sparkles, Calendar, ArrowRight } from 'lucide-react';

export const HomePage: React.FC = () => {
  return (
    <>
      <SEO
        title="BookBuddy - Where Stories Come Alive"
        description="Explore thousands of books, join community workshops, and cultivate a lifelong love of reading at BookBuddy."
      />

      {/* Hero Section */}
      <section
        style={{
          background: 'linear-gradient(135deg, var(--navy-dark) 0%, var(--navy) 100%)',
          color: 'var(--text-inverse)',
          padding: '4.5rem 1.5rem',
          textAlign: 'center',
        }}
      >
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              padding: '0.4rem 1rem',
              borderRadius: 'var(--radius-pill)',
              fontSize: '0.85rem',
              fontWeight: 600,
              color: 'var(--gold)',
              marginBottom: '1.25rem',
            }}
          >
            <Sparkles size={16} />
            <span>Welcome to Your Community Haven</span>
          </div>
          <h1
            style={{
              fontSize: 'clamp(2.2rem, 5vw, 3.5rem)',
              fontWeight: 800,
              lineHeight: 1.2,
              marginBottom: '1.25rem',
              letterSpacing: '-0.02em',
            }}
          >
            Read, Imagine, and Grow with <span style={{ color: 'var(--gold)' }}>BookBuddy</span>
          </h1>
          <p
            style={{
              fontSize: '1.15rem',
              color: '#cbd5e1',
              lineHeight: 1.6,
              marginBottom: '2rem',
              maxWidth: '650px',
              margin: '0 auto 2rem',
            }}
          >
            Discover our curated collection of books for children, teens, and adults. Borrow online
            or visit our reading spaces to join hands-on literary events.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <Link
              to="/library"
              style={{
                backgroundColor: 'var(--maroon)',
                color: 'var(--text-inverse)',
                padding: '0.85rem 1.75rem',
                borderRadius: 'var(--radius-md)',
                fontWeight: 700,
                fontSize: '1rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: 'var(--shadow-md)',
              }}
            >
              <BookOpen size={20} />
              <span>Explore Catalogue</span>
              <ArrowRight size={18} />
            </Link>
            <Link
              to="/about"
              style={{
                border: '2px solid rgba(255, 255, 255, 0.3)',
                color: 'var(--text-inverse)',
                padding: '0.8rem 1.5rem',
                borderRadius: 'var(--radius-md)',
                fontWeight: 600,
                fontSize: '1rem',
              }}
            >
              Our Story
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Highlights */}
      <section style={{ maxWidth: '1280px', margin: '4rem auto', padding: '0 1.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2
            style={{
              fontSize: '2rem',
              fontWeight: 800,
              color: 'var(--navy)',
              marginBottom: '0.5rem',
            }}
          >
            Why Families & Readers Love BookBuddy
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
            Everything you need to nurture a joyful reading habit
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '2rem',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--surface-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              padding: '2rem',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--navy-tint)',
                color: 'var(--navy)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem',
              }}
            >
              <BookOpen size={26} />
            </div>
            <h3
              style={{
                fontSize: '1.2rem',
                fontWeight: 700,
                color: 'var(--navy)',
                marginBottom: '0.5rem',
              }}
            >
              Curated Book Collection
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.5 }}>
              Handpicked titles in English, Tamil, and Hindi spanning award-winning fiction, STEM,
              picture books, and regional classics.
            </p>
          </div>

          <div
            style={{
              backgroundColor: 'var(--surface-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              padding: '2rem',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--maroon-tint)',
                color: 'var(--maroon)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem',
              }}
            >
              <Sparkles size={26} />
            </div>
            <h3
              style={{
                fontSize: '1.2rem',
                fontWeight: 700,
                color: 'var(--navy)',
                marginBottom: '0.5rem',
              }}
            >
              Convenient Borrowing
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.5 }}>
              Browse online, add to your borrow cart, and choose easy library pickup or reliable
              doorstep delivery.
            </p>
          </div>

          <div
            style={{
              backgroundColor: 'var(--surface-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              padding: '2rem',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--gold-tint)',
                color: 'var(--gold)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem',
              }}
            >
              <Calendar size={26} />
            </div>
            <h3
              style={{
                fontSize: '1.2rem',
                fontWeight: 700,
                color: 'var(--navy)',
                marginBottom: '0.5rem',
              }}
            >
              Events & Workshops
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.5 }}>
              Author meets, storytelling circles, book clubs, and creative workshops designed to
              inspire minds of every age.
            </p>
          </div>
        </div>
      </section>
    </>
  );
};
