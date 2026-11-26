import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { AboutPage } from './pages/AboutPage';
import { LibraryPage } from './pages/LibraryPage';
import { BookDetailPage } from './pages/BookDetailPage';
import { MembershipPage } from './pages/MembershipPage';
import { CommunityPage } from './pages/CommunityPage';
import { EventsPage } from './pages/EventsPage';
import { MediaPage } from './pages/MediaPage';
import { NewspaperPage } from './pages/NewspaperPage';
import { MagazinePage } from './pages/MagazinePage';
import { PodcastPage } from './pages/PodcastPage';
import { GalleryPage } from './pages/GalleryPage';
import { CollaboratorsPage } from './pages/CollaboratorsPage';
import { PartnerPage } from './pages/PartnerPage';
import { ContactPage } from './pages/ContactPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { LegalPage } from './pages/LegalPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const App: React.FC = () => {
  return (
    <ToastProvider>
      <AuthProvider>
        <CartProvider>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<HomePage />} />
              <Route path="about" element={<AboutPage />} />
              <Route path="library" element={<LibraryPage />} />
              <Route path="library/:id" element={<BookDetailPage />} />
              <Route path="membership" element={<MembershipPage />} />
              <Route path="plans" element={<MembershipPage />} />
              <Route path="community" element={<CommunityPage />} />
              <Route path="events" element={<EventsPage />} />
              <Route path="media" element={<MediaPage />} />
              <Route path="community/media" element={<MediaPage />} />
              <Route path="newspaper" element={<NewspaperPage />} />
              <Route path="magazine" element={<MagazinePage />} />
              <Route path="podcasts" element={<PodcastPage />} />
              <Route path="publications" element={<MediaPage />} />
              <Route path="gallery" element={<GalleryPage />} />
              <Route path="gallery/:slug" element={<GalleryPage />} />
              <Route path="collaborators" element={<CollaboratorsPage />} />
              <Route path="work-with-us" element={<PartnerPage />} />
              <Route path="become-a-partner" element={<PartnerPage />} />
              <Route path="partner" element={<PartnerPage />} />
              <Route path="contact" element={<ContactPage />} />
              <Route path="privacy-policy" element={<LegalPage type="privacy" />} />
              <Route path="terms" element={<LegalPage type="terms" />} />
              <Route path="refund-policy" element={<LegalPage type="refund" />} />
              <Route path="login" element={<LoginPage />} />
              <Route path="signup" element={<SignupPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </CartProvider>
      </AuthProvider>
    </ToastProvider>
  );
};

export default App;
