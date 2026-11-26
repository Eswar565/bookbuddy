import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Newspaper as NewspaperIcon, Calendar, Eye, Download } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { SEO } from '../components/common/SEO';
import { apiGet } from '../api/client';

export interface Publication {
  id: number;
  title: string;
  description?: string;
  kind: string;
  published_on?: string;
  is_paid: number;
  is_active: number;
  cover_path?: string;
  file_path?: string;
  edition?: string;
  volume?: string;
  issue_number?: string;
}

export const NewspaperPage: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [selectedMonth, setSelectedMonth] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const perPage = 6;

  const { data, isLoading } = useQuery({
    queryKey: ['newspapers-data'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/media?kind=news');
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch newspapers');
      return (res.data?.items || []) as Publication[];
    },
  });

  const allItems = data || [];

  // Filter by year & month
  const filtered = allItems.filter((item) => {
    if (!item.published_on) return true;
    const parts = item.published_on.split('-');
    const y = parts[0];
    const m = parts[1] ? String(parseInt(parts[1], 10)) : '';

    if (selectedYear && y !== selectedYear) return false;
    if (selectedMonth && m !== selectedMonth) return false;
    return true;
  });

  // Unique years for filter
  const years = Array.from(
    new Set(allItems.map((i) => i.published_on?.split('-')[0]).filter(Boolean))
  ).sort().reverse();

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  const currentItems = filtered.slice((page - 1) * perPage, page * perPage);

  return (
    <>
      <SEO
        title="The Chronicle Archive · Book Buddy Newspaper | BookBuddy"
        description="Read editions of the Book Buddy student newspaper in Chennai. Student journalism, young author spotlights, and book reviews."
      />

      <main style={{ padding: '2.5rem 1rem 4rem', backgroundColor: 'var(--tint, #fdfbf7)', minHeight: '80vh' }}>
        <div style={{ maxWidth: '1140px', margin: '0 auto' }}>
          {/* Breadcrumb */}
          <nav style={{ fontSize: '0.85rem', marginBottom: '16px', color: 'var(--ink-subtle, #6b7280)' }} aria-label="Breadcrumb">
            <Link to="/media" style={{ color: 'var(--navy, #061446)', textDecoration: 'none', fontWeight: 600 }}>
              Media Hub
            </Link>
            <span style={{ margin: '0 6px' }}>/</span>
            <span>Newspapers</span>
          </nav>

          {/* Header */}
          <header style={{ marginBottom: '28px' }}>
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
              Press &amp; Media
            </span>
            <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 6px' }}>
              The <span style={{ color: 'var(--maroon, #740f28)' }}>Chronicle</span> Archive
            </h1>
            <p style={{ color: 'var(--ink-subtle, #4b5563)', fontSize: '1rem', margin: 0 }}>
              Exploring stories, journalism, and student voices from our reading community.
            </p>
          </header>

          {/* Filter Bar */}
          <div
            style={{
              backgroundColor: '#ffffff',
              border: '1px solid var(--border-color, #e5e7eb)',
              borderRadius: '12px',
              padding: '16px 20px',
              marginBottom: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '16px',
              boxShadow: '0 2px 8px rgba(6, 20, 70, 0.04)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <label style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--navy, #061446)' }}>
                Filter Editions:
              </label>

              <select
                value={selectedYear}
                onChange={(e) => {
                  setSelectedYear(e.target.value);
                  setPage(1);
                }}
                style={{
                  padding: '8px 14px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color, #e5e7eb)',
                  fontSize: '0.875rem',
                  color: 'var(--ink, #111827)',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value="">All Years</option>
                {years.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>

              <select
                value={selectedMonth}
                onChange={(e) => {
                  setSelectedMonth(e.target.value);
                  setPage(1);
                }}
                style={{
                  padding: '8px 14px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color, #e5e7eb)',
                  fontSize: '0.875rem',
                  color: 'var(--ink, #111827)',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value="">All Months</option>
                <option value="1">January</option>
                <option value="2">February</option>
                <option value="3">March</option>
                <option value="4">April</option>
                <option value="5">May</option>
                <option value="6">June</option>
                <option value="7">July</option>
                <option value="8">August</option>
                <option value="9">September</option>
                <option value="10">October</option>
                <option value="11">November</option>
                <option value="12">December</option>
              </select>

              {(selectedYear || selectedMonth) && (
                <button
                  onClick={() => {
                    setSelectedYear('');
                    setSelectedMonth('');
                    setPage(1);
                  }}
                  type="button"
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--maroon, #740f28)',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Clear Filter
                </button>
              )}
            </div>

            <span style={{ fontSize: '0.875rem', color: 'var(--ink-subtle, #6b7280)' }}>
              Showing <strong>{filtered.length}</strong> editions
            </span>
          </div>

          {/* Grid */}
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
              Loading newspaper editions...
            </div>
          ) : currentItems.length === 0 ? (
            <div
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color, #e5e7eb)',
                borderRadius: '12px',
                padding: '48px',
                textAlign: 'center',
              }}
            >
              <h3 style={{ color: 'var(--navy, #061446)', margin: '0 0 8px' }}>No newspaper issues found</h3>
              <p style={{ color: 'var(--text-muted)', margin: 0 }}>
                Try adjusting your filter or check back soon for fresh editions!
              </p>
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                gap: '24px',
                marginBottom: '36px',
              }}
            >
              {currentItems.map((item) => (
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
                  {/* Cover */}
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
                          backgroundColor: 'rgba(6, 20, 70, 0.04)',
                          color: 'var(--navy, #061446)',
                          padding: '20px',
                          textAlign: 'center',
                        }}
                      >
                        <NewspaperIcon size={38} style={{ marginBottom: '8px' }} />
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Book Buddy Chronicle
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
                          letterSpacing: '0.06em',
                          color: 'var(--maroon, #740f28)',
                          backgroundColor: 'rgba(116, 15, 40, 0.08)',
                          padding: '2px 8px',
                          borderRadius: '12px',
                        }}
                      >
                        {item.volume || 'VOL 1'} · {item.issue_number || item.edition || 'ISSUE'}
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

                    <p style={{ fontSize: '0.85rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.5, margin: '0 0 20px', flexGrow: 1 }}>
                      {item.description || 'A fresh edition of the Book Buddy community newspaper.'}
                    </p>

                    {/* Action */}
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
                              gap: '6px',
                              backgroundColor: 'var(--maroon, #740f28)',
                              color: '#ffffff',
                              padding: '9px 14px',
                              borderRadius: '8px',
                              fontWeight: 700,
                              fontSize: '0.85rem',
                              textDecoration: 'none',
                            }}
                          >
                            <Eye size={15} /> View / Read
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
                          Print Edition in Library
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <nav style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', margin: '32px 0' }} aria-label="Pagination">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                type="button"
                style={{
                  padding: '8px 14px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color, #e5e7eb)',
                  backgroundColor: '#ffffff',
                  color: page === 1 ? '#9ca3af' : 'var(--navy, #061446)',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  cursor: page === 1 ? 'not-allowed' : 'pointer',
                }}
              >
                &larr; Previous
              </button>

              {Array.from({ length: totalPages }).map((_, idx) => {
                const pageNum = idx + 1;
                const isActive = pageNum === page;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    type="button"
                    style={{
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid ' + (isActive ? 'var(--maroon, #740f28)' : 'var(--border-color, #e5e7eb)'),
                      backgroundColor: isActive ? 'var(--maroon, #740f28)' : '#ffffff',
                      color: isActive ? '#ffffff' : 'var(--ink, #111827)',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                    }}
                  >
                    {pageNum}
                  </button>
                );
              })}

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                type="button"
                style={{
                  padding: '8px 14px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color, #e5e7eb)',
                  backgroundColor: '#ffffff',
                  color: page === totalPages ? '#9ca3af' : 'var(--navy, #061446)',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  cursor: page === totalPages ? 'not-allowed' : 'pointer',
                }}
              >
                Next &rarr;
              </button>
            </nav>
          )}
        </div>
      </main>
    </>
  );
};
