import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import styles from './Footer.module.css';

export const Footer: React.FC = () => {
  const { user } = useAuth();

  return (
    <footer className={styles.footer} role="contentinfo">
      <div className={styles.container}>
        {/* Col 1: Brand & Bio */}
        <div className={styles.brandCol}>
          <Link to="/" aria-label="Book Buddy — Home" className={styles.logoLink}>
            <img
              src="/static/img/brand/bookbuddy-official-logo.png"
              alt="Book Buddy"
              className={styles.logoImg}
              width={160}
              height={40}
              onError={(e) => {
                // Graceful fallback to text brand if image fails to load
                (e.currentTarget as HTMLElement).style.display = 'none';
                const parent = e.currentTarget.parentElement;
                if (parent && !parent.querySelector(`.${styles.logoFallback}`)) {
                  const fallback = document.createElement('span');
                  fallback.className = styles.logoFallback;
                  fallback.textContent = 'Book Buddy';
                  parent.appendChild(fallback);
                }
              }}
            />
          </Link>
          <p className={styles.tagline}>
            A welcoming community lending library fostering curiosity, lifelong reading, and connection for all ages.
          </p>
        </div>

        {/* Col 2: Working Hours */}
        <div className={styles.col}>
          <h3 className={styles.heading}>Working Hours</h3>
          <div className={styles.hoursBlock}>
            <p className={styles.hoursRow}>
              <strong className={styles.dayLabel}>Tuesday – Sunday</strong>
              <span className={styles.timeLabel}>10:00 AM – 1:00 PM</span>
              <span className={styles.timeLabel}>4:30 PM – 8:30 PM</span>
            </p>
            <p className={styles.hoursRow}>
              <strong className={styles.dayLabel}>Monday</strong>
              <span className={styles.closedLabel}>Closed</span>
            </p>
          </div>
        </div>

        {/* Col 3: Useful Links (Split into 2 sub-columns) */}
        <div className={styles.col}>
          <h3 className={styles.heading}>Useful Links</h3>
          <div className={styles.linksGrid}>
            <ul className={styles.linkList}>
              <li>
                <Link to="/library" className={styles.link}>Book Catalogue</Link>
              </li>
              <li>
                <Link to="/membership" className={styles.link}>Membership Plans</Link>
              </li>
              <li>
                <a href="/how-to-borrow/" className={styles.link}>How to Borrow</a>
              </li>
              <li>
                <a href="/visit-us/" className={styles.link}>Visit Us</a>
              </li>
              <li>
                <Link to="/events" className={styles.link}>Events &amp; Contests</Link>
              </li>
              <li>
                <a href="/community/" className={styles.link}>Community</a>
              </li>
            </ul>

            <ul className={styles.linkList}>
              <li>
                <Link to="/community/media" className={styles.link}>Media Hub</Link>
              </li>
              <li>
                <Link to="/gallery" className={styles.link}>Photo Gallery</Link>
              </li>
              <li>
                <Link to="/about" className={styles.link}>About Us</Link>
              </li>
              <li>
                <Link to="/collaborators" className={styles.link}>Collaborators</Link>
              </li>
              <li>
                <Link to="/contact" className={styles.link}>Contact Us</Link>
              </li>
              <li>
                {user ? (
                  <Link to="/membership" className={styles.linkAccent}>My Dashboard</Link>
                ) : (
                  <Link to="/login" className={styles.linkAccent}>Login / My Account</Link>
                )}
              </li>
            </ul>
          </div>
        </div>

        {/* Col 4: Get In Touch */}
        <div className={styles.col}>
          <h3 className={styles.heading}>Get In Touch</h3>
          <div className={styles.contactList}>
            <div className={styles.contactItem}>
              <span className={styles.contactLabel}>Phone:</span>
              <a href="tel:+919080759312" className={styles.contactLink}>
                +91 9080759312
              </a>
            </div>

            <div className={styles.contactItem}>
              <span className={styles.contactLabel}>Email:</span>
              <a href="mailto:bookbuddy.edu@gmail.com" className={styles.contactLink}>
                bookbuddy.edu@gmail.com
              </a>
            </div>

            <div className={styles.contactItem}>
              <span className={styles.contactLabel}>Address:</span>
              <a
                href="https://maps.google.com/?q=Book+Buddy+Gandhi+Nagar+Saligramam+Chennai+600093"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.contactLink}
                title="Open location in Google Maps"
              >
                1, Thiruvalluvar St, Thiru Nagar Colony, Gandhi Nagar, Saligramam, Chennai 600093
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Slim Bottom Bar (One row ~44px) */}
      <div className={styles.bottomBar}>
        <div className={styles.bottomContainer}>
          <p className={styles.copyright}>
            &copy; 2026 Book Buddy. All rights reserved.
          </p>

          <nav className={styles.legalLinks} aria-label="Legal navigation">
            <Link to="/privacy-policy" className={styles.legalLink}>Privacy Policy</Link>
            <span className={styles.dot} aria-hidden="true">&bull;</span>
            <Link to="/terms" className={styles.legalLink}>Terms &amp; Conditions</Link>
            <span className={styles.dot} aria-hidden="true">&bull;</span>
            <Link to="/refund-policy" className={styles.legalLink}>Refund &amp; Cancellation</Link>
          </nav>

          <div className={styles.socialIcons} aria-label="Follow Book Buddy on social media">
            {/* Instagram */}
            <a
              href="https://instagram.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Instagram"
              className={styles.socialLink}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
              </svg>
            </a>

            {/* Facebook */}
            <a
              href="https://facebook.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Facebook"
              className={styles.socialLink}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
              </svg>
            </a>

            {/* YouTube */}
            <a
              href="https://youtube.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="YouTube"
              className={styles.socialLink}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"></path>
                <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02" fill="currentColor"></polygon>
              </svg>
            </a>

            {/* WhatsApp */}
            <a
              href="https://wa.me/919080759312"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="WhatsApp"
              className={styles.socialLink}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
