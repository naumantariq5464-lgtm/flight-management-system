import React, { useState, useEffect } from 'react';
import { X, Plane, Clock, Shield, CheckCircle2, AlertTriangle, ArrowRight, UserPlus, Info } from 'lucide-react';
import api from '../api/client';
import { useNotification } from '../context/NotificationContext';
import { useAuth } from '../context/AuthContext';

export default function SeatMapModal({ flight, isOpen, onClose, onProceedToCheckout, onJoinWaitlist }) {
  const [seats, setSeats] = useState([]);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [fareType, setFareType] = useState('FLEXIBLE');
  const [loading, setLoading] = useState(false);
  const [holdTimer, setHoldTimer] = useState(null); // seconds remaining
  const [holdToken, setHoldToken] = useState(null);
  const { addToast } = useNotification();
  const { user } = useAuth();

  useEffect(() => {
    if (isOpen && flight) {
      fetchSeatMap();
      setSelectedSeats([]);
      setHoldTimer(null);
      setHoldToken(null);
    }
  }, [isOpen, flight]);

  // Countdown timer for 10-min seat hold
  useEffect(() => {
    let interval = null;
    if (holdTimer !== null && holdTimer > 0) {
      interval = setInterval(() => {
        setHoldTimer((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            addToast('Seat hold expired! Please re-select your seats.', 'error');
            setSelectedSeats([]);
            setHoldToken(null);
            fetchSeatMap();
            return null;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [holdTimer]);

  const fetchSeatMap = async () => {
    setLoading(true);
    try {
      const data = await api.get(`/flights/${flight.id}/seatmap`);
      setSeats(data);
    } catch (err) {
      addToast(err.message || 'Failed to load seat map', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSeatClick = (seat) => {
    if (seat.status !== 'AVAILABLE') return;
    if (fareType === 'BASIC_ECONOMY') {
      addToast('Basic Economy does not permit advance seat selection. Seat will be assigned at check-in.', 'info');
      return;
    }

    const isSelected = selectedSeats.some((s) => s.id === seat.id);
    if (isSelected) {
      setSelectedSeats(selectedSeats.filter((s) => s.id !== seat.id));
    } else {
      if (selectedSeats.length >= 4) {
        addToast('You can select a maximum of 4 seats per booking.', 'info');
        return;
      }
      setSelectedSeats([...selectedSeats, seat]);
    }
  };

  const handleHoldSeats = async () => {
    if (selectedSeats.length === 0 && fareType !== 'BASIC_ECONOMY') {
      addToast('Please select at least one seat.', 'error');
      return;
    }

    try {
      const seatIds = selectedSeats.map((s) => s.id);
      const res = await api.post('/bookings/hold', {
        flight_id: flight.id,
        seat_ids: seatIds,
      });

      setHoldToken(res.hold_token);
      setHoldTimer(10 * 60); // 10 minutes countdown
      addToast('Seats successfully held for 10 minutes!', 'success');
    } catch (err) {
      addToast(err.message || 'Failed to hold seats. Someone may have just reserved them.', 'error');
      fetchSeatMap();
    }
  };

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  if (!isOpen || !flight) return null;

  // Group seats by row
  const rowsMap = {};
  seats.forEach((seat) => {
    if (!rowsMap[seat.row]) rowsMap[seat.row] = [];
    rowsMap[seat.row].push(seat);
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-3xl border border-zinc-800 bg-zinc-950 shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-900/60">
          <div>
            <div className="text-base font-extrabold text-white flex items-center gap-2">
              <Plane className="w-4 h-4 text-white" />
              Flight {flight.flight_number} — Aircraft Seat Map
              <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">100 Seats</span>
            </div>
            <div className="text-xs text-zinc-400 font-mono mt-0.5">
              {flight.origin} → {flight.destination} · Departs {new Date(flight.departure_time).toLocaleString()}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-white p-1 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Hold Countdown Banner */}
        {holdTimer !== null && (
          <div className="px-6 py-2.5 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between text-xs text-zinc-200">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-white animate-spin" />
              <span>Temporary Seat Lock Active (Prevents Overselling):</span>
            </div>
            <div className="font-mono font-bold text-white text-sm bg-black px-3 py-1 rounded-lg border border-zinc-700">
              {formatTimer(holdTimer)}
            </div>
          </div>
        )}

        {/* Fare Rules & Class Selection Bar */}
        <div className="px-6 py-3 bg-black border-b border-zinc-800 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-zinc-400 uppercase">Fare Rule:</span>
            <button
              onClick={() => setFareType('FLEXIBLE')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                fareType === 'FLEXIBLE'
                  ? 'bg-white text-black'
                  : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'
              }`}
            >
              Flexible Fare (Free Seat Selection + Refundable)
            </button>
            <button
              onClick={() => { setFareType('BASIC_ECONOMY'); setSelectedSeats([]); }}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                fareType === 'BASIC_ECONOMY'
                  ? 'bg-white text-black'
                  : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'
              }`}
            >
              Basic Economy (Auto-Seat Assign)
            </button>
          </div>

          <button
            onClick={() => onJoinWaitlist(flight)}
            className="text-xs text-zinc-400 hover:text-white flex items-center gap-1 font-mono underline underline-offset-4"
          >
            <UserPlus className="w-3.5 h-3.5" />
            Join Standby / Waitlist
          </button>
        </div>

        {/* Seat Legend */}
        <div className="px-6 py-2 bg-zinc-950/80 border-b border-zinc-800 flex flex-wrap items-center justify-center gap-6 text-[11px] font-mono text-zinc-400">
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-zinc-900 border border-zinc-700" />
            <span>Available</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-white border border-white text-black font-bold flex items-center justify-center text-[9px]">✓</div>
            <span className="text-white font-bold">Selected</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-zinc-800/40 border border-zinc-800 text-zinc-600 line-through flex items-center justify-center text-[9px]">✕</div>
            <span>Occupied / Held</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 text-[10px]">EXIT</span>
            <span>Exit Row / Extra Legroom</span>
          </div>
        </div>

        {/* Cabin Map Visual Layout */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center">
          
          {/* Cockpit Indicator */}
          <div className="w-40 h-8 rounded-t-full bg-zinc-900 border-t-2 border-x-2 border-zinc-700 flex items-center justify-center text-[10px] font-mono text-zinc-500 uppercase tracking-widest mb-6">
            ▲ Front / Cockpit
          </div>

          <div className="space-y-3 w-full max-w-xl">
            {Object.keys(rowsMap).map((rowStr) => {
              const rowNum = parseInt(rowStr);
              const rowSeats = rowsMap[rowNum];
              const isFirst = rowSeats[0]?.seat_class === 'FIRST';
              const isBusiness = rowSeats[0]?.seat_class === 'BUSINESS';
              const isEconomy = rowSeats[0]?.seat_class === 'ECONOMY';

              return (
                <div key={rowNum} className="flex items-center justify-between gap-3">
                  
                  {/* Row Number */}
                  <span className="w-6 text-right font-mono text-xs text-zinc-500">{rowNum}</span>

                  {/* Seats in Row */}
                  <div className="flex-1 flex items-center justify-center gap-2 sm:gap-3">
                    {rowSeats.map((seat) => {
                      const isSelected = selectedSeats.some((s) => s.id === seat.id);
                      const isOccupied = seat.status !== 'AVAILABLE';

                      return (
                        <button
                          key={seat.id}
                          disabled={isOccupied || fareType === 'BASIC_ECONOMY'}
                          onClick={() => handleSeatClick(seat)}
                          className={`relative w-9 h-10 sm:w-11 sm:h-12 rounded-xl flex flex-col items-center justify-center text-xs font-mono font-bold transition-all duration-200 ${
                            isSelected
                              ? 'bg-white text-black scale-105 shadow-lg shadow-white/20 ring-2 ring-white'
                              : isOccupied
                              ? 'bg-zinc-900/40 border border-zinc-800/40 text-zinc-600 cursor-not-allowed'
                              : isFirst
                              ? 'bg-zinc-900 border border-zinc-700 text-zinc-200 hover:border-white hover:bg-zinc-800'
                              : isBusiness
                              ? 'bg-zinc-900 border border-zinc-800 text-zinc-300 hover:border-white hover:bg-zinc-800'
                              : 'bg-zinc-950 border border-zinc-800 text-zinc-400 hover:border-white hover:bg-zinc-900'
                          }`}
                        >
                          <span>{seat.seat_number}</span>
                          {seat.is_exit_row && (
                            <span className="text-[7px] text-zinc-400 leading-none">EXIT</span>
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Cabin Badge */}
                  <span className="w-16 text-left text-[10px] font-mono text-zinc-600 uppercase">
                    {isFirst ? 'First' : isBusiness ? 'Biz' : 'Eco'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-zinc-800 bg-zinc-950 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <div className="text-xs text-zinc-400">
              Selected: <strong className="text-white">{selectedSeats.length > 0 ? selectedSeats.map((s) => s.seat_number).join(', ') : fareType === 'BASIC_ECONOMY' ? 'Auto-Assigned' : 'None'}</strong>
            </div>
            <div className="text-xs text-zinc-500 font-mono mt-0.5">
              Fare Type: <span className="text-white font-bold">{fareType}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {holdTimer === null && selectedSeats.length > 0 && (
              <button
                type="button"
                onClick={handleHoldSeats}
                className="px-4 py-2.5 rounded-xl border border-zinc-700 hover:border-white text-zinc-200 hover:text-white text-xs font-bold font-mono transition-colors"
              >
                Lock Seat (10-Min Hold)
              </button>
            )}

            <button
              type="button"
              onClick={() => onProceedToCheckout({
                flight,
                seats: selectedSeats,
                fareType,
                holdToken
              })}
              disabled={selectedSeats.length === 0 && fareType !== 'BASIC_ECONOMY'}
              className="flex-1 sm:flex-initial px-6 py-3 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-sm flex items-center justify-center gap-2 transition-all shadow-lg shadow-white/5 disabled:opacity-40"
            >
              Continue to Checkout
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
