import React, { useState } from 'react';
import { Plane, Shield, User, LogOut, Sparkles, Clock, Compass, Activity, Ticket, Menu, X, ChevronDown, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ activeTab, setActiveTab, openAuthModal, openRAGModal }) {
  const { user, logout, switchDemoAccount, isSuperAdmin, isAgent, isAdminOrAgent } = useAuth();
  const [demoMenuOpen, setDemoMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-800/80 bg-black/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo */}
        <div className="flex items-center gap-6">
          <div 
            onClick={() => setActiveTab('search')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-white text-black flex items-center justify-center font-bold shadow-lg shadow-white/10 group-hover:scale-105 transition-transform duration-300">
              <Plane className="w-5 h-5 fill-black" />
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-wider text-white flex items-center gap-1.5">
                AEROPS <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">OS</span>
              </span>
              <p className="text-[10px] text-zinc-400 font-mono tracking-tight hidden sm:block">FastAPI · n8n · Neon Postgres</p>
            </div>
          </div>

          {/* Navigation Links (Customer & Operations) */}
          <nav className="hidden md:flex items-center gap-1">
            <button
              onClick={() => setActiveTab('search')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'search'
                  ? 'bg-zinc-800 text-white font-semibold shadow-inner'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              Search Flights
            </button>

            <button
              onClick={() => setActiveTab('manage')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'manage'
                  ? 'bg-zinc-800 text-white font-semibold shadow-inner'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              Manage Booking
            </button>

            <button
              onClick={() => setActiveTab('waitlist')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'waitlist'
                  ? 'bg-zinc-800 text-white font-semibold shadow-inner'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              Waitlist Portal
            </button>

            {isAdminOrAgent && (
              <div className="h-4 w-[1px] bg-zinc-800 mx-2" />
            )}

            {isAdminOrAgent && (
              <button
                onClick={() => setActiveTab('admin-dashboard')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
                  activeTab.startsWith('admin')
                    ? 'bg-white text-black font-bold shadow-md shadow-white/10'
                    : 'text-zinc-300 hover:text-white hover:bg-zinc-900 border border-zinc-800'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                Ops Dashboard
              </button>
            )}
          </nav>
        </div>

        {/* Right Actions: AI Assistant, Demo Account Switcher, User Menu */}
        <div className="flex items-center gap-3">
          
          {/* AI Policy Assistant Button */}
          <button
            onClick={openRAGModal}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 text-zinc-100 border border-zinc-700/60 transition-all hover:border-zinc-500 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-zinc-300 animate-pulse" />
            <span className="hidden sm:inline">Flight Policy AI</span>
            <span className="sm:hidden">Policy AI</span>
          </button>

          {/* User Auth Profile / Login / Logout */}
          {user ? (
            <div className="flex items-center gap-3 pl-2 border-l border-zinc-800">
              <div className="flex flex-col text-right">
                <span className="text-xs font-semibold text-white">{user.first_name} {user.last_name}</span>
                <span className="text-[10px] text-zinc-400 font-mono">
                  {user.role?.name === 'SUPER_ADMIN' ? 'SUPER ADMIN' : user.role?.name === 'OPERATIONS_AGENT' ? 'OPS AGENT' : (user.loyalty_tier || 'MEMBER')}
                </span>
              </div>
              <button
                onClick={logout}
                title="Log Out"
                className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-900 border border-transparent hover:border-zinc-800 transition-all"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={openAuthModal}
              className="px-4 py-1.5 rounded-lg text-xs font-bold bg-white text-black hover:bg-zinc-200 transition-all shadow-sm"
            >
              Sign In / Register
            </button>
          )}

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-zinc-400 hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-zinc-800 bg-zinc-950 p-4 space-y-2">
          <button
            onClick={() => { setActiveTab('search'); setMobileMenuOpen(false); }}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-zinc-300 hover:bg-zinc-900"
          >
            Search Flights
          </button>
          <button
            onClick={() => { setActiveTab('manage'); setMobileMenuOpen(false); }}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-zinc-300 hover:bg-zinc-900"
          >
            Manage Booking
          </button>
          <button
            onClick={() => { setActiveTab('waitlist'); setMobileMenuOpen(false); }}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-zinc-300 hover:bg-zinc-900"
          >
            Waitlist Portal
          </button>
          {isAdminOrAgent && (
            <button
              onClick={() => { setActiveTab('admin-dashboard'); setMobileMenuOpen(false); }}
              className="w-full text-left px-3 py-2 rounded-lg text-sm font-bold text-white bg-zinc-900 border border-zinc-800"
            >
              Operations Dashboard
            </button>
          )}
        </div>
      )}
    </header>
  );
}
