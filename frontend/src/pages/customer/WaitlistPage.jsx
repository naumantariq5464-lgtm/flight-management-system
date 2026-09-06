import React, { useState } from 'react';
import { UserPlus, Sparkles, Clock, CheckCircle2, ShieldCheck, Ticket, AlertCircle, ArrowRight } from 'lucide-react';
import api from '../../api/client';
import { useNotification } from '../../context/NotificationContext';
import { useAuth } from '../../context/AuthContext';

export default function WaitlistPage() {
  const { user } = useAuth();
  const { addToast } = useNotification();

  // Join form state
  const [flightNumber, setFlightNumber] = useState('BA-105');
  const [seatClass, setSeatClass] = useState('ECONOMY');
  const [fareType, setFareType] = useState('FLEXIBLE');
  const [passengerName, setPassengerName] = useState(user ? `${user.first_name} ${user.last_name}` : 'Ali Khan');
  const [passengerEmail, setPassengerEmail] = useState(user ? user.email : 'customer@flightsystem.com');
  const [loadingJoin, setLoadingJoin] = useState(false);
  const [joinResult, setJoinResult] = useState(null);

  // Claim token form state
  const [claimToken, setClaimToken] = useState('');
  const [loadingClaim, setLoadingClaim] = useState(false);
  const [claimResult, setClaimResult] = useState(null);

  const handleJoinWaitlist = async (e) => {
    e.preventDefault();
    setLoadingJoin(true);
    try {
      // Find flight by number
      const searchRes = await api.get('/flights/search');
      const targetFlight = searchRes.find((f) => f.flight_number.toLowerCase() === flightNumber.trim().toLowerCase()) || searchRes[0];

      if (!targetFlight) {
        addToast(`Flight ${flightNumber} not found`, 'error');
        setLoadingJoin(false);
        return;
      }

      const res = await api.post('/waitlist/join', {
        flight_id: targetFlight.id,
        seat_class: seatClass,
        fare_type: fareType,
        passenger_name: passengerName,
        passenger_email: passengerEmail,
        loyalty_tier: user?.loyalty_tier || 'SILVER',
      });

      setJoinResult(res);
      addToast('Successfully added to Standby / Waitlist queue!', 'success');
    } catch (err) {
      addToast(err.message || 'Failed to join waitlist', 'error');
    } finally {
      setLoadingJoin(false);
    }
  };

  const handleClaimSeat = async (e) => {
    e.preventDefault();
    if (!claimToken.trim()) return;
    setLoadingClaim(true);

    try {
      const res = await api.post('/waitlist/claim', { claim_token: claimToken.trim() });
      setClaimResult(res);
      addToast('Auto-promoted seat successfully claimed and confirmed!', 'success');
    } catch (err) {
      addToast(err.message || 'Invalid or expired 24h claim token', 'error');
    } finally {
      setLoadingClaim(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white">Waitlist & Standby Management</h1>
        <p className="text-xs text-zinc-400 mt-1">
          Join standby for sold-out flights or redeem your 24-hour seat auto-promotion claim token.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Column: Join Waitlist */}
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 sm:p-8 shadow-2xl space-y-6">
          <div className="flex items-center gap-3 border-b border-zinc-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center">
              <UserPlus className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Join Standby Queue</h2>
              <p className="text-xs text-zinc-400">Automated queue evaluated every 5 mins by n8n cron</p>
            </div>
          </div>

          <form onSubmit={handleJoinWaitlist} className="space-y-4 text-xs">
            <div>
              <label className="block text-zinc-400 font-mono mb-1 uppercase">Flight Number</label>
              <input
                type="text"
                required
                value={flightNumber}
                onChange={(e) => setFlightNumber(e.target.value.toUpperCase())}
                placeholder="e.g. BA-105"
                className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono uppercase focus:outline-none focus:border-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-zinc-400 font-mono mb-1 uppercase">Desired Class</label>
                <select
                  value={seatClass}
                  onChange={(e) => setSeatClass(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white focus:outline-none focus:border-white"
                >
                  <option value="ECONOMY">Economy</option>
                  <option value="BUSINESS">Business</option>
                  <option value="FIRST">First Class</option>
                </select>
              </div>

              <div>
                <label className="block text-zinc-400 font-mono mb-1 uppercase">Fare Type</label>
                <select
                  value={fareType}
                  onChange={(e) => setFareType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white focus:outline-none focus:border-white"
                >
                  <option value="FLEXIBLE">Flexible (+500 Priority)</option>
                  <option value="BASIC_ECONOMY">Basic Economy</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-zinc-400 font-mono mb-1 uppercase">Passenger Full Name</label>
              <input
                type="text"
                required
                value={passengerName}
                onChange={(e) => setPassengerName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white focus:outline-none focus:border-white"
              />
            </div>

            <div>
              <label className="block text-zinc-400 font-mono mb-1 uppercase">Notification Email</label>
              <input
                type="email"
                required
                value={passengerEmail}
                onChange={(e) => setPassengerEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white focus:outline-none focus:border-white"
              />
            </div>

            <button
              type="submit"
              disabled={loadingJoin}
              className="w-full py-3 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {loadingJoin ? 'Submitting...' : 'Join Waitlist Queue'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Join Result Banner */}
          {joinResult && (
            <div className="p-4 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-2 text-xs animate-in fade-in">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <CheckCircle2 className="w-4 h-4" />
                Waitlist Confirmed!
              </div>
              <div className="text-zinc-300">
                Calculated Priority Score: <strong className="text-white font-mono">{joinResult.priority_score || 3500}</strong>
              </div>
              <div className="text-[10px] text-zinc-500 font-mono">
                When a seat opens, n8n background cron will claim it for you with `FOR UPDATE SKIP LOCKED`.
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Claim Auto-Promoted Seat */}
        <div className="space-y-6">
          <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 sm:p-8 shadow-2xl space-y-6">
            <div className="flex items-center gap-3 border-b border-zinc-800 pb-4">
              <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center">
                <Ticket className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Redeem Claim Token</h2>
                <p className="text-xs text-zinc-400">Claim your promoted seat within the 24-hour window</p>
              </div>
            </div>

            <form onSubmit={handleClaimSeat} className="space-y-4 text-xs">
              <div>
                <label className="block text-zinc-400 font-mono mb-1 uppercase">24-Hour Promotion Claim Token</label>
                <input
                  type="text"
                  required
                  value={claimToken}
                  onChange={(e) => setClaimToken(e.target.value.trim())}
                  placeholder="e.g. CLAIM-82914-XJ9"
                  className="w-full px-3 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono focus:outline-none focus:border-white"
                />
              </div>

              <button
                type="submit"
                disabled={loadingClaim}
                className="w-full py-3 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {loadingClaim ? 'Validating Token...' : 'Claim & Confirm Seat'}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>

            {claimResult && (
              <div className="p-4 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-2 text-xs">
                <div className="text-emerald-400 font-bold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Seat Confirmed!
                </div>
                <div className="text-zinc-300">
                  New Booking PNR: <strong className="text-white font-mono">{claimResult.pnr || 'PNR-WAITLIST'}</strong>
                </div>
              </div>
            )}
          </div>

          {/* Priority Score Explanation */}
          <div className="p-6 rounded-3xl border border-zinc-800 bg-zinc-950/60 text-xs space-y-3">
            <h3 className="text-xs font-mono uppercase text-zinc-400 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-white" />
              Priority Algorithm Formula
            </h3>
            <ul className="space-y-1.5 text-zinc-400 font-mono text-[11px]">
              <li>• <strong className="text-white">Platinum Member:</strong> +3,000 pts</li>
              <li>• <strong className="text-white">Gold Member:</strong> +2,000 pts</li>
              <li>• <strong className="text-white">Silver Member:</strong> +1,000 pts</li>
              <li>• <strong className="text-white">Flexible Fare Choice:</strong> +500 pts</li>
              <li>• <strong className="text-white">First Come First Served:</strong> Earlier join time bonus</li>
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
}
