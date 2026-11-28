import React, { useState } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { BookOpen, User, ShoppingBag, LogOut, Menu, X, ChevronDown } from 'lucide-react';
import { useCart } from '../../context/CartContext';
import { useAuth } from '../../context/AuthContext';
import styles from './Navbar.module.css';

export const Navbar: React.FC = () => {
  const { count, openCheckout } = useCart();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const closeMobile = () => setMobileOpen(false);

  const isCommunityActive =
    location.pathname === '/community' ||
    location.pathname.startsWith('/community/') ||
    location.pathname.startsWith('/events') ||
    location.pathname.startsWith('/newspaper') ||
    location.pathname.startsWith('/magazine') ||
    location.pathname.startsWith('/podcasts') ||
    location.pathname.startsWith('/publications');

  return (
    <header className={styles.navbar}>
      <div className={styles.container}>
        <Link to="/" className={styles.brand} onClick={closeMobile}>
          <BookOpen className={styles.brandIcon} size={28} />
          <span>BookBuddy</span>
        </Link>

        {/* Desktop Nav */}
        <nav className={styles.desktopNav}>
          <ul className={styles.navLinks}>
            <li>
              <NavLink to="/" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink)}>
                Home
              </NavLink>
            </li>
            <li>
              <NavLink to="/library" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink)}>
                Catalogue
              </NavLink>
            </li>
            <li>
              <NavLink to="/membership" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink)}>
                Plans
              </NavLink>
            </li>

            {/* Community with dropdown (Media, Events & Contests) */}
            <li className={styles.navDropdownWrapper}>
              <NavLink
                to="/community"
                className={isCommunityActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}
              >
                Community
                <ChevronDown size={14} style={{ opacity: 0.7 }} />
              </NavLink>
              <div className={styles.navDropdownMenu}>
                <NavLink to="/community/media" className={styles.dropdownItem}>
                  Media
                </NavLink>
                <NavLink to="/events" className={styles.dropdownItem}>
                  Events &amp; Contests
                </NavLink>
              </div>
            </li>

            <li>
              <NavLink to="/gallery" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink)}>
                Gallery
              </NavLink>
            </li>
            <li>
              <NavLink to="/collaborators" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink)}>
                Partners
              </NavLink>
            </li>
            <li>
              <NavLink to="/contact" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink)}>
                Contact
              </NavLink>
            </li>
          </ul>
        </nav>

        {/* Right Actions: Cart & Auth */}
        <div className={styles.navActions}>
          <button
            onClick={openCheckout}
            type="button"
            className={styles.btnOutline}
            title="Open borrow request cart"
            style={{ position: 'relative', cursor: 'pointer', background: 'transparent' }}
          >
            <ShoppingBag size={18} />
            {count > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '-6px',
                  right: '-6px',
                  backgroundColor: 'var(--maroon, #740f28)',
                  color: '#ffffff',
                  borderRadius: '50%',
                  width: '18px',
                  height: '18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.7rem',
                  fontWeight: 800,
                }}
              >
                {count}
              </span>
            )}
          </button>

          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy)' }}>
                {user.name.split(' ')[0]}
              </span>
              <button
                onClick={() => logout()}
                type="button"
                title="Sign out"
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: '6px',
                  display: 'flex',
                }}
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <Link to="/login" className={styles.btnPrimary}>
              <User size={16} />
              <span>Sign In</span>
            </Link>
          )}

          {/* Mobile Menu Hamburger */}
          <button
            type="button"
            aria-label="Toggle navigation menu"
            onClick={() => setMobileOpen(!mobileOpen)}
            style={{
              display: 'none',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '6px',
              color: 'var(--navy)',
            }}
            className={styles.mobileHamburger}
          >
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div
          style={{
            position: 'fixed',
            inset: '64px 0 0 0',
            backgroundColor: '#ffffff',
            zIndex: 999,
            padding: '24px 20px',
            overflowY: 'auto',
            borderTop: '1px solid var(--border-color)',
          }}
        >
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[
              { to: '/', label: 'Home' },
              { to: '/library', label: 'Book Catalogue' },
              { to: '/membership', label: 'Membership Plans' },
              { to: '/community', label: 'Community' },
              { to: '/community/media', label: '— Media' },
              { to: '/events', label: '— Events & Contests' },
              { to: '/gallery', label: 'Photo Gallery' },
              { to: '/collaborators', label: 'Collaborators' },
              { to: '/about', label: 'About Us' },
              { to: '/contact', label: 'Contact & Contributions' },
            ].map((link) => (
              <li key={link.to}>
                <Link
                  to={link.to}
                  onClick={closeMobile}
                  style={{
                    display: 'block',
                    fontSize: link.label.startsWith('—') ? '0.95rem' : '1.05rem',
                    fontWeight: link.label.startsWith('—') ? 500 : 700,
                    color: link.label.startsWith('—') ? 'var(--text-muted)' : 'var(--navy, #061446)',
                    paddingLeft: link.label.startsWith('—') ? '12px' : '0',
                    textDecoration: 'none',
                    paddingBlock: '4px',
                  }}
                >
                  {link.label}
                </Link>
              </li>
            ))}
            <li style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px', marginTop: '8px' }}>
              <a
                href="/admin/login/"
                style={{
                  display: 'block',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  textDecoration: 'none',
                }}
              >
                Staff / Admin Portal →
              </a>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
};
