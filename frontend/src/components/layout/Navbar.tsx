import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { BookOpen, User, ShoppingBag } from 'lucide-react';
import styles from './Navbar.module.css';

export const Navbar: React.FC = () => {
  return (
    <header className={styles.navbar}>
      <div className={styles.container}>
        <Link to="/" className={styles.brand}>
          <BookOpen className={styles.brandIcon} size={28} />
          <span>BookBuddy</span>
        </Link>

        <nav>
          <ul className={styles.navLinks}>
            <li>
              <NavLink
                to="/"
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink
                }
              >
                Home
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/about"
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink
                }
              >
                About
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/library"
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink
                }
              >
                Catalogue
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/contact"
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.activeNavLink}` : styles.navLink
                }
              >
                Contact
              </NavLink>
            </li>
          </ul>
        </nav>

        <div className={styles.navActions}>
          <Link to="/library" className={styles.btnOutline} title="View borrow cart">
            <ShoppingBag size={18} />
          </Link>
          <a href="/admin/login/" className={styles.btnPrimary}>
            <User size={18} />
            <span>Admin</span>
          </a>
        </div>
      </div>
    </header>
  );
};
