import React from 'react';
import { Link } from 'react-router-dom';
import { SEO } from '../components/common/SEO';

export const NotFoundPage: React.FC = () => {
  return (
    <>
      <SEO title="404 - Page Not Found" description="The requested page could not be found." />
      <div
        style={{
          maxWidth: '600px',
          margin: '6rem auto',
          textAlign: 'center',
          padding: '0 1.5rem',
        }}
      >
        <h1 style={{ fontSize: '4rem', fontWeight: 800, color: 'var(--navy)' }}>404</h1>
        <h2 style={{ fontSize: '1.5rem', color: 'var(--maroon)', margin: '0.5rem 0 1.5rem' }}>
          Page Not Found
        </h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', lineHeight: 1.6 }}>
          The page you are looking for doesn't exist or may have moved.
        </p>
        <Link
          to="/"
          style={{
            backgroundColor: 'var(--navy)',
            color: '#fff',
            padding: '0.75rem 1.5rem',
            borderRadius: 'var(--radius-md)',
            fontWeight: 600,
            display: 'inline-block',
          }}
        >
          Return Home
        </Link>
      </div>
    </>
  );
};
