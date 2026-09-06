import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import Navbar from './components/Navbar';
import AuthModal from './components/AuthModal';
import RAGChatWidget from './components/RAGChatWidget';
import SeatMapModal from './components/SeatMapModal';
import FlightSearchPage from './pages/customer/FlightSearchPage';
import CheckoutPage from './pages/customer/CheckoutPage';
import ManageBookingsPage from './pages/customer/ManageBookingsPage';
import WaitlistPage from './pages/customer/WaitlistPage';
import AdminDashboard from './pages/admin/AdminDashboard';

function AppContent() {
  const [activeTab, setActiveTab] = useState('search'); // 'search', 'checkout', 'manage', 'waitlist', 'admin-dashboard'
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [ragModalOpen, setRagModalOpen] = useState(false);
  const [seatModalOpen, setSeatModalOpen] = useState(false);
  
  const [selectedFlight, setSelectedFlight] = useState(null);
  const [bookingDraft, setBookingDraft] = useState(null);

  const handleSelectFlight = (flight) => {
    setSelectedFlight(flight);
    setSeatModalOpen(true);
  };

  const handleProceedToCheckout = (draft) => {
    setBookingDraft(draft);
    setSeatModalOpen(false);
    setActiveTab('checkout');
  };

  const handleJoinWaitlistFromMap = (flight) => {
    setSeatModalOpen(false);
    setActiveTab('waitlist');
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col font-sans selection:bg-zinc-800 selection:text-white">
      
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        openAuthModal={() => setAuthModalOpen(true)}
        openRAGModal={() => setRagModalOpen(true)}
      />

      {/* Main View Router */}
      <main className="flex-1 pb-16">
        {activeTab === 'search' && (
          <FlightSearchPage onSelectFlight={handleSelectFlight} />
        )}

        {activeTab === 'checkout' && bookingDraft && (
          <CheckoutPage
            bookingDraft={bookingDraft}
            onBack={() => {
              setSeatModalOpen(true);
              setActiveTab('search');
            }}
            onBookingSuccess={(res) => {
              // Successfully booked
            }}
          />
        )}

        {activeTab === 'manage' && (
          <ManageBookingsPage />
        )}

        {activeTab === 'waitlist' && (
          <WaitlistPage />
        )}

        {activeTab === 'admin-dashboard' && (
          <AdminDashboard />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/80 bg-zinc-950 py-8 px-4 sm:px-6 lg:px-8 text-center text-xs text-zinc-500 font-mono">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-white" />
            <span>AEROPS Flight Management & Dual-Writer Automation Ledger</span>
          </div>
          <div>FastAPI · n8n Cloud · Neon PostgreSQL · ChromaDB · Groq LLaMA-3.3</div>
        </div>
      </footer>

      {/* Interactive Modals */}
      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />
      <RAGChatWidget isOpen={ragModalOpen} onClose={() => setRagModalOpen(false)} />
      <SeatMapModal
        flight={selectedFlight}
        isOpen={seatModalOpen}
        onClose={() => setSeatModalOpen(false)}
        onProceedToCheckout={handleProceedToCheckout}
        onJoinWaitlist={handleJoinWaitlistFromMap}
      />

    </div>
  );
}

export default function App() {
  return (
    <NotificationProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </NotificationProvider>
  );
}
