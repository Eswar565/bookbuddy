import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, X } from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { apiGet } from '../api/client';
import { Link } from 'react-router-dom';

export interface GalleryCategory {
  slug: string;
  title: string;
  short_line: string;
  cover_image: string;
  cta_text?: string;
  cta_link?: string;
  cta_desc?: string;
  photo_count?: number;
  preview_photos?: Array<{ id: any; image_path?: string; thumbnail_path?: string; alt_text?: string }>;
}

export const GalleryPage: React.FC = () => {
  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['gallery'],
    queryFn: async () => {
      const res = await apiGet('/api/v1/gallery');
      if (!res.ok) throw new Error(res.error?.message || 'Failed to fetch gallery');
      return res.data;
    },
  });

  const categories: GalleryCategory[] = data?.categories || [];
  const settings = data?.settings || {};

  return (
    <>
      <SEO
        title="Photo Gallery | BookBuddy Library"
        description="Capturing moments and memories from reading corners, storytelling sessions, and library life in Chennai."
      />

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '3rem 1.5rem 5rem' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', maxWidth: '680px', margin: '0 auto 3rem' }}>
          <span
            style={{
              display: 'inline-block',
              backgroundColor: 'var(--navy-tint, rgba(6, 20, 70, 0.06))',
              color: 'var(--navy, #061446)',
              fontSize: '0.8rem',
              fontWeight: 800,
              padding: '6px 14px',
              borderRadius: '20px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '10px',
            }}
          >
            {settings.gallery_pill || 'Our Gallery'}
          </span>
          <h1 style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 10px' }}>
            {settings.gallery_heading || 'Capturing Moments, Creating Memories'}
          </h1>
          <p style={{ color: 'var(--text-muted, #475569)', fontSize: '1rem', lineHeight: 1.6, margin: 0 }}>
            Take a visual tour through our welcoming Saligramam space, reading circles, and lively community workshops.
          </p>
        </div>

        {/* Categories Grid */}
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>Loading photos...</div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '28px',
            }}
          >
            {categories.map((cat) => (
              <div
                key={cat.slug}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '16px',
                  overflow: 'hidden',
                  boxShadow: '0 6px 20px rgba(10, 36, 114, 0.07)',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.18s ease, box-shadow 0.18s ease',
                }}
              >
                {/* Category Cover */}
                <div style={{ position: 'relative', width: '100%', height: '220px', backgroundColor: '#e2e8f0', overflow: 'hidden' }}>
                  <img
                    src={cat.cover_image.startsWith('/') ? cat.cover_image : `/${cat.cover_image}`}
                    alt={cat.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onClick={() => setSelectedPhoto(cat.cover_image)}
                  />
                  <span
                    style={{
                      position: 'absolute',
                      bottom: '12px',
                      right: '12px',
                      backgroundColor: 'rgba(6, 20, 70, 0.85)',
                      color: '#ffffff',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '4px 10px',
                      borderRadius: '12px',
                      backdropFilter: 'blur(4px)',
                    }}
                  >
                    {cat.photo_count || 3} Photos
                  </span>
                </div>

                {/* Details */}
                <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', flex: 1 }}>
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--navy)', margin: '0 0 8px' }}>
                    {cat.title}
                  </h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5, margin: '0 0 20px', flex: 1 }}>
                    {cat.short_line}
                  </p>

                  {/* Thumbnail Row */}
                  {cat.preview_photos && cat.preview_photos.length > 0 && (
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
                      {cat.preview_photos.map((p, idx) => {
                        const img = p.thumbnail_path || p.image_path || '';
                        return (
                          <div
                            key={idx}
                            onClick={() => setSelectedPhoto(p.image_path || img)}
                            style={{
                              width: '60px',
                              height: '45px',
                              borderRadius: '6px',
                              overflow: 'hidden',
                              backgroundColor: '#e2e8f0',
                              cursor: 'pointer',
                              border: '1px solid var(--border-color)',
                            }}
                          >
                            <img src={img.startsWith('/') ? img : `/${img}`} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {cat.cta_link && (
                    <Link
                      to={cat.cta_link}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        color: 'var(--maroon, #740f28)',
                        fontWeight: 700,
                        fontSize: '0.85rem',
                        textDecoration: 'none',
                        marginTop: 'auto',
                      }}
                    >
                      <span>{cat.cta_text || 'Learn More'}</span>
                      <ArrowRight size={14} />
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Lightbox Modal */}
        {selectedPhoto && (
          <div
            onClick={() => setSelectedPhoto(null)}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 1100,
              backgroundColor: 'rgba(0, 0, 0, 0.88)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
              cursor: 'zoom-out',
            }}
          >
            <button
              onClick={() => setSelectedPhoto(null)}
              type="button"
              style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                background: 'rgba(255, 255, 255, 0.2)',
                border: 'none',
                borderRadius: '50%',
                color: '#ffffff',
                padding: '8px',
                cursor: 'pointer',
              }}
            >
              <X size={24} />
            </button>
            <img
              src={selectedPhoto.startsWith('/') ? selectedPhoto : `/${selectedPhoto}`}
              alt="Enlarged gallery view"
              style={{
                maxWidth: '92vw',
                maxHeight: '88vh',
                objectFit: 'contain',
                borderRadius: '8px',
                boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
              }}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}
      </div>
    </>
  );
};
