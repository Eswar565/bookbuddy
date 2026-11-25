import React from 'react';
import { SEO } from '../components/common/SEO';
import { Mail, Phone, MapPin } from 'lucide-react';

export const ContactPage: React.FC = () => {
  return (
    <>
      <SEO
        title="Contact & Visit Us"
        description="Visit BookBuddy Library, get directions, view hours, or send us a message."
      />
      <div style={{ maxWidth: '960px', margin: '3rem auto', padding: '0 1.5rem' }}>
        <h1
          style={{
            fontSize: '2.5rem',
            fontWeight: 800,
            color: 'var(--navy)',
            marginBottom: '0.75rem',
          }}
        >
          Visit & Contact Us
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem', marginBottom: '2.5rem' }}>
          We would love to welcome you to our space or answer any questions you have.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '2rem',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--surface-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              padding: '2rem',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <h2 style={{ fontSize: '1.3rem', color: 'var(--navy)', marginBottom: '1.5rem' }}>
              Get In Touch
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  color: 'var(--text-main)',
                }}
              >
                <MapPin size={22} color="var(--maroon)" />
                <div>
                  <strong>Address</strong>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    BookBuddy Community Library, Main Street
                  </p>
                </div>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  color: 'var(--text-main)',
                }}
              >
                <Phone size={22} color="var(--maroon)" />
                <div>
                  <strong>Phone</strong>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>+91 98765 43210</p>
                </div>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  color: 'var(--text-main)',
                }}
              >
                <Mail size={22} color="var(--maroon)" />
                <div>
                  <strong>Email</strong>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    hello@bookbuddy.example
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div
            style={{
              backgroundColor: 'var(--surface-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              padding: '2rem',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <h2 style={{ fontSize: '1.3rem', color: 'var(--navy)', marginBottom: '1.5rem' }}>
              Library Hours
            </h2>
            <ul
              style={{
                listStyle: 'none',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                color: 'var(--text-muted)',
              }}
            >
              <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Tuesday – Friday</span>
                <strong>10:00 AM – 7:00 PM</strong>
              </li>
              <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Saturday – Sunday</span>
                <strong>9:30 AM – 8:00 PM</strong>
              </li>
              <li
                style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--maroon)' }}
              >
                <span>Monday</span>
                <strong>Closed (Maintenance)</strong>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
};
