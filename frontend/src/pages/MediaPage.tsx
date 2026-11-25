import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Newspaper, BookMarked, Radio, Lock, Download } from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { useAuth } from '../context/AuthContext';
import { apiGet } from '../api/client';
import { Link } from 'react-router-dom';

export interface Publication {
  id: number;
  title: string;
  description?: string;
  kind: 'news' | 'magazine' | 'podcast';
  published_on: string;
  is_paid: number;
  is_active: number;
  cover_path?: string;
  file_path?: string;
  audio_url?: string;
  issue_number?: string;
}

export const MediaPage: React.FC = () => {
  const { user, activeSubscription } = useAuth();
  const [activeTab, setActiveTab] = useState<'all' | 'news' | 'magazine' | 'podcast'>('all');

  const { data, isLoading } = useQuery({
    queryKey: ['media', activeTab],
    queryFn: async () => {
      const param = activeTab !== 'all' ? `?kind=${activeTab}` : '';
      const res = await apiGet(`/api/v1/media${param}`);
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch publications');
      return res.data;
    },
  });

  const newspapers: Publication[] = data?.newspapers || (activeTab === 'news' ? data?.items : []) || [];
  const magazines: Publication[] = data?.magazines || (activeTab === 'magazine' ? data?.items : []) || [];
  const podcasts: Publication[] = data?.podcasts || (activeTab === 'podcast' ? data?.items : []) || [];

  return (
    <>
      <SEO
        title="Community Publications & Podcasts | BookBuddy"
        description="Read Book Buddy student newspapers, literary magazines, and listen to children audio podcasts in Chennai."
      />

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2.5rem 1.5rem 5rem' }}>
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: 0 }}>
            Community Publications & Media
          </h1>
          <p style={{ color: 'var(--text-muted, #475569)', marginTop: '0.4rem', fontSize: '0.95rem' }}>
            Explore newspapers, young-author magazines, and storytelling podcasts created for our reading community.
          </p>
        </div>

        {/* Tab Controls */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            marginBottom: '2rem',
            borderBottom: '1px solid var(--border-color)',
            paddingBottom: '12px',
          }}
        >
          {[
            { id: 'all', label: 'All Publications' },
            { id: 'news', label: 'Newspapers' },
            { id: 'magazine', label: 'Magazines' },
            { id: 'podcast', label: 'Podcasts' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              type="button"
              style={{
                padding: '8px 18px',
                borderRadius: '20px',
                border: activeTab === tab.id ? 'none' : '1px solid var(--border-color)',
                backgroundColor: activeTab === tab.id ? 'var(--navy, #061446)' : '#ffffff',
                color: activeTab === tab.id ? '#ffffff' : 'var(--text-muted)',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>Loading media items...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
            {/* Newspapers Section */}
            {(activeTab === 'all' || activeTab === 'news') && newspapers.length > 0 && (
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Newspaper size={20} color="var(--maroon)" />
                  <span>Community Newspapers</span>
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
                  {newspapers.map((item) => (
                    <PublicationCard key={item.id} item={item} user={user} activeSubscription={activeSubscription} />
                  ))}
                </div>
              </div>
            )}

            {/* Magazines Section */}
            {(activeTab === 'all' || activeTab === 'magazine') && magazines.length > 0 && (
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BookMarked size={20} color="var(--maroon)" />
                  <span>Literary Magazines</span>
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
                  {magazines.map((item) => (
                    <PublicationCard key={item.id} item={item} user={user} activeSubscription={activeSubscription} />
                  ))}
                </div>
              </div>
            )}

            {/* Podcasts Section */}
            {(activeTab === 'all' || activeTab === 'podcast') && podcasts.length > 0 && (
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Radio size={20} color="var(--maroon)" />
                  <span>Audio Podcasts & Stories</span>
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
                  {podcasts.map((item) => (
                    <div
                      key={item.id}
                      style={{
                        backgroundColor: '#ffffff',
                        borderRadius: '12px',
                        padding: '20px',
                        boxShadow: '0 4px 18px rgba(10, 36, 114, 0.06)',
                        borderLeft: '4px solid var(--maroon, #740f28)',
                        display: 'flex',
                        flexDirection: 'column',
                      }}
                    >
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy)', margin: '0 0 6px' }}>{item.title}</h3>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', marginBottom: '10px' }}>Released {item.published_on}</div>
                      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: '0 0 16px', flex: 1 }}>
                        {item.description || 'Audio storytelling episode.'}
                      </p>

                      {item.audio_url ? (
                        <div>
                          <audio controls src={item.audio_url} style={{ width: '100%', height: '36px' }} />
                        </div>
                      ) : (
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', fontStyle: 'italic' }}>Audio recording coming soon.</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};

const PublicationCard: React.FC<{ item: Publication; user: any; activeSubscription: any }> = ({ item, user, activeSubscription }) => {
  const isLocked = item.is_paid && (!user || !activeSubscription);

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        padding: '20px',
        boxShadow: '0 4px 18px rgba(10, 36, 114, 0.06)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-subtle)' }}>
          {item.issue_number ? `Issue ${item.issue_number} • ` : ''}
          {item.published_on}
        </span>
        {item.is_paid ? (
          <span style={{ fontSize: '0.7rem', fontWeight: 800, backgroundColor: '#fef3c7', color: '#92400e', padding: '2px 8px', borderRadius: '4px' }}>
            Members Only
          </span>
        ) : (
          <span style={{ fontSize: '0.7rem', fontWeight: 800, backgroundColor: '#dcfce7', color: '#166534', padding: '2px 8px', borderRadius: '4px' }}>
            Free
          </span>
        )}
      </div>

      <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy)', margin: '0 0 8px' }}>
        {item.title}
      </h3>
      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: '0 0 18px', flex: 1 }}>
        {item.description || 'Community literary issue with student essays, artwork, and book reviews.'}
      </p>

      <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
        {isLocked ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#b45309' }}>
              <Lock size={14} /> Subscription Required
            </span>
            <Link
              to="/membership"
              style={{
                fontSize: '0.8rem',
                fontWeight: 700,
                color: 'var(--maroon)',
                textDecoration: 'none',
              }}
            >
              Unlock
            </Link>
          </div>
        ) : item.file_path ? (
          <a
            href={item.file_path.startsWith('/') ? item.file_path : `/${item.file_path}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--navy)',
              color: '#ffffff',
              padding: '8px 14px',
              borderRadius: '8px',
              fontSize: '0.825rem',
              fontWeight: 700,
              textDecoration: 'none',
            }}
          >
            <Download size={14} /> Read Issue (PDF)
          </a>
        ) : (
          <span style={{ fontSize: '0.825rem', color: 'var(--text-subtle)' }}>Published in library print edition</span>
        )}
      </div>
    </div>
  );
};
