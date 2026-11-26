import React, { useState } from 'react';
import { Send, CheckCircle, Handshake, Mail, Phone, MapPin } from 'lucide-react';
import { SEO } from '../components/common/SEO';
import { useToast } from '../context/ToastContext';
import { apiPost } from '../api/client';

export const PartnerPage: React.FC = () => {
  const { showToast } = useToast();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [organisation, setOrganisation] = useState('');
  const [proposalType, setProposalType] = useState('Reading Circle Partner');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !message) {
      showToast('Please fill in your name, email, and proposal message.', 'error');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await apiPost('/api/v1/partners', {
        full_name: fullName,
        email,
        phone,
        organisation,
        proposal_type: proposalType,
        message,
      });

      if (res.ok) {
        setSubmitted(true);
        showToast('Thank you! Your partnership proposal has been received.', 'success');
      } else {
        showToast(res.error?.message || 'Could not submit proposal. Please try again.', 'error');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <SEO
        title="Become a Partner | BookBuddy Library"
        description="Collaborate with BookBuddy to expand reading circles, school outreach, and creative literacy initiatives."
      />

      <main style={{ padding: '24px 0 32px', backgroundColor: 'var(--surface-body, #f8fafc)', minHeight: 'calc(100vh - 140px)' }}>
        <div style={{ maxWidth: '1120px', margin: '0 auto', padding: '0 16px' }}>
          {/* Header */}
          <header style={{ marginBottom: '18px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 800,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--maroon, #740f28)',
                display: 'block',
                marginBottom: '4px',
              }}
            >
              PARTNERSHIP &amp; COLLABORATION
            </span>
            <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 4px', lineHeight: 1.2 }}>
              Partner with Book Buddy
            </h1>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted, #475569)', margin: 0, lineHeight: 1.4 }}>
              Collaborate with us to expand reading circles, school library outreach, author sessions, and literacy initiatives.
            </p>
          </header>

          {/* Main 2-Column Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1.4fr) minmax(280px, 0.9fr)',
              gap: '20px',
              alignItems: 'start',
            }}
            className="partner-grid-react"
          >
            {/* Form Card */}
            <section
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color, #e2e8f0)',
                borderRadius: '12px',
                padding: '20px 24px',
                boxShadow: '0 2px 8px rgba(10, 36, 114, 0.04)',
              }}
            >
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 14px' }}>
                Tell us about your proposal
              </h2>

              {submitted ? (
                <div style={{ textAlign: 'center', padding: '28px 16px' }}>
                  <CheckCircle size={44} color="#16a34a" style={{ margin: '0 auto 12px' }} />
                  <h3 style={{ fontSize: '1.2rem', color: 'var(--navy, #061446)', margin: '0 0 8px' }}>
                    Proposal Submitted!
                  </h3>
                  <p style={{ color: 'var(--text-muted, #475569)', fontSize: '0.875rem', margin: '0 0 16px' }}>
                    Thank you for reaching out. Our partnerships team will review your proposal and get in touch shortly.
                  </p>
                  <button
                    onClick={() => {
                      setSubmitted(false);
                      setFullName('');
                      setEmail('');
                      setPhone('');
                      setOrganisation('');
                      setMessage('');
                    }}
                    type="button"
                    style={{
                      backgroundColor: 'var(--navy, #061446)',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '8px 18px',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Submit Another Proposal
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {/* Row 1: Name & Email */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '4px' }}>
                        Full Name <span style={{ color: 'var(--maroon, #740f28)' }}>*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="Your name"
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          height: '36px',
                          padding: '6px 12px',
                          border: '1px solid var(--border-color, #cbd5e1)',
                          borderRadius: '8px',
                          fontSize: '13px',
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '4px' }}>
                        Email Address <span style={{ color: 'var(--maroon, #740f28)' }}>*</span>
                      </label>
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@organisation.com"
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          height: '36px',
                          padding: '6px 12px',
                          border: '1px solid var(--border-color, #cbd5e1)',
                          borderRadius: '8px',
                          fontSize: '13px',
                        }}
                      />
                    </div>
                  </div>

                  {/* Row 2: Phone & Org */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '4px' }}>
                        Phone Number
                      </label>
                      <input
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="+91 90000 00000"
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          height: '36px',
                          padding: '6px 12px',
                          border: '1px solid var(--border-color, #cbd5e1)',
                          borderRadius: '8px',
                          fontSize: '13px',
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '4px' }}>
                        Organisation / School
                      </label>
                      <input
                        type="text"
                        value={organisation}
                        onChange={(e) => setOrganisation(e.target.value)}
                        placeholder="e.g. Oakridge High, Book Club"
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          height: '36px',
                          padding: '6px 12px',
                          border: '1px solid var(--border-color, #cbd5e1)',
                          borderRadius: '8px',
                          fontSize: '13px',
                        }}
                      />
                    </div>
                  </div>

                  {/* Row 3: Interest */}
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '4px' }}>
                      Partnership Interest
                    </label>
                    <select
                      value={proposalType}
                      onChange={(e) => setProposalType(e.target.value)}
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        height: '36px',
                        padding: '6px 10px',
                        border: '1px solid var(--border-color, #cbd5e1)',
                        borderRadius: '8px',
                        fontSize: '13px',
                        backgroundColor: '#ffffff',
                      }}
                    >
                      <option value="Reading Circle Partner">Host / Co-organise Reading Circles</option>
                      <option value="School Library Outreach">School Library Outreach &amp; Curation</option>
                      <option value="Book Box Donation &amp; Sponsorship">Book Bundle Sponsorship &amp; Donations</option>
                      <option value="Author &amp; Storyteller Collaboration">Author, Storyteller or Illustrator Session</option>
                      <option value="Venue &amp; Community Partner">Venue &amp; Community Space Partner</option>
                      <option value="Other">Other Collaboration</option>
                    </select>
                  </div>

                  {/* Row 4: Message */}
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--navy, #061446)', marginBottom: '4px' }}>
                      Your Message or Proposal <span style={{ color: 'var(--maroon, #740f28)' }}>*</span>
                    </label>
                    <textarea
                      required
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      rows={3}
                      placeholder="Briefly describe your idea or how we can work together..."
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        height: '68px',
                        padding: '8px 12px',
                        border: '1px solid var(--border-color, #cbd5e1)',
                        borderRadius: '8px',
                        fontSize: '13px',
                        resize: 'none',
                      }}
                    />
                  </div>

                  {/* Submit Button */}
                  <div style={{ marginTop: '4px' }}>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        border: 'none',
                        cursor: isSubmitting ? 'not-allowed' : 'pointer',
                        padding: '10px 24px',
                        fontSize: '14px',
                        fontWeight: 700,
                        borderRadius: '8px',
                        backgroundColor: 'var(--navy, #061446)',
                        color: '#ffffff',
                      }}
                    >
                      <Send size={15} />
                      {isSubmitting ? 'Submitting...' : 'Submit Partnership Proposal'}
                    </button>
                  </div>
                </form>
              )}
            </section>

            {/* Right Details Aside */}
            <aside style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-color, #e2e8f0)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  boxShadow: '0 2px 8px rgba(10, 36, 114, 0.04)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Handshake size={18} color="var(--navy, #061446)" />
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: 0 }}>
                    Why Partner with Us?
                  </h3>
                </div>
                <ul
                  style={{
                    paddingLeft: '18px',
                    margin: 0,
                    color: 'var(--text-muted, #475569)',
                    lineHeight: 1.5,
                    fontSize: '12.5px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                  }}
                >
                  <li>Curated multilingual catalogues for ages 4 to adult.</li>
                  <li>Pomodoro-style reading circles and story interactions.</li>
                  <li>Direct connection with families, young readers &amp; schools.</li>
                  <li>Community newspaper and podcasts highlighting stories.</li>
                </ul>
              </div>

              <div
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-color, #e2e8f0)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  boxShadow: '0 2px 8px rgba(10, 36, 114, 0.04)',
                }}
              >
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 10px' }}>
                  Partnerships Desk
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12.5px', color: 'var(--text-muted, #475569)' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                    <Phone size={14} color="var(--navy, #061446)" style={{ marginTop: '2px', flexShrink: 0 }} />
                    <div>
                      <strong style={{ color: 'var(--navy, #061446)' }}>Phone:</strong>
                      <div>
                        <a href="tel:+919080759312" style={{ color: 'var(--maroon, #740f28)', textDecoration: 'none', fontWeight: 600 }}>
                          +91 90807 59312
                        </a>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                    <Mail size={14} color="var(--navy, #061446)" style={{ marginTop: '2px', flexShrink: 0 }} />
                    <div>
                      <strong style={{ color: 'var(--navy, #061446)' }}>Email:</strong>
                      <div>
                        <a href="mailto:contact@book-buddy.in" style={{ color: 'var(--maroon, #740f28)', textDecoration: 'none', fontWeight: 600 }}>
                          contact@book-buddy.in
                        </a>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                    <MapPin size={14} color="var(--navy, #061446)" style={{ marginTop: '2px', flexShrink: 0 }} />
                    <div>
                      <strong style={{ color: 'var(--navy, #061446)' }}>Address:</strong>
                      <div>Book Buddy, Saligramam, Chennai, TN, India</div>
                    </div>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </>
  );
};
