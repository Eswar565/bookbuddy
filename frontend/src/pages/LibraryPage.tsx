import React from 'react';
import { SEO } from '../components/common/SEO';
import { BookOpen } from 'lucide-react';

export const LibraryPage: React.FC = () => {
  return (
    <>
      <SEO
        title="Book Catalogue"
        description="Browse thousands of books across genres, languages, and age groups in the BookBuddy Library."
      />
      <div style={{ maxWidth: '1280px', margin: '3rem auto', padding: '0 1.5rem' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '2rem',
          }}
        >
          <div>
            <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy)' }}>
              Book Catalogue
            </h1>
            <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              Explore books by language, category, or age group. (React UI shell ready for Phase 2
              API integration)
            </p>
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--surface-card)',
            border: '1px dashed var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '3rem',
            textAlign: 'center',
          }}
        >
          <BookOpen size={48} color="var(--navy)" style={{ margin: '0 auto 1rem' }} />
          <h2 style={{ fontSize: '1.3rem', color: 'var(--navy)', marginBottom: '0.5rem' }}>
            React Catalogue Shell Active
          </h2>
          <p style={{ color: 'var(--text-muted)', maxWidth: '540px', margin: '0 auto 1.5rem' }}>
            The frontend shell, routing, styling tokens, and query client are configured. In Phase
            2, this will connect directly to{' '}
            <code style={{ background: '#eee', padding: '2px 6px', borderRadius: 4 }}>
              /api/v1/books
            </code>{' '}
            for real-time live filtering, pagination, and the borrow cart!
          </p>
          <a
            href="/library/"
            style={{
              display: 'inline-block',
              backgroundColor: 'var(--navy)',
              color: '#fff',
              padding: '0.6rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              fontWeight: 600,
              fontSize: '0.9rem',
            }}
          >
            View Existing Jinja Catalogue (Active)
          </a>
        </div>
      </div>
    </>
  );
};
