import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Eye, Download, Calendar } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { SEO } from '../components/common/SEO';
import { apiGet } from '../api/client';
import { Publication } from './NewspaperPage';

export const MagazinePage: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['magazines-data'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/media?kind=magazine');
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch magazines');
      return (res.data?.items || []) as Publication[];
    },
  });

  const items = data || [];
  const featuredIssue = items[0] || null;
  const pastIssues = items.length > 1 ? items.slice(1) : [];

  return (
    <>
      <SEO
        title="The Magazine Archive · Book Buddy Magazine | BookBuddy"
        description="Explore quarterly literary digests filled with illustrated adventures, creative writing, poetry, and reader reviews from Book Buddy."
      />

      <main style={{ padding: '2.5rem 1rem 4rem', backgroundColor: 'var(--tint, #fdfbf7)', minHeight: '80vh' }}>
        <div style={{ maxWidth: '1140px', margin: '0 auto' }}>
          {/* Breadcrumb */}
          <nav style={{ fontSize: '0.85rem', marginBottom: '16px', color: 'var(--ink-subtle, #6b7280)' }} aria-label="Breadcrumb">
            <Link to="/media" style={{ color: 'var(--navy, #061446)', textDecoration: 'none', fontWeight: 600 }}>
              Media Hub
            </Link>
            <span style={{ margin: '0 6px' }}>/</span>
            <span>Magazines</span>
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
              Publication &amp; Media
            </span>
            <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 6px' }}>
              The <span style={{ color: 'var(--maroon, #740f28)' }}>Magazine</span> Archive
            </h1>
            <p style={{ color: 'var(--ink-subtle, #4b5563)', fontSize: '1rem', margin: 0 }}>
              Celebrating creativity and community through every page of our quarterly digests.
            </p>
          </header>

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
              Loading magazine editions...
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
              <h3 style={{ color: 'var(--navy, #061446)', margin: '0 0 8px' }}>No magazine editions published yet</h3>
              <p style={{ color: 'var(--text-muted)', margin: 0 }}>
                Check back soon for upcoming editions of our literary magazine!
              </p>
            </div>
          ) : (
            <>
              {/* Featured Issue on Top */}
              {featuredIssue && (
                <section
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-color, #e5e7eb)',
                    borderRadius: '12px',
                    padding: '32px 28px',
                    marginBottom: '40px',
                    boxShadow: '0 4px 20px rgba(6, 20, 70, 0.06)',
                  }}
                >
                  <div style={{ display: 'flex', gap: '32px', alignItems: 'center', flexWrap: 'wrap' }}>
                    {/* Cover Preview */}
                    <div
                      style={{
                        width: '240px',
                        minWidth: '200px',
                        aspectRatio: '3/4',
                        backgroundColor: 'var(--tint, #fdfbf7)',
                        borderRadius: '10px',
                        overflow: 'hidden',
                        border: '1px solid var(--border-color, #e5e7eb)',
                        boxShadow: '0 4px 14px rgba(6, 20, 70, 0.08)',
                        flexShrink: 0,
                      }}
                    >
                      {featuredIssue.cover_path ? (
                        <img
                          src={featuredIssue.cover_path}
                          alt={featuredIssue.title}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          loading="lazy"
                        />
                      ) : (
                        <div
                          style={{
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backgroundColor: 'rgba(217, 119, 6, 0.08)',
                            color: '#b45309',
                            padding: '20px',
                            textAlign: 'center',
                          }}
                        >
                          <BookOpen size={44} style={{ marginBottom: '8px' }} />
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase' }}>
                            Literary Magazine
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1, minWidth: '280px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                        <span
                          style={{
                            backgroundColor: 'var(--maroon, #740f28)',
                            color: '#ffffff',
                            fontSize: '0.75rem',
                            fontWeight: 800,
                            textTransform: 'uppercase',
                            letterSpacing: '0.06em',
                            padding: '3px 12px',
                            borderRadius: '20px',
                          }}
                        >
                          Featured Issue
                        </span>
                        <span style={{ fontSize: '0.85rem', color: 'var(--ink-subtle, #6b7280)' }}>
                          {featuredIssue.edition || 'Latest Edition'} · {featuredIssue.published_on || 'Recent'}
                        </span>
                      </div>

                      <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 12px', lineHeight: 1.3 }}>
                        {featuredIssue.title}
                      </h2>

                      <p style={{ fontSize: '0.95rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.6, margin: '0 0 24px' }}>
                        {{ ...featuredIssue }.description || 'A rich quarterly collection featuring student artwork, short fiction, poetry, and book reflections from young readers.'}
                      </p>

                      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                        {featuredIssue.file_path ? (
                          <>
                            <a
                              href={featuredIssue.file_path}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '8px',
                                backgroundColor: 'var(--maroon, #740f28)',
                                color: '#ffffff',
                                padding: '11px 22px',
                                borderRadius: '8px',
                                fontWeight: 700,
                                fontSize: '0.9rem',
                                textDecoration: 'none',
                              }}
                            >
                              <Eye size={16} /> Read Issue &rarr;
                            </a>
                            <a
                              href={featuredIssue.file_path}
                              download
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '8px',
                                backgroundColor: '#ffffff',
                                border: '1px solid var(--border-color, #e5e7eb)',
                                color: 'var(--navy, #061446)',
                                padding: '11px 18px',
                                borderRadius: '8px',
                                fontWeight: 700,
                                fontSize: '0.9rem',
                                textDecoration: 'none',
                              }}
                            >
                              <Download size={16} /> Download PDF
                            </a>
                          </>
                        ) : (
                          <span style={{ fontSize: '0.9rem', color: 'var(--ink-subtle, #6b7280)' }}>
                            Available in library reading room
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </section>
              )}

              {/* Past Issues Grid */}
              {pastIssues.length > 0 && (
                <section>
                  <div style={{ marginBottom: '24px' }}>
                    <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 4px' }}>
                      Past Magazine Issues
                    </h2>
                    <p style={{ color: 'var(--ink-subtle, #6b7280)', fontSize: '0.9rem', margin: 0 }}>
                      Explore previous editions from our community archives.
                    </p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '24px' }}>
                    {pastIssues.map((item) => (
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
                        <div
                          style={{
                            width: '100%',
                            aspectRatio: '16/10',
                            backgroundColor: 'var(--tint, #fdfbf7)',
                            position: 'relative',
                            overflow: 'hidden',
                            borderBottom: '1px solid var(--border-color, #e5e7eb)',
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
                                width: '100%',
                                height: '100%',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                backgroundColor: 'rgba(217, 119, 6, 0.06)',
                                color: '#b45309',
                                padding: '16px',
                              }}
                            >
                              <BookOpen size={36} style={{ marginBottom: '6px' }} />
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                                Magazine Archive
                              </span>
                            </div>
                          )}
                        </div>

                        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span
                              style={{
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                color: '#b45309',
                                backgroundColor: '#fffbeb',
                                padding: '2px 8px',
                                borderRadius: '12px',
                                border: '1px solid #fde68a',
                              }}
                            >
                              {{ ...item }.edition || 'Quarterly Issue'}
                            </span>
                            {item.published_on && (
                              <span style={{ fontSize: '0.8rem', color: 'var(--ink-subtle, #6b7280)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <Calendar size={13} /> {item.published_on}
                              </span>
                            )}
                          </div>

                          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 8px', lineHeight: 1.35 }}>
                            {item.title}
                          </h3>

                          <p style={{ fontSize: '0.85rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.5, margin: '0 0 20px', flexGrow: 1 }}>
                            {item.description || 'A creative edition of the Book Buddy literary magazine.'}
                          </p>

                          <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
                            {item.file_path ? (
                              <>
                                <a
                                  href={item.file_path}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{
                                    flex: 1,
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backgroundColor: 'var(--maroon, #740f28)',
                                    color: '#ffffff',
                                    padding: '9px 14px',
                                    borderRadius: '8px',
                                    fontWeight: 700,
                                    fontSize: '0.85rem',
                                    textDecoration: 'none',
                                  }}
                                >
                                  Read Issue
                                </a>
                                <a
                                  href={item.file_path}
                                  download
                                  style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backgroundColor: '#ffffff',
                                    border: '1px solid var(--border-color, #e5e7eb)',
                                    color: 'var(--navy, #061446)',
                                    padding: '9px 12px',
                                    borderRadius: '8px',
                                    fontWeight: 700,
                                    fontSize: '0.85rem',
                                    textDecoration: 'none',
                                  }}
                                  title="Download PDF"
                                >
                                  <Download size={15} />
                                </a>
                              </>
                            ) : (
                              <button
                                disabled
                                type="button"
                                style={{
                                  flex: 1,
                                  backgroundColor: 'var(--tint, #fdfbf7)',
                                  color: 'var(--text-muted)',
                                  border: '1px solid var(--border-color, #e5e7eb)',
                                  padding: '9px 14px',
                                  borderRadius: '8px',
                                  fontWeight: 700,
                                  fontSize: '0.85rem',
                                }}
                              >
                                In Library Archive
                              </button>
                            )}
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </main>
    </>
  );
};
