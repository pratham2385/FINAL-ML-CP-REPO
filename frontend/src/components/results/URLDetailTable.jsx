import React, { useState } from 'react';
import { Globe, ShieldAlert, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { formatPercent } from '../../utils/formatters';

export function URLDetailTable({ urls = [] }) {
  const [expandedIndex, setExpandedIndex] = useState(null);

  if (!urls || urls.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 text-center text-xs text-slate-400">
        No embedded URLs detected in the email body.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#14171b] overflow-hidden">
      <div className="p-4 border-b border-white/[0.08] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-slate-300" />
          <h4 className="text-sm font-semibold text-white">Extracted Embedded URLs ({urls.length})</h4>
        </div>
        <span className="text-xs text-slate-400 font-mono">Stream 1 Lexical Analysis</span>
      </div>

      <div className="divide-y divide-white/[0.06]">
        {urls.map((u, idx) => {
          const isPhish = u.is_phishing;
          const prob = (u.phishing_probability || 0) * 100;
          const isExpanded = expandedIndex === idx;

          return (
            <div key={idx} className="p-4 hover:bg-[#181c23]/60 transition-colors">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 font-mono text-xs text-slate-200 break-all">
                    <span>{u.url}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs font-mono tabular-nums text-slate-400">
                    Phish prob:{' '}
                    <span className={isPhish ? 'text-[#ff8182] font-semibold' : 'text-slate-300'}>
                      {formatPercent(prob)}
                    </span>
                  </span>

                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${
                      isPhish
                        ? 'bg-[#cf222e]/15 text-[#ff8182] border-[#cf222e]/40'
                        : 'bg-[#2da44e]/15 text-[#56d364] border-[#2da44e]/40'
                    }`}
                  >
                    {isPhish ? <ShieldAlert className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
                    <span>{u.label || (isPhish ? 'Phishing' : 'Legitimate')}</span>
                  </span>

                  {u.features && (
                    <button
                      type="button"
                      onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                      className="p-1 rounded text-slate-400 hover:text-white hover:bg-[#1c2027] transition-colors"
                      title="Inspect features"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  )}
                </div>
              </div>

              {/* Expanded Features Panel */}
              {isExpanded && u.features && (
                <div className="mt-3 p-3 rounded-lg bg-[#101216] border border-white/[0.06] grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                  {Object.entries(u.features).map(([featKey, featVal]) => (
                    <div key={featKey} className="p-2 rounded bg-[#181c23] border border-white/[0.06]">
                      <div className="text-[10px] text-slate-400 truncate" title={featKey}>{featKey}</div>
                      <div className="text-slate-200 font-semibold tabular-nums mt-0.5">{String(featVal)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
