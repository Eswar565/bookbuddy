import React from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Headphones, ExternalLink, Calendar } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { SEO } from '../components/common/SEO';
import { apiGet } from '../api/client';
import { Publication } from './NewspaperPage';

export const PodcastPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const sort = searchParams.get('sort') === 'desc' ? 'desc' : 'asc';

  const { data, isLoading } = useQuery({
    queryKey: ['podcasts-data', sort],
    queryFn: async () => {
      const res = await apiGet(`/api/v1/media?kind=podcast&sort=${sort}`);
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch podcasts');
      return (res.data?.items || []) as (Publication & { embed_url?: string; audio_url?: string; episode_label?: string; ep_num?: number })[];
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
          <header style={{ marginBottom: '24px' }}>
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

          {/* Sort Controls */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: '24px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '10px' }}>
              <label
                htmlFor="podcast-sort"
                style={{
                  fontFamily: 'var(--font-body, "Nunito", sans-serif)',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  color: 'var(--color-text, #061446)',
                  margin: 0,
                  whiteSpace: 'nowrap',
                }}
              >
                Sort by:
              </label>
              <select
                id="podcast-sort"
                className="filter-select"
                value={sort}
                onChange={(e) => setSearchParams({ sort: e.target.value })}
                style={{
                  width: 'auto',
                  minWidth: '160px',
                  height: '40px',
                  minHeight: '40px',
                  padding: '0 32px 0 14px',
                  fontSize: '0.875rem',
                }}
              >
                <option value="asc">Oldest first</option>
                <option value="desc">Newest first</option>
              </select>
            </div>
          </div>

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
              Loading podcast episodes...
            </div>
          ) : items.length === 0 ? (
            <div
              style={{
                backgroundColor: 'var(--color-surface, #ffffff)',
                border: '1px solid var(--color-border, #e5e7eb)',
                borderRadius: '12px',
                padding: '48px 24px',
                textAlign: 'center',
              }}
            >
              <h3 style={{ fontFamily: 'var(--font-heading, "Fraunces", serif)', color: 'var(--navy, #061446)', margin: '0 0 8px' }}>
                No podcast episodes found
              </h3>
              <p style={{ fontFamily: 'var(--font-body, "Nunito", sans-serif)', color: 'var(--ink-subtle, #6b7280)', margin: 0 }}>
                We are preparing exciting new audio adventures. Check back soon!
              </p>
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                gap: '24px',
                alignItems: 'stretch',
              }}
            >
              {items.map((item, idx) => (
                <article
                  key={item.id}
                  style={{
                    backgroundColor: 'var(--color-surface, #ffffff)',
                    border: '1px solid var(--color-border, #e5e7eb)',
                    borderRadius: '12px',
                    boxShadow: '0 4px 16px rgba(43, 27, 32, 0.05)',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                    boxSizing: 'border-box',
                  }}
                >
                  {/* Cover Art ONLY if present */}
                  {item.cover_path && (
                    <div
                      style={{
                        width: '100%',
                        aspectRatio: '16/9',
                        borderRadius: '12px',
                        overflow: 'hidden',
                        marginBottom: '12px',
                        flexShrink: 0,
                      }}
                    >
                      <img
                        src={item.cover_path}
                        alt={item.title}
                        style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                        loading="lazy"
                      />
                    </div>
                  )}

                  {/* Meta row: pill on left, date on right */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '12px',
                    }}
                  >
                    <span
                      style={{
                        fontFamily: 'var(--font-body, "Nunito", sans-serif)',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        color: '#1e40af',
                        backgroundColor: '#eff6ff',
                        padding: '3px 10px',
                        borderRadius: '12px',
                        border: '1px solid #bfdbfe',
                        display: 'inline-block',
                      }}
                    >
                      {(item.episode_label || item.edition || `EPISODE ${item.ep_num || idx + 1}`).toUpperCase()}
                    </span>
                    {item.published_on && (
                      <span
                        style={{
                          fontFamily: 'var(--font-body, "Nunito", sans-serif)',
                          fontSize: '0.8rem',
                          color: 'var(--ink-subtle, #6b7280)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        <Calendar size={13} /> {item.published_on}
                      </span>
                    )}
                  </div>

                  <h2
                    style={{
                      fontFamily: 'var(--font-heading, "Fraunces", Georgia, serif)',
                      fontSize: '1.25rem',
                      fontWeight: 700,
                      color: 'var(--color-text, #061446)',
                      margin: '0 0 10px 0',
                      lineHeight: 1.35,
                    }}
                  >
                    {item.title}
                  </h2>

                  <p
                    style={{
                      fontFamily: 'var(--font-body, "Nunito", sans-serif)',
                      fontSize: '0.875rem',
                      color: 'var(--ink-subtle, #4b5563)',
                      lineHeight: 1.5,
                      margin: '0 0 16px 0',
                      flexGrow: 1,
                    }}
                  >
                    {item.description || 'A heartwarming audio story and literary adventure for children.'}
                  </p>

                  {/* Audio Player / Embed pinned to bottom */}
                  <div style={{ marginTop: 'auto', width: '100%' }}>
                    {item.embed_url ? (
                      <div style={{ borderRadius: '8px', overflow: 'hidden', marginBottom: '8px' }}>
                        <iframe
                          src={item.embed_url.includes('spotify.com/episode') && !item.embed_url.includes('/embed/') ? item.embed_url.replace('/episode/', '/embed/episode/') : item.embed_url}
                          title={`${item.title} player`}
                          width="100%"
                          height="152"
                          style={{ borderRadius: '8px', border: 0, display: 'block' }}
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
                          fontFamily: 'var(--font-body, "Nunito", sans-serif)',
                          fontWeight: 700,
                          fontSize: '0.875rem',
                          textDecoration: 'none',
                          boxSizing: 'border-box',
                        }}
                      >
                        <Headphones size={16} /> Listen on Spotify <ExternalLink size={14} />
                      </a>
                    )}
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
