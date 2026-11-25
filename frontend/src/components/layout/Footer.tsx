import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Footer.module.css';

export const Footer: React.FC = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.brandCol}>
          <h3>BookBuddy</h3>
          <p>
            A vibrant community library dedicated to spreading the joy of reading, literary arts,
            and lifelong learning for children, youth, and adults.
          </p>
        </div>

        <div className={styles.col}>
          <h4>Library</h4>
          <ul>
            <li>
              <Link to="/library">Catalogue</Link>
            </li>
            <li>
              <Link to="/about">About Us</Link>
            </li>
            <li>
              <Link to="/contact">Visit Us</Link>
            </li>
          </ul>
        </div>

        <div className={styles.col}>
          <h4>Community</h4>
          <ul>
            <li>
              <a href="/events">Events</a>
            </li>
            <li>
              <a href="/gallery">Gallery</a>
            </li>
            <li>
              <a href="/community">Community</a>
            </li>
          </ul>
        </div>

        <div className={styles.col}>
          <h4>Admin & Portal</h4>
          <ul>
            <li>
              <a href="/admin/login/">Librarian Login</a>
            </li>
            <li>
              <a href="/accounts/login/">Member Portal</a>
            </li>
          </ul>
        </div>
      </div>

      <div className={styles.bottomBar}>
        <p>&copy; {new Date().getFullYear()} BookBuddy Community Library. All rights reserved.</p>
        <p>Built with React & Flask</p>
      </div>
    </footer>
  );
};
