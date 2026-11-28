import React from 'react';
import { Link } from 'react-router-dom';

interface LegalPageProps {
  type: 'privacy' | 'terms' | 'refund';
}

const META = {
  privacy: {
    title: 'Privacy Policy',
    subtitle: 'How we collect, use, and protect your information at Book Buddy Community Library.',
  },
  terms: {
    title: 'Terms & Conditions',
    subtitle: 'Membership terms, borrowing policies, and guidelines for library members.',
  },
  refund: {
    title: 'Refund & Cancellation Policy',
    subtitle: 'Payment processing, cancellation guidelines, and refund terms for memberships.',
  },
};

export const LegalPage: React.FC<LegalPageProps> = ({ type }) => {
  const info = META[type] || META.terms;

  return (
    <main style={{ maxWidth: '840px', margin: '40px auto 60px', padding: '0 20px', fontFamily: 'var(--font-main)' }}>
      <nav style={{ marginBottom: '20px', fontSize: '0.875rem' }}>
        <Link to="/" style={{ color: 'var(--navy-light, #0a2472)', textDecoration: 'none' }}>Home</Link>
        <span style={{ margin: '0 8px', color: '#94a3b8' }}>/</span>
        <span style={{ color: '#64748b' }}>{info.title}</span>
      </nav>

      <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '8px' }}>
        {info.title}
      </h1>
      <p style={{ color: '#475569', fontSize: '1rem', marginBottom: '32px', lineHeight: 1.5 }}>
        {info.subtitle}
      </p>

      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '12px',
        padding: '32px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.04)'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          background: '#fef3c7',
          color: '#92400e',
          padding: '6px 12px',
          borderRadius: '9999px',
          fontSize: '0.8125rem',
          fontWeight: 600,
          marginBottom: '20px'
        }}>
          <span>Note: Content to be provided</span>
        </div>

        <p style={{ color: '#334155', lineHeight: 1.6, fontSize: '0.95rem', marginBottom: '16px' }}>
          The complete text of the <strong>{info.title}</strong> is currently being drafted and finalized by Book Buddy management in accordance with Indian regulatory and payment gateway guidelines (including Razorpay compliance).
        </p>

        <p style={{ color: '#334155', lineHeight: 1.6, fontSize: '0.95rem', marginBottom: '24px' }}>
          If you have questions regarding our membership rules, data privacy, or payment cancellations in the interim, please reach out to our circulation desk:
        </p>

        <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
          <p style={{ margin: '0 0 6px 0', fontSize: '0.9rem', color: '#1e293b' }}>
            <strong>Email:</strong> <a href="mailto:bookbuddy.edu@gmail.com" style={{ color: 'var(--navy-light, #0a2472)' }}>bookbuddy.edu@gmail.com</a>
          </p>
          <p style={{ margin: '0 0 6px 0', fontSize: '0.9rem', color: '#1e293b' }}>
            <strong>Phone / WhatsApp:</strong> <a href="tel:+919080759312" style={{ color: 'var(--navy-light, #0a2472)' }}>+91 9080759312</a>
          </p>
          <p style={{ margin: 0, fontSize: '0.9rem', color: '#1e293b' }}>
            <strong>Address:</strong> 1, Thiruvalluvar St, Thiru Nagar Colony, Gandhi Nagar, Saligramam, Chennai, Tamil Nadu 600093
          </p>
        </div>
      </div>
    </main>
  );
};
