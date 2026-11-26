import React from 'react';
import { Link } from 'react-router-dom';
import { Newspaper, BookOpen, Radio, ArrowRight } from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../api/client';

export const MediaPage: React.FC = () => {
  const { data } = useQuery({
    queryKey: ['media-hub-counts'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/media');
      if (!res.ok) return null;
      return res.data;
    },
  });

  const newsCount = data?.counts?.newspapers ?? 3;
  const magCount = data?.counts?.magazines ?? 3;
  const podCount = data?.counts?.podcasts ?? 3;

  return (
    <>
      <SEO
        title="Media Hub · Newspapers, Magazines &amp; Podcasts | BookBuddy"
        description="Discover original student newspapers, quarterly literary magazines, and bedtime story podcasts from the Book Buddy community."
      />

      <main style={{ padding: '2.5rem 1rem 4rem', backgroundColor: 'var(--tint, #fdfbf7)', minHeight: '80vh' }}>
        <div style={{ maxWidth: '1140px', margin: '0 auto' }}>
          {/* Header */}
          <header style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 36px' }}>
            <span
              style={{
                display: 'inline-block',
                fontSize: '0.75rem',
                fontWeight: 800,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--maroon, #740f28)',
                backgroundColor: 'rgba(116, 15, 40, 0.08)',
                padding: '4px 14px',
                borderRadius: '20px',
                marginBottom: '10px',
              }}
            >
              Community Publications
            </span>
            <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 8px', lineHeight: 1.25 }}>
              Book Buddy Media Hub
            </h1>
            <p style={{ color: 'var(--ink-subtle, #4b5563)', fontSize: '1rem', lineHeight: 1.55, margin: 0 }}>
              Explore our original student newspapers, curated quarterly magazines, and cozy story podcasts created by and for our vibrant reading community.
            </p>
          </header>

          {/* 3 Large Cards Hub */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '24px',
              marginBottom: '40px',
            }}
          >
            {/* Card 1: Newspapers */}
            <article
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color, #e5e7eb)',
                borderRadius: '12px',
                padding: '32px 26px',
                boxShadow: '0 4px 16px rgba(6, 20, 70, 0.05)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
              }}
            >
              <div
                style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(6, 20, 70, 0.08)',
                  color: 'var(--navy, #061446)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                }}
              >
                <Newspaper size={28} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: 0 }}>
                  Newspapers
                </h2>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    backgroundColor: '#ecfdf5',
                    color: '#065f46',
                    border: '1px solid #a7f3d0',
                    padding: '2px 8px',
                    borderRadius: '12px',
                  }}
                >
                  {newsCount} Editions
                </span>
              </div>
              <p style={{ fontSize: '0.925rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.6, margin: '0 0 24px', flexGrow: 1 }}>
                Student journalism, literary scoops, and young author spotlights in our community newspaper editions. Sorted newest first with easy month/year navigation.
              </p>
              <Link
                to="/newspaper"
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  backgroundColor: 'var(--navy, #061446)',
                  color: '#ffffff',
                  padding: '12px 20px',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  textDecoration: 'none',
                }}
              >
                Read Newspapers <ArrowRight size={16} />
              </Link>
            </article>

            {/* Card 2: Magazines */}
            <article
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color, #e5e7eb)',
                borderRadius: '12px',
                padding: '32px 26px',
                boxShadow: '0 4px 16px rgba(6, 20, 70, 0.05)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
              }}
            >
              <div
                style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(217, 119, 6, 0.12)',
                  color: '#b45309',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                }}
              >
                <BookOpen size={28} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: 0 }}>
                  Magazines
                </h2>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    backgroundColor: '#fffbeb',
                    color: '#b45309',
                    border: '1px solid #fde68a',
                    padding: '2px 8px',
                    borderRadius: '12px',
                  }}
                >
                  {magCount} Issues
                </span>
              </div>
              <p style={{ fontSize: '0.925rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.6, margin: '0 0 24px', flexGrow: 1 }}>
                Quarterly literary digests filled with illustrated adventures, creative writing, poetry, and reader reviews. Featured issue on top with archive of past issues.
              </p>
              <Link
                to="/magazine"
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  backgroundColor: 'var(--maroon, #740f28)',
                  color: '#ffffff',
                  padding: '12px 20px',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  textDecoration: 'none',
                }}
              >
                Browse Magazines <ArrowRight size={16} />
              </Link>
            </article>

            {/* Card 3: Podcasts */}
            <article
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color, #e5e7eb)',
                borderRadius: '12px',
                padding: '32px 26px',
                boxShadow: '0 4px 16px rgba(6, 20, 70, 0.05)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
              }}
            >
              <div
                style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(116, 15, 40, 0.08)',
                  color: 'var(--maroon, #740f28)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                }}
              >
                <Radio size={28} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: 0 }}>
                  Podcasts
                </h2>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    backgroundColor: '#eff6ff',
                    color: '#1e40af',
                    border: '1px solid #bfdbfe',
                    padding: '2px 8px',
                    borderRadius: '12px',
                  }}
                >
                  {podCount} Episodes
                </span>
              </div>
              <p style={{ fontSize: '0.925rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.6, margin: '0 0 24px', flexGrow: 1 }}>
                Audio bedtime stories, literature discussions, and reading tips for parents and young minds. Listen directly through our integrated player.
              </p>
              <Link
                to="/podcasts"
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  backgroundColor: 'var(--navy, #061446)',
                  color: '#ffffff',
                  padding: '12px 20px',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  textDecoration: 'none',
                }}
              >
                Listen to Podcasts <ArrowRight size={16} />
              </Link>
            </article>
          </div>

          {/* Reader Contribution Callout */}
          <div
            style={{
              backgroundColor: '#ffffff',
              border: '1px solid var(--border-color, #e5e7eb)',
              borderRadius: '12px',
              padding: '24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '16px',
            }}
          >
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 4px' }}>
                Have a story, poem, or book review to share?
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--ink-subtle, #4b5563)', margin: 0 }}>
                Our publications regularly feature young writers and community artists.
              </p>
            </div>
            <Link
              to="/contact"
              style={{
                backgroundColor: 'transparent',
                color: 'var(--maroon, #740f28)',
                border: '1.5px solid var(--maroon, #740f28)',
                padding: '8px 18px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 700,
                textDecoration: 'none',
              }}
            >
              Submit a Contribution &rarr;
            </Link>
          </div>
        </div>
      </main>
    </>
  );
};
