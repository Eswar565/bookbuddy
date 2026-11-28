import React, { useState } from 'react';
import { Icon } from '../components/ui/Icon';
import { SEO } from '../components/common/SEO';
import { useToast } from '../context/ToastContext';
import { apiPost } from '../api/client';

export const ContactPage: React.FC = () => {
  const { showToast } = useToast();
  const [activeForm, setActiveForm] = useState<'contact' | 'contribute'>('contact');

  // Contact form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);

  // Contribution form state
  const [cName, setCName] = useState('');
  const [cEmail, setCEmail] = useState('');
  const [cTitle, setCTitle] = useState('');
  const [cCategory, setCCategory] = useState('Essay');
  const [cBody, setCBody] = useState('');
  const [isSubmittingContribute, setIsSubmittingContribute] = useState(false);

  const handleContactSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSending(true);
    try {
      const res = await apiPost('/api/v1/contact', {
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        subject: subject.trim() || 'General Enquiry',
        message: message.trim(),
      });

      if (res.ok) {
        showToast('Your message has been received! We will reply shortly.', 'success');
        setName('');
        setEmail('');
        setPhone('');
        setSubject('');
        setMessage('');
      } else {
        showToast(res.error?.message || 'Could not send message.', 'error');
      }
    } finally {
      setIsSending(false);
    }
  };

  const handleContributeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingContribute(true);
    try {
      const res = await apiPost('/api/v1/contributions', {
        student_name: cName.trim(),
        email: cEmail.trim(),
        title: cTitle.trim(),
        category: cCategory,
        body: cBody.trim(),
      });

      if (res.ok) {
        showToast('Your contribution was received for editorial review! Thank you.', 'success');
        setCName('');
        setCEmail('');
        setCTitle('');
        setCBody('');
      } else {
        showToast(res.error?.message || 'Could not submit contribution.', 'error');
      }
    } finally {
      setIsSubmittingContribute(false);
    }
  };

  return (
    <>
      <SEO
        title="Contact & Contributions | BookBuddy Library"
        description="Visit our children lending library in Saligramam, Chennai, send an enquiry, or submit reader stories for our literary publications."
      />

      <div style={{ maxWidth: '1160px', margin: '0 auto', padding: '3rem 1.5rem 5rem' }}>
        <div style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto 3rem' }}>
          <h1 style={{ fontSize: '2.3rem', fontWeight: 800, color: 'var(--navy, #061446)', margin: '0 0 10px' }}>
            Get in Touch
          </h1>
          <p style={{ color: 'var(--text-muted, #475569)', fontSize: '1rem', lineHeight: 1.6, margin: 0 }}>
            Have questions about memberships, book requests, or volunteering? We’d love to hear from you.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '40px' }}>
          {/* Left: Contact Info & Library Location */}
          <div>
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '16px',
                padding: '32px',
                boxShadow: '0 4px 20px rgba(10, 36, 114, 0.06)',
                border: '1px solid var(--border-color)',
                marginBottom: '24px',
              }}
            >
              <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--navy)', marginBottom: '18px' }}>
                Visit Our Space
              </h2>

              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <li style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                  <Icon name="map-pin" size={20} color="var(--color-primary, #740f28)" style={{ flexShrink: 0, marginTop: '3px' }} />
                  <div>
                    <strong style={{ fontSize: '0.9rem', color: 'var(--navy)' }}>Library Address</strong>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: 1.5, margin: '4px 0 0' }}>
                      1, Thiruvalluvar St, Thiru Nagar Colony, Gandhi Nagar,<br />
                      Saligramam, Chennai, Tamil Nadu 600093
                    </p>
                  </div>
                </li>

                <li style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                  <Icon name="phone" size={20} color="var(--color-primary, #740f28)" style={{ flexShrink: 0, marginTop: '3px' }} />
                  <div>
                    <strong style={{ fontSize: '0.9rem', color: 'var(--navy)' }}>Phone & WhatsApp</strong>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: '4px 0 0' }}>
                      <a href="tel:+919080759312" style={{ color: 'inherit', textDecoration: 'none' }}>+91 90807 59312</a>
                    </p>
                  </div>
                </li>

                <li style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                  <Icon name="envelope-simple" size={20} color="var(--color-primary, #740f28)" style={{ flexShrink: 0, marginTop: '3px' }} />
                  <div>
                    <strong style={{ fontSize: '0.9rem', color: 'var(--navy)' }}>Email</strong>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: '4px 0 0' }}>
                      <a href="mailto:bookbuddy.edu@gmail.com" style={{ color: 'inherit', textDecoration: 'none' }}>bookbuddy.edu@gmail.com</a>
                    </p>
                  </div>
                </li>
              </ul>
            </div>

            {/* Timings */}
            <div style={{ backgroundColor: 'var(--navy, #061446)', borderRadius: '16px', padding: '24px', color: '#ffffff' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: '0 0 10px' }}>Library Hours</h3>
              <div style={{ fontSize: '0.875rem', opacity: 0.9, lineHeight: 1.6 }}>
                <strong>Tuesday – Sunday:</strong><br />
                Morning: 10:00 AM – 1:00 PM<br />
                Evening: 4:30 PM – 8:30 PM<br /><br />
                <span style={{ color: '#fca5a5' }}>Monday: Closed</span>
              </div>
            </div>
          </div>

          {/* Right: Form Selector & Active Form */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              padding: '32px',
              boxShadow: '0 4px 20px rgba(10, 36, 114, 0.06)',
              border: '1px solid var(--border-color)',
            }}
          >
            {/* Form Toggle Buttons */}
            <div style={{ display: 'flex', gap: '10px', marginBottom: '24px' }}>
              <button
                type="button"
                onClick={() => setActiveForm('contact')}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '8px',
                  border: activeForm === 'contact' ? 'none' : '1px solid var(--border-color)',
                  backgroundColor: activeForm === 'contact' ? 'var(--navy, #061446)' : '#fff',
                  color: activeForm === 'contact' ? '#fff' : 'var(--text-muted)',
                  fontWeight: 700,
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <Icon name="paper-plane-tilt" size={16} /> Send an Enquiry
              </button>
              <button
                type="button"
                onClick={() => setActiveForm('contribute')}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '8px',
                  border: activeForm === 'contribute' ? 'none' : '1px solid var(--border-color)',
                  backgroundColor: activeForm === 'contribute' ? 'var(--maroon, #740f28)' : '#fff',
                  color: activeForm === 'contribute' ? '#fff' : 'var(--text-muted)',
                  fontWeight: 700,
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <Icon name="chats-circle" size={16} /> Reader Contribution
              </button>
            </div>

            {activeForm === 'contact' ? (
              <form onSubmit={handleContactSubmit}>
                <div style={{ marginBottom: '14px' }}>
                  <label htmlFor="c-name" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Your Name *
                  </label>
                  <input
                    id="c-name"
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Priyan"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                  <div>
                    <label htmlFor="c-email" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Email *
                    </label>
                    <input
                      id="c-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="email@example.com"
                      style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                    />
                  </div>
                  <div>
                    <label htmlFor="c-phone" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Phone
                    </label>
                    <input
                      id="c-phone"
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+91..."
                      style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                    />
                  </div>
                </div>

                <div style={{ marginBottom: '14px' }}>
                  <label htmlFor="c-sub" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Subject
                  </label>
                  <input
                    id="c-sub"
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Book recommendation, membership enquiry..."
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  />
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <label htmlFor="c-msg" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Message *
                  </label>
                  <textarea
                    id="c-msg"
                    rows={4}
                    required
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="How can our librarians assist you?"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem', fontFamily: 'inherit' }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSending}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '8px',
                    border: 'none',
                    backgroundColor: 'var(--navy, #061446)',
                    color: '#ffffff',
                    fontWeight: 700,
                    fontSize: '0.925rem',
                    cursor: isSending ? 'not-allowed' : 'pointer',
                  }}
                >
                  {isSending ? 'Sending...' : 'Send Message'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleContributeSubmit}>
                <div style={{ marginBottom: '14px' }}>
                  <label htmlFor="cr-name" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Student / Author Name *
                  </label>
                  <input
                    id="cr-name"
                    type="text"
                    required
                    value={cName}
                    onChange={(e) => setCName(e.target.value)}
                    placeholder="Author name"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  />
                </div>

                <div style={{ marginBottom: '14px' }}>
                  <label htmlFor="cr-email" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Guardian / Student Email *
                  </label>
                  <input
                    id="cr-email"
                    type="email"
                    required
                    value={cEmail}
                    onChange={(e) => setCEmail(e.target.value)}
                    placeholder="email@example.com"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px', marginBottom: '14px' }}>
                  <div>
                    <label htmlFor="cr-title" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Article / Story Title *
                    </label>
                    <input
                      id="cr-title"
                      type="text"
                      required
                      value={cTitle}
                      onChange={(e) => setCTitle(e.target.value)}
                      placeholder="My favorite book journey..."
                      style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                    />
                  </div>
                  <div>
                    <label htmlFor="cr-cat" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Category
                    </label>
                    <select
                      id="cr-cat"
                      value={cCategory}
                      onChange={(e) => setCCategory(e.target.value)}
                      style={{ width: '100%', padding: '9px 10px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                    >
                      <option value="Essay">Essay</option>
                      <option value="Review">Book Review</option>
                      <option value="Poem">Poem</option>
                      <option value="Short Story">Story</option>
                    </select>
                  </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <label htmlFor="cr-body" style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Content / Draft *
                  </label>
                  <textarea
                    id="cr-body"
                    rows={6}
                    required
                    value={cBody}
                    onChange={(e) => setCBody(e.target.value)}
                    placeholder="Type or paste your piece here..."
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem', fontFamily: 'inherit' }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmittingContribute}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '8px',
                    border: 'none',
                    backgroundColor: 'var(--maroon, #740f28)',
                    color: '#ffffff',
                    fontWeight: 700,
                    fontSize: '0.925rem',
                    cursor: isSubmittingContribute ? 'not-allowed' : 'pointer',
                  }}
                >
                  {isSubmittingContribute ? 'Submitting...' : 'Submit for Editorial Review'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </>
  );
};
