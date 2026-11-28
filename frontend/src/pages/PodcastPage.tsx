import React from 'react';
import { Link } from 'react-router-dom';
import { Radio, Headphones, ExternalLink, Calendar } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { SEO } from '../components/common/SEO';
import { apiGet } from '../api/client';
import { Publication } from './NewspaperPage';

export const PodcastPage: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['podcasts-data'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/media?kind=podcast');
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch podcasts');
      return (res.data?.items || []) as (Publication & { embed_url?: string; audio_url?: string })[];
    },
  });

  const items = data || [];

  return (
    <>
      <SEO
        title="The Podcast Archive · Book Buddy Podcasts | BookBuddy"
        description="Listen to bedtime audio stories, literature discussions, and reading journeys for children on Book Buddy podcasts."
      />

      <main style={{ padding: '24px 0 48px', backgroundColor: 'var(--tint, #fdfbf7)', minHeight: '80vh' }}>
        <div style={{ maxWidth: '1200px', width: '100%', margin: '0 auto', padding: '0 24px', boxSizing: 'border-box' }}>
          {/* Breadcrumb */}
          <nav style={{ fontSize: '0.85rem', marginBottom: '16px', color: 'var(--ink-subtle, #6b7280)' }} aria-label="Breadcrumb">
            <Link to="/media" style={{ color: 'var(--navy, #061446)', textDecoration: 'none', fontWeight: 600 }}>
              Media Hub
            </Link>
            <span style={{ margin: '0 6px' }}>/</span>
            <span>Podcasts</span>
          </nav>

          {/* Header */}
          <header style={{ marginBottom: '32px' }}>
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
                marginBottom: '8px',
              }}
            >
              Media &amp; Audio
            </span>
            <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 6px' }}>
              The <span style={{ color: 'var(--maroon, #740f28)' }}>Podcast</span> Archive
            </h1>
            <p style={{ color: 'var(--ink-subtle, #4b5563)', fontSize: '1rem', margin: 0 }}>
              Exploring bedtime stories, literary discussions, and learning journeys for young minds.
            </p>
          </header>

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
              Loading podcast episodes...
            </div>
          ) : items.length === 0 ? (
            <div
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color, #e5e7eb)',
                borderRadius: '12px',
                padding: '48px',
                textAlign: 'center',
              }}
            >
              <h3 style={{ color: 'var(--navy, #061446)', margin: '0 0 8px' }}>No podcast episodes published yet</h3>
              <p style={{ color: 'var(--text-muted)', margin: 0 }}>
                Check back soon for new audio adventures from our storytellers!
              </p>
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                gap: '24px',
              }}
            >
              {items.map((item, idx) => (
                <article
                  key={item.id}
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-color, #e5e7eb)',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    boxShadow: '0 4px 16px rgba(6, 20, 70, 0.05)',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  {/* Artwork / Hero Header */}
                  <div
                    style={{
                      width: '100%',
                      aspectRatio: '16/9',
                      backgroundColor: 'var(--navy, #061446)',
                      position: 'relative',
                      overflow: 'hidden',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {item.cover_path ? (
                      <img
                        src={item.cover_path}
                        alt={item.title}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        loading="lazy"
                      />
                    ) : (
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#ffffff',
                          padding: '20px',
                          textAlign: 'center',
                        }}
                      >
                        <Radio size={40} style={{ color: '#93c5fd', marginBottom: '8px' }} />
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#bfdbfe' }}>
                          Book Buddy Stories
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Details */}
                  <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          color: '#1e40af',
                          backgroundColor: '#eff6ff',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          border: '1px solid #bfdbfe',
                        }}
                      >
                        {item.edition || `EPISODE ${String(idx + 1).padStart(2, '0')}`}
                      </span>
                      {item.published_on && (
                        <span style={{ fontSize: '0.8rem', color: 'var(--ink-subtle, #6b7280)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Calendar size={13} /> {item.published_on}
                        </span>
                      )}
                    </div>

                    <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 8px', lineHeight: 1.35 }}>
                      {item.title}
                    </h2>

                    <p style={{ fontSize: '0.85rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.5, margin: '0 0 16px', flexGrow: 1 }}>
                      {item.description || 'A heartwarming audio story and literary adventure for children.'}
                    </p>

                    {/* Audio Player / Embed */}
                    <div style={{ marginTop: 'auto' }}>
                      {item.embed_url ? (
                        <div style={{ borderRadius: '8px', overflow: 'hidden', marginBottom: '8px' }}>
                          <iframe
                            src={item.embed_url.includes('spotify.com/episode') && !item.embed_url.includes('/embed/') ? item.embed_url.replace('/episode/', '/embed/episode/') : item.embed_url}
                            title={`${item.title} player`}
                            width="100%"
                            height="152"
                            style={{ borderRadius: '8px', border: 0 }}
                            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                            loading="lazy"
                          />
                        </div>
                      ) : item.audio_url || item.file_path ? (
                        <audio
                          controls
                          src={item.audio_url || item.file_path}
                          style={{ width: '100%', height: '36px', marginBottom: '8px' }}
                        />
                      ) : (
                        <a
                          href="https://open.spotify.com"
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px',
                            backgroundColor: 'var(--navy, #061446)',
                            color: '#ffffff',
                            padding: '10px 16px',
                            borderRadius: '8px',
                            fontWeight: 700,
                            fontSize: '0.875rem',
                            textDecoration: 'none',
                          }}
                        >
                          <Headphones size={16} /> Listen on Spotify <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
};
