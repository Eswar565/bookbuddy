import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Icon } from '../components/ui/Icon';
import { SEO } from '../components/common/SEO';
import { apiGet } from '../api/client';

export interface Collaborator {
  id: number;
  name: string;
  category: string;
  brief: string;
  image?: string;
  link?: string;
}

export interface CollaboratorSection {
  slug: string;
  title: string;
  description: string;
  count: number;
  partners: Collaborator[];
}

export const CollaboratorsPage: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['collaborators'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/collaborators');
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch collaborators');
      return res.data?.sections as CollaboratorSection[];
    },
  });

  const sections = data || [];

  return (
    <>
      <SEO
        title="Collaborators & Partners | BookBuddy Library"
        description="Meet the schools, authors, and community organisations collaborating with BookBuddy to foster children reading across Chennai."
      />

      <div style={{ maxWidth: '1160px', margin: '0 auto', padding: '3rem 1.5rem 5rem' }}>
        <div style={{ textAlign: 'center', maxWidth: '680px', margin: '0 auto 3.5rem' }}>
          <span
            style={{
              display: 'inline-block',
              backgroundColor: 'var(--maroon-tint, rgba(116, 15, 40, 0.08))',
              color: 'var(--maroon, #740f28)',
              fontSize: '0.8rem',
              fontWeight: 800,
              padding: '6px 14px',
              borderRadius: '20px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '10px',
            }}
          >
            Community Network
          </span>
          <h1 style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 10px' }}>
            Our Collaborators & Friends
          </h1>
          <p style={{ color: 'var(--text-muted, #475569)', fontSize: '1rem', lineHeight: 1.6, margin: 0 }}>
            We work closely with passionate educators, storytellers, and cultural spaces across Chennai to expand the joy of books.
          </p>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>Loading partners...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3.5rem' }}>
            {sections.map((section) => (
              <div key={section.slug}>
                <div style={{ marginBottom: '1.25rem', borderBottom: '2px solid var(--border-color)', paddingBottom: '8px' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--navy)', margin: '0 0 4px' }}>
                    {section.title}
                  </h2>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0 }}>
                    {section.description}
                  </p>
                </div>

                {section.partners.length === 0 ? (
                  <div style={{ padding: '16px', backgroundColor: 'var(--surface-body)', borderRadius: '8px', color: 'var(--text-subtle)', fontSize: '0.875rem' }}>
                    Partners in this category will be listed shortly.
                  </div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '20px' }}>
                    {section.partners.map((partner) => (
                      <div
                        key={partner.id}
                        style={{
                          backgroundColor: '#ffffff',
                          borderRadius: '12px',
                          padding: '20px',
                          boxShadow: '0 4px 18px rgba(10, 36, 114, 0.05)',
                          display: 'flex',
                          flexDirection: 'column',
                          border: '1px solid var(--border-color)',
                        }}
                      >
                        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy)', margin: '0 0 8px' }}>
                          {partner.name}
                        </h3>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: '0 0 16px', flex: 1 }}>
                          {partner.brief || 'Community collaborator supporting literacy initiatives.'}
                        </p>
                        {partner.link && (
                          <a
                            href={partner.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              marginTop: 'auto',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              color: 'var(--maroon, #740f28)',
                              fontSize: '0.825rem',
                              fontWeight: 700,
                              textDecoration: 'none',
                            }}
                          >
                            <span>Visit Partner</span>
                            <Icon name="arrow-square-out" size={14} />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
};
