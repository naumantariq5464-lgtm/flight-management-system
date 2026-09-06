import React, { useState } from 'react';
import { Search, Ticket, Plane, Calendar, User, AlertTriangle, CheckCircle, RefreshCw, XCircle, ArrowRight } from 'lucide-react';
import api from '../../api/client';
import { useNotification } from '../../context/NotificationContext';

export default function ManageBookingsPage() {
  const [pnrInput, setPnrInput] = useState('');
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [selectedPassengersToCancel, setSelectedPassengersToCancel] = useState([]);
  const [cancelType, setCancelType] = useState('REFUND'); // REFUND vs TRAVEL_CREDIT
  const [cancelReason, setCancelReason] = useState('Customer requested');
  const [processingCancel, setProcessingCancel] = useState(false);
  const { addToast } = useNotification();

  const handleLookup = async (e) => {
    e?.preventDefault();
    if (!pnrInput.trim()) return;
    setLoading(true);

    try {
      const data = await api.get(`/bookings/${pnrInput.trim().toUpperCase()}`);
      setBooking(data);
      setSelectedPassengersToCancel([]);
    } catch (err) {
      addToast(err.message || 'Booking not found with this PNR.', 'error');
      setBooking(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = async () => {
    if (!booking) return;
    setProcessingCancel(true);

    try {
      if (selectedPassengersToCancel.length > 0 && selectedPassengersToCancel.length < booking.passengers.length) {
        // Partial cancellation
        const res = await api.post(`/bookings/${booking.pnr}/cancel-passengers`, {
          passenger_ids: selectedPassengersToCancel,
          reason: cancelReason,
        });
        addToast(`Partial cancellation completed! Refund: $${res.refund_amount || 0}`, 'success');
      } else {
        // Full cancellation
        const res = await api.post(`/bookings/${booking.pnr}/cancel`, {
          reason: cancelReason,
          refund_method: cancelType,
        });
        addToast(`Booking ${booking.pnr} cancelled! Refund amount: $${res.refund_amount || 0}`, 'success');
      }

      setCancelModalOpen(false);
      handleLookup(); // Refresh booking state
    } catch (err) {
      addToast(err.message || 'Failed to process cancellation', 'error');
    } finally {
      setProcessingCancel(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white">Manage My Booking</h1>
        <p className="text-xs text-zinc-400 mt-1">
          Look up your itinerary by PNR, review e-tickets, or request full/partial cancellations.
        </p>
      </div>

      {/* Lookup Form */}
      <form onSubmit={handleLookup} className="flex gap-3 p-4 rounded-2xl bg-zinc-950 border border-zinc-800 shadow-xl">
        <div className="relative flex-1">
          <Ticket className="w-4 h-4 text-zinc-500 absolute left-3.5 top-3.5" />
          <input
            type="text"
            required
            value={pnrInput}
            onChange={(e) => setPnrInput(e.target.value.toUpperCase())}
            placeholder="Enter 6-character PNR (e.g. PNR-981240 or PNR-ABC123)"
            className="w-full pl-10 pr-3 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono uppercase text-sm focus:outline-none focus:border-white transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2.5 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-xs sm:text-sm flex items-center gap-2 transition-all disabled:opacity-50"
        >
          <Search className="w-4 h-4" />
          {loading ? 'Searching...' : 'Find Booking'}
        </button>
      </form>

      {/* Booking Details Card */}
      {booking && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 sm:p-8 shadow-2xl space-y-6 animate-in fade-in">
          
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
            <div>
              <div className="text-xs font-mono text-zinc-400 uppercase">Booking Reference</div>
              <div className="text-2xl font-black font-mono tracking-wider text-white">{booking.pnr}</div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold ${
                booking.status === 'CONFIRMED'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : booking.status === 'CANCELLED'
                  ? 'bg-red-950 text-red-300 border border-red-800'
                  : 'bg-zinc-800 text-zinc-300'
              }`}>
                {booking.status}
              </span>
            </div>
          </div>

          {/* Flight Details */}
          {booking.flight && (
            <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-zinc-500 font-mono">Flight Number</span>
                <div className="text-white font-bold font-mono mt-0.5">{booking.flight.flight_number}</div>
              </div>
              <div>
                <span className="text-zinc-500 font-mono">Route</span>
                <div className="text-white font-bold font-mono mt-0.5">{booking.flight.origin} → {booking.flight.destination}</div>
              </div>
              <div>
                <span className="text-zinc-500 font-mono">Departure</span>
                <div className="text-white font-bold font-mono mt-0.5">{new Date(booking.flight.departure_time).toLocaleString()}</div>
              </div>
              <div>
                <span className="text-zinc-500 font-mono">Total Paid</span>
                <div className="text-white font-bold font-mono mt-0.5">${booking.total_price} USD</div>
              </div>
            </div>
          )}

          {/* Passenger Manifest */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono text-zinc-400 uppercase">Passenger Manifest</h3>
            <div className="space-y-2">
              {booking.passengers?.map((p) => (
                <div key={p.id} className="p-3.5 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 font-semibold text-white">
                    <User className="w-4 h-4 text-zinc-400" />
                    {p.first_name} {p.last_name}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-zinc-300 bg-black px-2 py-0.5 rounded border border-zinc-800">
                      Seat: {p.seat?.seat_number || 'Auto-Assigned'}
                    </span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                      p.status === 'CONFIRMED' ? 'text-emerald-400 bg-emerald-950/60' : 'text-zinc-500 bg-zinc-800'
                    }`}>
                      {p.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Footer: Cancel Options */}
          {booking.status === 'CONFIRMED' && (
            <div className="pt-4 border-t border-zinc-800 flex justify-end">
              <button
                onClick={() => setCancelModalOpen(true)}
                className="px-5 py-2.5 rounded-xl bg-red-950/60 hover:bg-red-900 border border-red-800 text-red-200 text-xs font-bold transition-all flex items-center gap-1.5"
              >
                <XCircle className="w-4 h-4 text-red-400" />
                Cancel Booking or Passengers
              </button>
            </div>
          )}
        </div>
      )}

      {/* Cancellation Modal */}
      {cancelModalOpen && booking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in">
          <div className="relative w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950 p-6 sm:p-8 shadow-2xl space-y-6">
            
            <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-zinc-300" />
                <h3 className="text-base font-extrabold text-white">Cancel Booking {booking.pnr}</h3>
              </div>
              <button
                onClick={() => setCancelModalOpen(false)}
                className="text-zinc-500 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-zinc-400 font-mono mb-2 uppercase">
                  Select Passengers to Cancel (Leave blank to cancel entire booking):
                </label>
                <div className="space-y-2">
                  {booking.passengers?.map((p) => {
                    const isChecked = selectedPassengersToCancel.includes(p.id);
                    return (
                      <label
                        key={p.id}
                        className="flex items-center justify-between p-3 rounded-xl bg-zinc-900 border border-zinc-800 cursor-pointer hover:border-zinc-700"
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedPassengersToCancel([...selectedPassengersToCancel, p.id]);
                              } else {
                                setSelectedPassengersToCancel(selectedPassengersToCancel.filter((id) => id !== p.id));
                              }
                            }}
                            className="accent-white"
                          />
                          <span className="font-semibold text-white">{p.first_name} {p.last_name}</span>
                        </div>
                        <span className="font-mono text-zinc-400">Seat {p.seat?.seat_number || 'N/A'}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-zinc-400 font-mono mb-1 uppercase">Cancellation Reason</label>
                <input
                  type="text"
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white text-xs focus:outline-none focus:border-white"
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-mono mb-1 uppercase">Compensation Preference</label>
                <select
                  value={cancelType}
                  onChange={(e) => setCancelType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white text-xs focus:outline-none focus:border-white"
                >
                  <option value="REFUND">Bank / Card Refund (Subject to fare policy)</option>
                  <option value="TRAVEL_CREDIT">100% Travel Credit Voucher (Valid 1 Year)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-zinc-800">
              <button
                onClick={() => setCancelModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-bold"
              >
                Go Back
              </button>
              <button
                onClick={handleCancelBooking}
                disabled={processingCancel}
                className="px-5 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-extrabold disabled:opacity-50"
              >
                {processingCancel ? 'Processing...' : 'Confirm Cancellation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
