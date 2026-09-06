import React, { useState, useEffect } from 'react';
import { Plane, Calendar, Search, ArrowRight, ArrowRightLeft, Users, Clock, ShieldCheck, Sparkles, Filter, CheckCircle2 } from 'lucide-react';
import api from '../../api/client';
import { useNotification } from '../../context/NotificationContext';

export default function FlightSearchPage({ onSelectFlight }) {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [date, setDate] = useState('');
  const [seatClass, setSeatClass] = useState('ALL');
  const [flights, setFlights] = useState([]);
  const [connectingRoutes, setConnectingRoutes] = useState([]);
  const [isConnectingMode, setIsConnectingMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const { addToast } = useNotification();

  // Load all available scheduled flights on initial load
  useEffect(() => {
    fetchInitialFlights();
  }, []);

  const fetchInitialFlights = async () => {
    setLoading(true);
    try {
      const data = await api.get('/flights/search');
      setFlights(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      if (isConnectingMode) {
        if (!origin || !destination) {
          addToast('Please enter both Origin and Destination for connecting flights', 'error');
          setLoading(false);
          return;
        }
        const data = await api.get('/flights/connecting-search', {
          params: { origin: origin.toUpperCase(), destination: destination.toUpperCase() }
        });
        setConnectingRoutes(data);
        if (data.length === 0) {
          addToast('No multi-leg connecting routes found for this itinerary.', 'info');
        }
      } else {
        const params = {};
        if (origin) params.origin = origin.toUpperCase();
        if (destination) params.destination = destination.toUpperCase();
        if (date) params.departure_date = date;
        if (seatClass !== 'ALL') params.seat_class = seatClass;

        const data = await api.get('/flights/search', { params });
        setFlights(data);
      }
    } catch (err) {
      addToast(err.message || 'Search failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      
      {/* Hero Header */}
      <div className="relative rounded-3xl border border-zinc-800 bg-gradient-to-b from-zinc-900/60 to-black p-8 sm:p-12 shadow-2xl overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-zinc-700/60 bg-zinc-900/80 text-xs text-zinc-300 font-mono">
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            Live Inventory · Concurrency-Locked Seat Ledger
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Next-Generation Flight Booking & Operations
          </h1>
          <p className="text-sm sm:text-base text-zinc-400 max-w-2xl leading-relaxed">
            Real-time seat reservations with atomic row-locking, multi-leg connecting itineraries, 
            instant fare rules enforcement, and automated waitlist standby.
          </p>
        </div>

        {/* Search Filter Form */}
        <form onSubmit={handleSearch} className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 p-4 rounded-2xl bg-zinc-950/90 border border-zinc-800 shadow-xl">
          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1 uppercase">From (Origin)</label>
            <div className="relative">
              <Plane className="w-4 h-4 text-zinc-500 absolute left-3 top-3 rotate-45" />
              <input
                type="text"
                value={origin}
                onChange={(e) => setOrigin(e.target.value.toUpperCase())}
                placeholder="e.g. LHR or LHE"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-white text-sm font-mono focus:outline-none focus:border-white transition-colors uppercase placeholder:normal-case"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1 uppercase">To (Destination)</label>
            <div className="relative">
              <Plane className="w-4 h-4 text-zinc-500 absolute left-3 top-3 -rotate-45" />
              <input
                type="text"
                value={destination}
                onChange={(e) => setDestination(e.target.value.toUpperCase())}
                placeholder="e.g. DXB or JFK"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-white text-sm font-mono focus:outline-none focus:border-white transition-colors uppercase placeholder:normal-case"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1 uppercase">Departure Date</label>
            <div className="relative">
              <Calendar className="w-4 h-4 text-zinc-500 absolute left-3 top-3" />
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white text-sm focus:outline-none focus:border-white transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1 uppercase">Cabin Class</label>
            <select
              value={seatClass}
              onChange={(e) => setSeatClass(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-white text-sm focus:outline-none focus:border-white transition-colors"
            >
              <option value="ALL">All Classes</option>
              <option value="ECONOMY">Economy</option>
              <option value="BUSINESS">Business</option>
              <option value="FIRST">First Class</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-sm flex items-center justify-center gap-2 transition-all shadow-md shadow-white/10 disabled:opacity-50"
            >
              <Search className="w-4 h-4" />
              {loading ? 'Searching...' : 'Search Flights'}
            </button>
          </div>
        </form>

        {/* Tab Toggle: Direct Flights vs Connecting Multi-Leg */}
        <div className="mt-4 flex items-center gap-2">
          <button
            type="button"
            onClick={() => { setIsConnectingMode(false); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              !isConnectingMode ? 'bg-white text-black font-bold' : 'text-zinc-400 hover:text-white bg-zinc-900'
            }`}
          >
            Direct Flights
          </button>
          <button
            type="button"
            onClick={() => { setIsConnectingMode(true); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              isConnectingMode ? 'bg-white text-black font-bold' : 'text-zinc-400 hover:text-white bg-zinc-900'
            }`}
          >
            <ArrowRightLeft className="w-3.5 h-3.5" />
            Multi-Leg Connecting Routes
          </button>
        </div>
      </div>

      {/* Flight Search Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            Available Flights
            <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 font-mono">
              {isConnectingMode ? `${connectingRoutes.length} Itineraries` : `${flights.length} Scheduled`}
            </span>
          </h2>
          <span className="text-xs text-zinc-500 font-mono">Real-time Neon DB inventory</span>
        </div>

        {/* Direct Flights List */}
        {!isConnectingMode && (
          <div className="grid grid-cols-1 gap-4">
            {flights.map((flight) => {
              const depTime = new Date(flight.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              const arrTime = new Date(flight.arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              const depDate = new Date(flight.departure_time).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });

              return (
                <div
                  key={flight.id}
                  className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6 hover:border-zinc-700 transition-all duration-300 group shadow-lg"
                >
                  {/* Flight Info & Route */}
                  <div className="flex flex-col sm:flex-row sm:items-center gap-6">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-white font-mono font-bold text-base group-hover:scale-105 transition-transform">
                        {flight.flight_number.split('-')[0] || 'FL'}
                      </div>
                      <div>
                        <div className="text-base font-extrabold text-white font-mono">{flight.flight_number}</div>
                        <div className="text-xs text-zinc-400 font-mono">{depDate}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div>
                        <div className="text-xl font-black text-white font-mono">{depTime}</div>
                        <div className="text-sm font-bold text-zinc-300">{flight.origin}</div>
                        <div className="text-[11px] text-zinc-500 max-w-[120px] truncate">{flight.origin_name}</div>
                      </div>

                      <div className="flex flex-col items-center px-2">
                        <span className="text-[10px] font-mono text-zinc-500 mb-1">Direct · Non-stop</span>
                        <div className="flex items-center gap-1.5 w-24 sm:w-32">
                          <div className="w-2 h-2 rounded-full border border-white bg-black" />
                          <div className="flex-1 border-t border-dashed border-zinc-700" />
                          <Plane className="w-3.5 h-3.5 text-white" />
                        </div>
                      </div>

                      <div>
                        <div className="text-xl font-black text-white font-mono">{arrTime}</div>
                        <div className="text-sm font-bold text-zinc-300">{flight.destination}</div>
                        <div className="text-[11px] text-zinc-500 max-w-[120px] truncate">{flight.destination_name}</div>
                      </div>
                    </div>
                  </div>

                  {/* Seat Classes & Live Availability */}
                  <div className="flex flex-wrap sm:flex-nowrap items-center gap-3">
                    
                    {/* Economy */}
                    <div className="px-3.5 py-2.5 rounded-xl border border-zinc-800/80 bg-zinc-900/60 min-w-[100px]">
                      <div className="text-[10px] uppercase font-mono text-zinc-400">Economy</div>
                      <div className="text-sm font-extrabold text-white font-mono">${flight.base_price_economy}</div>
                      <div className="text-[10px] font-mono text-zinc-400 mt-0.5">
                        {flight.available_economy ?? flight.economy_seats} seats left
                      </div>
                    </div>

                    {/* Business */}
                    <div className="px-3.5 py-2.5 rounded-xl border border-zinc-800/80 bg-zinc-900/60 min-w-[100px]">
                      <div className="text-[10px] uppercase font-mono text-zinc-400">Business</div>
                      <div className="text-sm font-extrabold text-white font-mono">${flight.base_price_business}</div>
                      <div className="text-[10px] font-mono text-zinc-400 mt-0.5">
                        {flight.available_business ?? flight.business_class_seats} seats left
                      </div>
                    </div>

                    {/* First */}
                    <div className="px-3.5 py-2.5 rounded-xl border border-zinc-800/80 bg-zinc-900/60 min-w-[100px]">
                      <div className="text-[10px] uppercase font-mono text-zinc-400">First Class</div>
                      <div className="text-sm font-extrabold text-white font-mono">${flight.base_price_first}</div>
                      <div className="text-[10px] font-mono text-zinc-400 mt-0.5">
                        {flight.available_first ?? flight.first_class_seats} seats left
                      </div>
                    </div>

                    {/* Select / Book Seat */}
                    <button
                      onClick={() => onSelectFlight(flight)}
                      className="px-5 py-3 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all shadow-md shadow-white/5 shrink-0"
                    >
                      Select Seats
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}

            {flights.length === 0 && !loading && (
              <div className="text-center py-16 rounded-2xl border border-zinc-800 bg-zinc-950 p-8">
                <Plane className="w-10 h-10 text-zinc-600 mx-auto mb-3" />
                <h3 className="text-base font-bold text-white">No Flights Found</h3>
                <p className="text-xs text-zinc-500 mt-1">Try searching for origin "LHR" or "LHE" to destination "DXB".</p>
              </div>
            )}
          </div>
        )}

        {/* Multi-Leg Connecting Flights List */}
        {isConnectingMode && (
          <div className="grid grid-cols-1 gap-4">
            {connectingRoutes.map((route, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 space-y-4 hover:border-zinc-700 transition-all shadow-lg"
              >
                <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-white font-mono font-bold">
                      Connecting Itinerary #{idx + 1}
                    </span>
                    <span className="text-xs text-zinc-400 font-mono">
                      Layover at <strong className="text-white">{route.layover_airport}</strong> ({route.layover_duration_hours} hrs)
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-zinc-400">Total Combined Fare: </span>
                    <span className="text-base font-extrabold text-white font-mono">${route.total_price_economy} USD</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Leg 1 */}
                  <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
                    <div className="text-[11px] font-mono text-zinc-400 uppercase">Leg 1: {route.leg1.flight_number}</div>
                    <div className="text-sm font-bold text-white mt-1">
                      {route.leg1.origin} ({route.leg1.origin_name}) → {route.leg1.destination}
                    </div>
                    <div className="text-[11px] text-zinc-400">
                      Departs: {new Date(route.leg1.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>

                  {/* Leg 2 */}
                  <div className="p-3.5 rounded-xl bg-zinc-900 border border-zinc-800/80 space-y-1">
                    <div className="text-xs font-bold text-white font-mono flex items-center justify-between">
                      <span>{route.leg2.flight_number} (Leg 2)</span>
                      <span className="text-[10px] text-zinc-400">{route.leg2.destination}</span>
                    </div>
                    <div className="text-xs text-zinc-300 font-mono font-medium">
                      {route.leg2.origin} → {route.leg2.destination} ({route.leg2.destination_name})
                    </div>
                    <div className="text-xs text-zinc-400 mt-1 font-mono">
                      Departs: {new Date(route.leg2.departure_time).toLocaleString()}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => onSelectFlight(route.leg1)}
                    className="px-5 py-2.5 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-xs flex items-center gap-2 transition-all"
                  >
                    Book Itinerary (Select Leg 1 Seats)
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
