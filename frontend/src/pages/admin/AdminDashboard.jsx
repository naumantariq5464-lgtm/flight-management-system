import React, { useState, useEffect } from 'react';
import { 
  Activity, Plane, DollarSign, Users, RefreshCw, AlertTriangle, 
  CheckCircle2, Plus, Calendar, XCircle, ShieldAlert, Sparkles, 
  FileText, ArrowRight, Eye, Check, X
} from 'lucide-react';
import api from '../../api/client';
import { useNotification } from '../../context/NotificationContext';
import { useAuth } from '../../context/AuthContext';

export default function AdminDashboard() {
  const { isSuperAdmin, isAgent } = useAuth();
  const { addToast } = useNotification();

  const [activeTab, setActiveTab] = useState('kpis'); // kpis, flights, refunds, rag, audit
  const [report, setReport] = useState(null);
  const [flights, setFlights] = useState([]);
  const [refunds, setRefunds] = useState([]);
  const [ragApprovals, setRagApprovals] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Flight Create Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [flightNumber, setFlightNumber] = useState('');
  const [origin, setOrigin] = useState('LHR');
  const [originName, setOriginName] = useState('London Heathrow Airport');
  const [destination, setDestination] = useState('DXB');
  const [destinationName, setDestinationName] = useState('Dubai International Airport');
  const [depTime, setDepTime] = useState('');
  const [arrTime, setArrTime] = useState('');
  const [capacity, setCapacity] = useState(100);
  const [firstSeats, setFirstSeats] = useState(20);
  const [bizSeats, setBizSeats] = useState(30);
  const [ecoSeats, setEcoSeats] = useState(50);
  const [pEco, setPEco] = useState('450.00');
  const [pBiz, setPBiz] = useState('1200.00');
  const [pFirst, setPFirst] = useState('2400.00');
  const [creatingFlight, setCreatingFlight] = useState(false);

  // Schedule Edit Modal State
  const [editFlight, setEditFlight] = useState(null);
  const [editDepTime, setEditDepTime] = useState('');
  const [editArrTime, setEditArrTime] = useState('');

  useEffect(() => {
    fetchAllAdminData();
  }, []);

  const fetchAllAdminData = async () => {
    setLoading(true);
    try {
      const [repData, flightsData, refData, ragData, auditData] = await Promise.allSettled([
        api.get('/admin/reports/daily-summary'),
        api.get('/flights/search'),
        api.get('/admin/refunds/pending'),
        api.get('/admin/rag/pending'),
        api.get('/admin/audit-logs'),
      ]);

      if (repData.status === 'fulfilled') setReport(repData.value);
      if (flightsData.status === 'fulfilled') setFlights(flightsData.value);
      if (refData.status === 'fulfilled') setRefunds(refData.value);
      if (ragData.status === 'fulfilled') setRagApprovals(ragData.value);
      if (auditData.status === 'fulfilled') setAuditLogs(auditData.value);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Seat sum validation rule: First + Biz + Eco === Capacity
  const seatSumValid = parseInt(firstSeats || 0) + parseInt(bizSeats || 0) + parseInt(ecoSeats || 0) === parseInt(capacity || 0);

  const handleCreateFlight = async (e) => {
    e.preventDefault();
    if (!seatSumValid) {
      addToast(`Seat classes (${parseInt(firstSeats) + parseInt(bizSeats) + parseInt(ecoSeats)}) must sum exactly to capacity (${capacity})!`, 'error');
      return;
    }

    setCreatingFlight(true);
    try {
      await api.post('/admin/flights', {
        flight_number: flightNumber.toUpperCase(),
        origin: origin.toUpperCase(),
        origin_name: originName,
        destination: destination.toUpperCase(),
        destination_name: destinationName,
        departure_time: new Date(depTime).toISOString(),
        arrival_time: new Date(arrTime).toISOString(),
        aircraft_capacity: parseInt(capacity),
        first_class_seats: parseInt(firstSeats),
        business_class_seats: parseInt(bizSeats),
        economy_seats: parseInt(ecoSeats),
        base_price_economy: parseFloat(pEco),
        base_price_business: parseFloat(pBiz),
        base_price_first: parseFloat(pFirst),
        currency: 'USD',
        overbooking_policy: 'HARD_NEVER_OVERSELL',
      });

      addToast(`Flight ${flightNumber} created with 100-seat layout!`, 'success');
      setCreateModalOpen(false);
      await fetchAllAdminData();
    } catch (err) {
      addToast(err.message || 'Failed to create flight', 'error');
    } finally {
      setCreatingFlight(false);
    }
  };

  const handleCancelFlight = async (flightId, flightNo) => {
    if (!confirm(`Are you sure you want to CANCEL flight ${flightNo}? This triggers automated refund/rebooking cascades and notifies n8n!`)) return;

    try {
      await api.post(`/admin/flights/${flightId}/cancel`, {
        reason: 'Operational cancellation by Operations Admin',
      });
      addToast(`Flight ${flightNo} cancelled. Downstream refund cascades triggered!`, 'success');
      fetchAllAdminData();
    } catch (err) {
      addToast(err.message || 'Failed to cancel flight', 'error');
    }
  };

  const handleEditSchedule = async (e) => {
    e.preventDefault();
    if (!editFlight) return;

    try {
      await api.put(`/admin/flights/${editFlight.id}/schedule`, {
        new_departure_time: new Date(editDepTime).toISOString(),
        new_arrival_time: new Date(editArrTime).toISOString(),
        schedule_change_reason: 'Weather & Air Traffic Control rescheduling',
      });

      addToast(`Flight ${editFlight.flight_number} schedule updated! Affected bookings status updated.`, 'success');
      setEditFlight(null);
      fetchAllAdminData();
    } catch (err) {
      addToast(err.message || 'Failed to edit schedule', 'error');
    }
  };

  const handleApproveRefund = async (refundId) => {
    try {
      await api.post(`/admin/refunds/${refundId}/approve`);
      addToast('Refund approved and scheduled for bank payout!', 'success');
      fetchAllAdminData();
    } catch (err) {
      addToast(err.message || 'Failed to approve refund', 'error');
    }
  };

  const handleApproveRAG = async (approvalId, action) => {
    try {
      await api.post(`/admin/rag/${approvalId}/decision`, { action });
      addToast(`RAG response draft ${action === 'APPROVE' ? 'Approved & Dispatched' : 'Rejected'}!`, 'success');
      fetchAllAdminData();
    } catch (err) {
      addToast(err.message || 'Action failed', 'error');
    }
  };

  if (!isSuperAdmin && !isAgent) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto text-zinc-400">
          <ShieldAlert className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-xl font-bold text-white">Administrator Access Required</h2>
        <p className="text-xs text-zinc-400">
          You are currently signed in as a standard Customer. Operations Dashboard requires Super Admin credentials.
        </p>
        <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 font-mono text-xs text-zinc-400">
          Admin Login: <span className="text-white font-bold">admin@flightsystem.com</span> / <span className="text-white font-bold">Admin@123456</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Admin Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-white text-black text-xs font-mono font-black">
              ADMIN · OPS CONTROL
            </span>
            <span className="text-xs text-zinc-500 font-mono">FastAPI Write Ledger + n8n Dual-Writer</span>
          </div>
          <h1 className="text-3xl font-black text-white mt-1">Flight Operations Console</h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAllAdminData}
            disabled={loading}
            className="p-2.5 rounded-xl border border-zinc-800 hover:border-zinc-600 text-zinc-400 hover:text-white transition-colors"
            title="Refresh All Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          {isSuperAdmin && (
            <button
              onClick={() => setCreateModalOpen(true)}
              className="px-4 py-2.5 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-xs sm:text-sm flex items-center gap-2 transition-all shadow-md shadow-white/5"
            >
              <Plus className="w-4 h-4" />
              Create Flight
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-zinc-400 text-xs font-mono">
            <span>TOTAL REVENUE</span>
            <DollarSign className="w-4 h-4 text-white" />
          </div>
          <div className="text-2xl font-black font-mono text-white">
            ${(report?.total_revenue !== undefined && report?.total_revenue !== null ? Number(report.total_revenue).toLocaleString() : '0')} USD
          </div>
          <div className="text-[10px] text-zinc-500 font-mono">Live transactional bookings</div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-zinc-400 text-xs font-mono">
            <span>AVG LOAD FACTOR</span>
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div className="text-2xl font-black font-mono text-white">
            {report?.load_factor_percentage !== undefined && report?.load_factor_percentage !== null ? `${report.load_factor_percentage}%` : '0.0%'}
          </div>
          <div className="text-[10px] text-zinc-500 font-mono">Across 100-seat cabins</div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-zinc-400 text-xs font-mono">
            <span>ACTIVE FLIGHTS</span>
            <Plane className="w-4 h-4 text-white" />
          </div>
          <div className="text-2xl font-black font-mono text-white">
            {flights.filter((f) => f.status === 'SCHEDULED').length}
          </div>
          <div className="text-[10px] text-zinc-500 font-mono">Scheduled & in-flight</div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-zinc-400 text-xs font-mono">
            <span>PENDING REFUNDS / SLA</span>
            <AlertTriangle className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-2xl font-black font-mono text-white">
            {refunds.length}
          </div>
          <div className="text-[10px] text-zinc-500 font-mono">Awaiting human sign-off</div>
        </div>

      </div>

      {/* Admin Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-zinc-800 pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('kpis')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'kpis' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'
          }`}
        >
          Flight Schedule & Operations
        </button>
        <button
          onClick={() => setActiveTab('refunds')}
          className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
            activeTab === 'refunds' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'
          }`}
        >
          Refund Approvals
          {refunds.length > 0 && (
            <span className="w-4 h-4 rounded-full bg-zinc-700 text-white text-[9px] flex items-center justify-center font-mono">
              {refunds.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('rag')}
          className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
            activeTab === 'rag' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          RAG AI Drafts Queue
          {ragApprovals.length > 0 && (
            <span className="w-4 h-4 rounded-full bg-zinc-700 text-white text-[9px] flex items-center justify-center font-mono">
              {ragApprovals.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'audit' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'
          }`}
        >
          Audit Ledger & Fraud Events
        </button>
      </div>

      {/* Tab 1: Flights List & Operations */}
      {activeTab === 'kpis' && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white">Managed Flights & Inventory</h2>
            <span className="text-xs text-zinc-500 font-mono">Showing {flights.length} flights</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-zinc-800 text-zinc-400 font-mono uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-3">Flight #</th>
                  <th className="py-3 px-3">Route</th>
                  <th className="py-3 px-3">Departure / Arrival</th>
                  <th className="py-3 px-3">Seat Allocations (F/B/E)</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900 font-mono">
                {flights.map((f) => (
                  <tr key={f.id} className="hover:bg-zinc-900/40 transition-colors">
                    <td className="py-3 px-3 font-bold text-white">{f.flight_number}</td>
                    <td className="py-3 px-3 text-zinc-300">
                      {f.origin} → {f.destination}
                    </td>
                    <td className="py-3 px-3 text-zinc-400">
                      {new Date(f.departure_time).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-zinc-300">
                      {f.first_class_seats}F / {f.business_class_seats}B / {f.economy_seats}E (Total: {f.aircraft_capacity})
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        f.status === 'SCHEDULED' ? 'bg-emerald-950 text-emerald-300' : 'bg-red-950 text-red-300'
                      }`}>
                        {f.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right space-x-2">
                      {f.status === 'SCHEDULED' && (
                        <>
                          <button
                            onClick={() => {
                              setEditFlight(f);
                              setEditDepTime(f.departure_time.slice(0, 16));
                              setEditArrTime(f.arrival_time.slice(0, 16));
                            }}
                            className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-[11px]"
                          >
                            Reschedule
                          </button>
                          <button
                            onClick={() => handleCancelFlight(f.id, f.flight_number)}
                            className="px-2.5 py-1 rounded bg-red-950 hover:bg-red-900 border border-red-800 text-red-200 text-[11px]"
                          >
                            Cancel
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Refund Approvals */}
      {activeTab === 'refunds' && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white">Pending Refund & Compensation Requests</h2>
            <span className="text-xs text-zinc-500 font-mono">Requires human sign-off</span>
          </div>

          <div className="space-y-3">
            {refunds.map((ref) => (
              <div key={ref.id} className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
                <div>
                  <div className="font-bold text-white flex items-center gap-2">
                    Booking PNR: {ref.booking_pnr || 'PNR-10293'}
                    <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">
                      {ref.refund_type || 'IN_POLICY'}
                    </span>
                  </div>
                  <div className="text-zinc-400 mt-1 font-mono">
                    Refund Amount: <strong className="text-white">${ref.refund_amount} USD</strong> · Reason: {ref.reason}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleApproveRefund(ref.id)}
                    className="px-4 py-2 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-xs flex items-center gap-1"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Approve Payout
                  </button>
                </div>
              </div>
            ))}

            {refunds.length === 0 && (
              <div className="text-center py-12 text-zinc-500 font-mono text-xs">
                ✓ No pending refund requests in queue.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: RAG AI Drafts Queue (Human-in-the-loop) */}
      {activeTab === 'rag' && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl space-y-4">
          <div>
            <h2 className="text-base font-bold text-white">RAG Policy AI Human Approval Gate</h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Review AI-drafted email responses before they are dispatched to customers via n8n Gmail.
            </p>
          </div>

          <div className="space-y-4">
            {ragApprovals.map((item) => (
              <div key={item.id} className="p-5 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-zinc-400">Customer Question:</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">
                    Target Fare: {item.booking_fare_type || 'Flexible'}
                  </span>
                </div>
                <div className="text-sm font-bold text-white">"{item.question}"</div>

                <div className="p-3.5 rounded-xl bg-black border border-zinc-800 text-zinc-300 leading-relaxed font-mono text-xs">
                  {item.draft_answer}
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => handleApproveRAG(item.id, 'REJECT')}
                    className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-bold"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleApproveRAG(item.id, 'APPROVE')}
                    className="px-5 py-2 rounded-xl bg-white hover:bg-zinc-200 text-black text-xs font-extrabold flex items-center gap-1.5"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Approve & Email Customer
                  </button>
                </div>
              </div>
            ))}

            {ragApprovals.length === 0 && (
              <div className="text-center py-12 text-zinc-500 font-mono text-xs">
                ✓ All RAG drafts approved. Queue is clean.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Audit Logs & Security */}
      {activeTab === 'audit' && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white">Immutable Regulatory Audit Trail</h2>
            <span className="text-xs text-zinc-500 font-mono">Neon DB Ledger</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-zinc-800 text-zinc-400 font-mono uppercase text-[10px]">
                <tr>
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Action</th>
                  <th className="py-2 px-3">Actor / Email</th>
                  <th className="py-2 px-3">Source</th>
                  <th className="py-2 px-3">Entity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900 font-mono text-[11px]">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-zinc-900/40">
                    <td className="py-2 px-3 text-zinc-500">{new Date(log.created_at).toLocaleString()}</td>
                    <td className="py-2 px-3 font-bold text-white">{log.action}</td>
                    <td className="py-2 px-3 text-zinc-300">{log.actor_email}</td>
                    <td className="py-2 px-3 text-zinc-400">{log.source}</td>
                    <td className="py-2 px-3 text-zinc-400">{log.entity_type} ({log.entity_id?.slice(0, 8)})</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Create Flight */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in">
          <div className="relative w-full max-w-2xl rounded-3xl border border-zinc-800 bg-zinc-950 p-6 sm:p-8 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
              <h2 className="text-xl font-extrabold text-white">Create New Flight (100-Seat Auto Map)</h2>
              <button onClick={() => setCreateModalOpen(false)} className="text-zinc-500 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleCreateFlight} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 font-mono mb-1 uppercase">Flight Number</label>
                  <input
                    type="text"
                    required
                    value={flightNumber}
                    onChange={(e) => setFlightNumber(e.target.value.toUpperCase())}
                    placeholder="e.g. BA-202"
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono uppercase focus:outline-none focus:border-white"
                  />
                </div>
                <div>
                  <label className="block text-zinc-400 font-mono mb-1 uppercase">Aircraft Capacity</label>
                  <input
                    type="number"
                    required
                    value={capacity}
                    onChange={(e) => setCapacity(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono focus:outline-none focus:border-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 font-mono mb-1 uppercase">Origin Code</label>
                  <input
                    type="text"
                    required
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono uppercase focus:outline-none focus:border-white"
                  />
                </div>
                <div>
                  <label className="block text-zinc-400 font-mono mb-1 uppercase">Destination Code</label>
                  <input
                    type="text"
                    required
                    value={destination}
                    onChange={(e) => setDestination(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono uppercase focus:outline-none focus:border-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 font-mono mb-1 uppercase">Departure Datetime</label>
                  <input
                    type="datetime-local"
                    required
                    value={depTime}
                    onChange={(e) => setDepTime(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white focus:outline-none focus:border-white"
                  />
                </div>
                <div>
                  <label className="block text-zinc-400 font-mono mb-1 uppercase">Arrival Datetime</label>
                  <input
                    type="datetime-local"
                    required
                    value={arrTime}
                    onChange={(e) => setArrTime(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white focus:outline-none focus:border-white"
                  />
                </div>
              </div>

              {/* Seat Allocations & Sum Validator */}
              <div className="p-4 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-zinc-300 uppercase">Seat Class Allocations</span>
                  <span className={`font-mono text-[11px] font-bold ${seatSumValid ? 'text-emerald-400' : 'text-red-400'}`}>
                    Sum: {parseInt(firstSeats || 0) + parseInt(bizSeats || 0) + parseInt(ecoSeats || 0)} / {capacity}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-500 mb-1">First Class</label>
                    <input
                      type="number"
                      value={firstSeats}
                      onChange={(e) => setFirstSeats(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-black border border-zinc-800 text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-500 mb-1">Business</label>
                    <input
                      type="number"
                      value={bizSeats}
                      onChange={(e) => setBizSeats(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-black border border-zinc-800 text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-500 mb-1">Economy</label>
                    <input
                      type="number"
                      value={ecoSeats}
                      onChange={(e) => setEcoSeats(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-black border border-zinc-800 text-white font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Base Prices */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-[10px] font-mono text-zinc-500 mb-1">Price First ($)</label>
                  <input
                    type="number"
                    value={pFirst}
                    onChange={(e) => setPFirst(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono text-zinc-500 mb-1">Price Biz ($)</label>
                  <input
                    type="number"
                    value={pBiz}
                    onChange={(e) => setPBiz(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono text-zinc-500 mb-1">Price Eco ($)</label>
                  <input
                    type="number"
                    value={pEco}
                    onChange={(e) => setPEco(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white font-mono"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={!seatSumValid || creatingFlight}
                className="w-full py-3.5 rounded-2xl bg-white hover:bg-zinc-200 text-black font-extrabold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40"
              >
                {creatingFlight ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-black" />
                    Creating Flight & 100 Seats in Neon DB...
                  </>
                ) : (
                  <>
                    Create Flight & Generate Seat Map
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Reschedule Flight */}
      {editFlight && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in">
          <div className="relative w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <h3 className="text-base font-bold text-white">Reschedule Flight {editFlight.flight_number}</h3>
              <button onClick={() => setEditFlight(null)} className="text-zinc-500 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleEditSchedule} className="space-y-4 text-xs">
              <div>
                <label className="block text-zinc-400 font-mono mb-1 uppercase">New Departure Datetime</label>
                <input
                  type="datetime-local"
                  required
                  value={editDepTime}
                  onChange={(e) => setEditDepTime(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white focus:outline-none focus:border-white"
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-mono mb-1 uppercase">New Arrival Datetime</label>
                <input
                  type="datetime-local"
                  required
                  value={editArrTime}
                  onChange={(e) => setEditArrTime(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-white focus:outline-none focus:border-white"
                />
              </div>

              <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800 text-[10px] text-zinc-400 font-mono">
                ⚠️ Cascades schedule change notification to all booked passengers and updates booking status.
              </div>

              <button
                type="submit"
                className="w-full py-3 rounded-xl bg-white hover:bg-zinc-200 text-black font-extrabold text-xs"
              >
                Apply Schedule Change
              </button>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
