import React from 'react';
import { Link } from 'react-router-dom';
import { Icon } from '../components/ui/Icon';
import { SEO } from '../components/common/SEO';

export const CommunityPage: React.FC = () => {
  return (
    <>
      <SEO
        title="Community · Reading Circles, Contests & Gatherings | Book Buddy"
        description="Join the Book Buddy community in Chennai. Enjoy curated reading circles, friendly creative contests, workshops, and student-published media."
      />

      <main style={{ padding: '2.5rem 1rem 4rem', backgroundColor: 'var(--tint, #fdfbf7)' }}>
        <div style={{ maxWidth: '1140px', margin: '0 auto' }}>
          {/* Hero Banner */}
          <header
            style={{
              background: 'linear-gradient(135deg, var(--navy, #061446) 0%, #172554 60%, var(--maroon, #740f28) 100%)',
              borderRadius: '12px',
              padding: '40px 24px',
              textAlign: 'center',
              margin: '0 auto 36px',
              boxShadow: '0 8px 24px rgba(6, 20, 70, 0.12)',
            }}
          >
            <span
              style={{
                display: 'inline-block',
                background: 'rgba(255, 255, 255, 0.18)',
                color: '#ffffff',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                padding: '4px 12px',
                borderRadius: '20px',
                fontWeight: 700,
                marginBottom: '12px',
              }}
            >
              Our Reading Family
            </span>
            <h1
              style={{
                fontSize: 'clamp(1.8rem, 3.5vw, 2.4rem)',
                fontWeight: 800,
                color: '#ffffff',
                margin: '0 0 10px',
                lineHeight: 1.25,
              }}
            >
              Welcome to the Book Buddy Community
            </h1>
            <p
              style={{
                fontSize: '0.95rem',
                color: 'rgba(255, 255, 255, 0.9)',
                maxWidth: '680px',
                margin: '0 auto 20px',
                lineHeight: 1.6,
              }}
            >
              Stories are meant to be shared, lived, and celebrated together. We bring readers, parents, children, and authors together through inspiring reading circles, friendly creative contests, and thoughtful library gatherings.
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <Link
                to="/events"
                style={{
                  background: '#ffffff',
                  color: 'var(--navy, #061446)',
                  fontWeight: 700,
                  padding: '10px 20px',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                }}
              >
                Explore Events &amp; Contests &rarr;
              </Link>
              <Link
                to="/community/media"
                style={{
                  background: 'transparent',
                  color: '#ffffff',
                  border: '1.5px solid #ffffff',
                  fontWeight: 700,
                  padding: '10px 20px',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                }}
              >
                Read Our Media &rarr;
              </Link>
            </div>
          </header>

          {/* 4 Community Pillars Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '20px',
              margin: '0 auto 36px',
            }}
          >
            {/* 1. Reading Circles */}
            <article
              style={{
                background: '#ffffff',
                border: '1px solid var(--border, #e5e7eb)',
                borderRadius: '12px',
                padding: '24px 20px',
                boxShadow: '0 2px 8px rgba(6, 20, 70, 0.04)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '10px',
                  background: 'rgba(6, 20, 70, 0.08)',
                  color: 'var(--navy, #061446)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px',
                }}
              >
                <Icon name="book-open" size={24} weight="duotone" />
              </div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 8px' }}>
                Reading Circles
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.55, margin: '0 0 16px', flexGrow: 1 }}>
                Curated reading sessions for children and young adults. We dive into rich stories, discuss themes, build vocabulary, and nurture lifelong reading habits.
              </p>
              <Link
                to="/events?type=reading-circle"
                style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--maroon, #740f28)', textDecoration: 'none' }}
              >
                Explore Reading Circles &rarr;
              </Link>
            </article>

            {/* 2. Contests & Creative Challenges */}
            <article
              style={{
                background: '#ffffff',
                border: '1px solid var(--border, #e5e7eb)',
                borderRadius: '12px',
                padding: '24px 20px',
                boxShadow: '0 2px 8px rgba(6, 20, 70, 0.04)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '10px',
                  background: 'rgba(217, 119, 6, 0.12)',
                  color: '#b45309',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px',
                }}
              >
                <Icon name="trophy" size={24} weight="duotone" />
              </div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 8px' }}>
                Contests &amp; Challenges
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.55, margin: '0 0 16px', flexGrow: 1 }}>
                From story-writing contests and bookmark creation to vocabulary challenges, our friendly competitions recognize young talent and encourage creative expression.
              </p>
              <Link
                to="/events?type=contest"
                style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--maroon, #740f28)', textDecoration: 'none' }}
              >
                See Active Contests &rarr;
              </Link>
            </article>

            {/* 3. Workshops & Author Visits */}
            <article
              style={{
                background: '#ffffff',
                border: '1px solid var(--border, #e5e7eb)',
                borderRadius: '12px',
                padding: '24px 20px',
                boxShadow: '0 2px 8px rgba(6, 20, 70, 0.04)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '10px',
                  background: 'rgba(116, 15, 40, 0.08)',
                  color: 'var(--maroon, #740f28)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px',
                }}
              >
                <Icon name="calendar-blank" size={24} weight="duotone" />
              </div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 8px' }}>
                Events &amp; Workshops
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.55, margin: '0 0 16px', flexGrow: 1 }}>
                Meet children's book authors, participate in hands-on art &amp; craft sessions, and attend educational seminars hosted right in our Saligramam library room.
              </p>
              <Link
                to="/events"
                style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--maroon, #740f28)', textDecoration: 'none' }}
              >
                Browse Events Calendar &rarr;
              </Link>
            </article>

            {/* 4. Reader Contributions */}
            <article
              style={{
                background: '#ffffff',
                border: '1px solid var(--border, #e5e7eb)',
                borderRadius: '12px',
                padding: '24px 20px',
                boxShadow: '0 2px 8px rgba(6, 20, 70, 0.04)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '10px',
                  background: 'rgba(6, 20, 70, 0.08)',
                  color: 'var(--navy, #061446)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px',
                }}
              >
                <Icon name="chats-circle" size={24} weight="duotone" />
              </div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 8px' }}>
                Reader Contributions
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--ink-subtle, #4b5563)', lineHeight: 1.55, margin: '0 0 16px', flexGrow: 1 }}>
                Your child wrote a heartwarming story, poem, or book review? Share it with us to be featured in our student newspapers, magazines, and podcasts!
              </p>
              <Link
                to="/contact"
                style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--maroon, #740f28)', textDecoration: 'none' }}
              >
                Submit Your Story &rarr;
              </Link>
            </article>
          </div>

          {/* Media Hub Section */}
          <section
            style={{
              background: '#ffffff',
              border: '1px solid var(--border, #e5e7eb)',
              borderRadius: '12px',
              padding: '28px 24px',
              margin: '0 auto 36px',
              boxShadow: '0 2px 8px rgba(6, 20, 70, 0.04)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
              <div>
                <span
                  style={{
                    display: 'inline-block',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: 'var(--maroon, #740f28)',
                    marginBottom: '6px',
                  }}
                >
                  Read, Listen &amp; Learn
                </span>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--navy, #061446)', margin: '0 0 4px' }}>
                  Media Hub: Newspapers, Magazines &amp; Podcasts
                </h2>
                <p style={{ color: 'var(--ink-subtle, #4b5563)', fontSize: '0.9rem', margin: 0 }}>
                  Explore publications written by and for young readers, parents, and literature lovers.
                </p>
              </div>
              <Link
                to="/community/media"
                style={{
                  background: 'var(--navy, #061446)',
                  color: '#ffffff',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  padding: '8px 18px',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                View All Media &rarr;
              </Link>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
              <div style={{ background: 'var(--tint, #fdfbf7)', padding: '18px 16px', borderRadius: '10px', border: '1px solid var(--border, #e5e7eb)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--navy, #061446)' }}>
                  <Icon name="newspaper" size={18} />
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Newspapers</h3>
                </div>
                <p style={{ fontSize: '0.825rem', color: 'var(--ink-subtle, #4b5563)', margin: '0 0 12px', lineHeight: 1.5 }}>
                  Student journalism, book roundups, and young author spotlights in our community newspaper editions.
                </p>
                <Link to="/newspaper" style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--maroon, #740f28)', textDecoration: 'none' }}>
                  Read Newspapers &rarr;
                </Link>
              </div>
              <div style={{ background: 'var(--tint, #fdfbf7)', padding: '18px 16px', borderRadius: '10px', border: '1px solid var(--border, #e5e7eb)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--navy, #061446)' }}>
                  <Icon name="book-open-text" size={18} />
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Magazines</h3>
                </div>
                <p style={{ fontSize: '0.825rem', color: 'var(--ink-subtle, #4b5563)', margin: '0 0 12px', lineHeight: 1.5 }}>
                  Quarterly literary magazines filled with illustrated adventures, creative writing, and reader reviews.
                </p>
                <Link to="/magazine" style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--maroon, #740f28)', textDecoration: 'none' }}>
                  Browse Magazines &rarr;
                </Link>
              </div>
              <div style={{ background: 'var(--tint, #fdfbf7)', padding: '18px 16px', borderRadius: '10px', border: '1px solid var(--border, #e5e7eb)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--navy, #061446)' }}>
                  <Icon name="microphone-stage" size={18} />
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Podcasts</h3>
                </div>
                <p style={{ fontSize: '0.825rem', color: 'var(--ink-subtle, #4b5563)', margin: '0 0 12px', lineHeight: 1.5 }}>
                  Audio episodes featuring engaging bedtime stories, author discussions, and reading tips for parents.
                </p>
                <Link to="/podcasts" style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--maroon, #740f28)', textDecoration: 'none' }}>
                  Listen to Podcasts &rarr;
                </Link>
              </div>
            </div>
          </section>

          {/* Join Callout Footer */}
          <section
            style={{
              background: 'linear-gradient(135deg, var(--navy, #061446) 0%, var(--maroon, #740f28) 100%)',
              borderRadius: '12px',
              padding: '32px 24px',
              textAlign: 'center',
              boxShadow: '0 8px 24px rgba(6, 20, 70, 0.12)',
              marginTop: 0,
            }}
          >
            <h3 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ffffff', margin: '0 0 8px' }}>
              Ready to Join Our Community?
            </h3>
            <p style={{ fontSize: '0.925rem', color: 'rgba(255, 255, 255, 0.9)', maxWidth: '620px', margin: '0 auto 18px', lineHeight: 1.55 }}>
              Whether you're visiting our reading room in Chennai, joining an online circle, or sharing your creative story, there is always an open chair for you at Book Buddy.
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <Link
                to="/visit-us"
                style={{
                  background: '#ffffff',
                  color: 'var(--navy, #061446)',
                  fontWeight: 700,
                  padding: '9px 18px',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontSize: '0.85rem',
                }}
              >
                Visit Our Library
              </Link>
              <Link
                to="/contact"
                style={{
                  background: 'transparent',
                  color: '#ffffff',
                  border: '1.5px solid #ffffff',
                  fontWeight: 700,
                  padding: '9px 18px',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontSize: '0.85rem',
                }}
              >
                Contact Us
              </Link>
            </div>
          </section>
        </div>
      </main>
    </>
  );
};
