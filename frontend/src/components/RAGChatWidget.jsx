import React, { useState } from 'react';
import { X, Sparkles, Send, Bot, User as UserIcon, CheckCircle2, ShieldCheck, AlertCircle, ArrowRight } from 'lucide-react';
import api from '../api/client';
import { useNotification } from '../context/NotificationContext';
import { useAuth } from '../context/AuthContext';

// Clean Rich Markdown Formatter Component
function FormattedMarkdown({ text }) {
  if (!text) return null;

  // Split lines
  const lines = text.split('\n');
  const elements = [];

  const parseInline = (line, keyPrefix) => {
    // Split by code, bold, italic
    const parts = line.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={`${keyPrefix}-${i}`} className="text-white font-bold">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={`${keyPrefix}-${i}`} className="text-zinc-300 italic">{part.slice(1, -1)}</em>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={`${keyPrefix}-${i}`} className="px-1 py-0.5 rounded bg-zinc-800 text-zinc-200 font-mono text-xs">{part.slice(1, -1)}</code>;
      }
      return part;
    });
  };

  let listItems = [];
  let inList = false;

  const flushList = (key) => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${key}`} className="space-y-1.5 my-2 pl-1">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    if (!trimmed) {
      flushList(idx);
      return;
    }

    // Headers: ### or ## or #
    if (trimmed.startsWith('### ') || trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
      flushList(idx);
      const cleanHeader = trimmed.replace(/^#+\s+/, '');
      elements.push(
        <div key={`h-${idx}`} className="font-extrabold text-white text-sm mt-3 mb-1 flex items-center gap-1.5 border-b border-zinc-800/80 pb-1">
          <span className="w-1.5 h-1.5 rounded-full bg-white shrink-0" />
          <span>{parseInline(cleanHeader, `h-${idx}`)}</span>
        </div>
      );
      return;
    }

    // Bullet Points: - or *
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      inList = true;
      const cleanBullet = trimmed.replace(/^[-*]\s+/, '');
      listItems.push(
        <li key={`bullet-${idx}`} className="flex items-start gap-2 text-zinc-300 text-xs sm:text-sm leading-relaxed">
          <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 mt-1.5 shrink-0" />
          <span className="flex-1">{parseInline(cleanBullet, `b-${idx}`)}</span>
        </li>
      );
      return;
    }

    // Numbered List: 1. 2. etc.
    const numMatch = trimmed.match(/^(\d+)\.\s+(.+)$/);
    if (numMatch) {
      inList = true;
      const num = numMatch[1];
      const cleanNumText = numMatch[2];
      listItems.push(
        <li key={`num-${idx}`} className="flex items-start gap-2 text-zinc-300 text-xs sm:text-sm leading-relaxed">
          <span className="px-1.5 py-0.2 rounded bg-zinc-800 text-[10px] font-mono text-zinc-300 shrink-0 font-bold mt-0.5">{num}</span>
          <span className="flex-1">{parseInline(cleanNumText, `n-${idx}`)}</span>
        </li>
      );
      return;
    }

    // Regular Paragraph
    flushList(idx);
    elements.push(
      <p key={`p-${idx}`} className="my-1.5 text-zinc-300 leading-relaxed text-xs sm:text-sm">
        {parseInline(trimmed, `p-${idx}`)}
      </p>
    );
  });

  flushList('end');
  return <div className="space-y-1">{elements}</div>;
}

export default function RAGChatWidget({ isOpen, onClose }) {
  const { user } = useAuth() || {};
  const [query, setQuery] = useState('');
  const [pnr, setPnr] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your **AerOps AI Policy Assistant**.\n\nAsk me anything regarding:\n- **Ticket Cancellations & Cash/Credit Refunds**\n- **Fare Class Rules (Flexible vs Basic Economy)**\n- **Checked & Cabin Baggage Allowances**\n- **Flight Delays, Reschedules & Compensations**\n\n*You can optionally enter your 6-character PNR above for instant personalized fare validation.*',
    },
  ]);
  const [loading, setLoading] = useState(false);
  const { addToast } = useNotification();

  if (!isOpen) return null;

  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const currentQuery = query.trim();
    const currentPnr = pnr.trim();
    const userMessage = { role: 'user', content: currentQuery, pnr: currentPnr || null };
    
    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      const res = await api.post('/rag/query', {
        query: currentQuery,
        booking_id: currentPnr || undefined,
        recipient_email: (user && user.email) ? user.email : 'customer@flightsystem.com',
      });

      const responseText = typeof res.draft_response === 'string' 
        ? res.draft_response 
        : (res.message || 'Policy analysis completed.');

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: responseText,
          isBookingAware: res.is_booking_aware,
          category: res.policy_category_matched,
        },
      ]);
    } catch (err) {
      const errorMsg = typeof err.message === 'string' ? err.message : 'Failed to query policy assistant';
      addToast(errorMsg, 'error');
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an issue connecting to the AI policy vector engine. Please verify the backend is running.',
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl h-[620px] flex flex-col rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800/80 bg-zinc-900/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white text-black flex items-center justify-center font-bold">
              <Sparkles className="w-5 h-5 text-black" />
            </div>
            <div>
              <div className="text-sm font-extrabold text-white flex items-center gap-2">
                AerOps Flight Policy AI
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">Semantic RAG Engine</span>
              </div>
              <div className="text-[11px] text-zinc-400 font-mono">ChromaDB Policy Vector Store + Live PNR Context</div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-white p-1 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* PNR Context Bar */}
        <div className="px-6 py-2 bg-black border-b border-zinc-800/60 flex items-center gap-3">
          <span className="text-[11px] font-mono text-zinc-400 uppercase">Optional PNR Context:</span>
          <input
            type="text"
            placeholder="e.g. 6-Char PNR"
            value={pnr}
            onChange={(e) => setPnr(e.target.value.toUpperCase())}
            className="px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-xs text-white font-mono uppercase focus:outline-none focus:border-white transition-colors w-36"
          />
          <span className="text-[10px] text-zinc-500 hidden sm:inline">
            Matches your specific Basic/Flexible fare rule in Neon DB
          </span>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-white text-black font-semibold'
                    : 'bg-zinc-900/90 border border-zinc-800 text-zinc-200'
                }`}
              >
                {msg.pnr && (
                  <div className="text-[10px] font-mono uppercase text-zinc-500 mb-1 font-bold">
                    PNR Context: {msg.pnr}
                  </div>
                )}

                {msg.role === 'assistant' ? (
                  <FormattedMarkdown text={msg.content} />
                ) : (
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                )}

                {msg.isBookingAware && (
                  <div className="mt-2.5 pt-2 border-t border-zinc-800 flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Live Booking & Fare Rules Validated from Neon DB</span>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-white text-black flex items-center justify-center font-bold shrink-0">
                  <UserIcon className="w-4 h-4 text-black" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 justify-start items-center">
              <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="px-4 py-3 rounded-2xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-400 flex items-center gap-2 font-mono">
                <div className="w-2 h-2 rounded-full bg-white animate-ping" />
                Searching policy vector store & generating answer...
              </div>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} className="p-4 border-t border-zinc-800 bg-zinc-950 flex items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about cancellation fees, refund rules, schedule delays..."
            className="flex-1 px-4 py-3 rounded-xl bg-zinc-900 border border-zinc-800 text-white text-sm focus:outline-none focus:border-white transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-3 rounded-xl bg-white hover:bg-zinc-200 text-black font-bold text-sm flex items-center justify-center transition-all disabled:opacity-50 shadow-md shadow-white/10"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
