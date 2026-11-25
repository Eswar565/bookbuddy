import React from 'react';
import { SEO } from '../components/common/SEO';

export const AboutPage: React.FC = () => {
  return (
    <>
      <SEO
        title="About Us"
        description="Learn about BookBuddy's mission, community initiatives, and values."
      />
      <div style={{ maxWidth: '960px', margin: '3rem auto', padding: '0 1.5rem' }}>
        <h1
          style={{
            fontSize: '2.5rem',
            fontWeight: 800,
            color: 'var(--navy)',
            marginBottom: '1rem',
          }}
        >
          About BookBuddy
        </h1>
        <p
          style={{
            fontSize: '1.1rem',
            color: 'var(--text-muted)',
            lineHeight: 1.7,
            marginBottom: '2rem',
          }}
        >
          BookBuddy was founded with a singular purpose: to make quality books accessible, engaging,
          and cherished across our local communities.
        </p>

        <div
          style={{
            backgroundColor: 'var(--surface-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '2rem',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <h2 style={{ fontSize: '1.5rem', color: 'var(--maroon)', marginBottom: '1rem' }}>
            Our Mission
          </h2>
          <p style={{ color: 'var(--text-main)', lineHeight: 1.7, marginBottom: '1.5rem' }}>
            We believe that reading expands empathy, fuels imagination, and empowers individuals to
            achieve their fullest potential. Through curated multilingual catalogues, inclusive
            lending plans, and community storytelling sessions, we nurture a lifelong culture of
            books.
          </p>

          <h2 style={{ fontSize: '1.5rem', color: 'var(--maroon)', marginBottom: '1rem' }}>
            What We Offer
          </h2>
          <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-muted)', lineHeight: 1.8 }}>
            <li>Over 3,000 carefully curated titles for early readers, youth, and adults.</li>
            <li>Flexible borrow plans with home delivery or quick library pickup.</li>
            <li>Reading spaces and quiet study nooks designed for book lovers.</li>
            <li>Regular weekend literary events, book clubs, and educational workshops.</li>
          </ul>
        </div>
      </div>
    </>
  );
};
