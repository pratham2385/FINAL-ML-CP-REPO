import React, { useState } from 'react';
import { Globe, ShieldAlert, CheckCircle, ChevronDown, ChevronUp, Layers } from 'lucide-react';
import { formatPercent } from '../../utils/formatters';

export function URLResultCard({ urlData }) {
  const [showFeatures, setShowFeatures] = useState(false);
  if (!urlData) return null;

  const isPhish = urlData.is_phishing;
  const phishProb = (urlData.phishing_probability || 0) * 100;
  const features = urlData.features || {};

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-slate-300 shrink-0" />
          <div className="overflow-hidden">
            <h3 className="text-sm font-semibold text-white">URL Phishing Analysis</h3>
            <p className="text-xs font-mono text-slate-400 truncate max-w-md">{urlData.url}</p>
          </div>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-mono font-medium border shrink-0 ${
            isPhish
              ? 'bg-[#cf222e]/15 text-[#ff8182] border-[#cf222e]/40'
              : 'bg-[#2da44e]/15 text-[#56d364] border-[#2da44e]/40'
          }`}
        >
          {isPhish ? <ShieldAlert className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
          <span>{urlData.classification || (isPhish ? 'Phishing' : 'Legitimate')}</span>
        </span>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
          <span className="text-xs text-slate-400 block">Phishing probability</span>
          <span className="text-xl font-semibold font-mono tabular-nums text-white mt-1 block">
            {formatPercent(phishProb)}
          </span>
          <div className="w-full bg-[#1c2027] h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${isPhish ? 'bg-[#cf222e]' : 'bg-[#2da44e]'}`}
              style={{ width: `${Math.min(phishProb, 100)}%` }}
            />
          </div>
        </div>

        <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
          <span className="text-xs text-slate-400 block">Confidence score</span>
          <span className="text-xl font-semibold font-mono tabular-nums text-slate-100 mt-1 block">
            {formatPercent(urlData.confidence_percent || 0)}
          </span>
          <span className="text-[11px] text-slate-500 mt-1 block">400-Tree Random Forest</span>
        </div>

        <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
          <span className="text-xs text-slate-400 block">Lexical inspection</span>
          <span className="text-xl font-semibold font-mono tabular-nums text-white mt-1 block">
            {Object.keys(features).length} Features
          </span>
          <span className="text-[11px] text-slate-500 mt-1 block">Dual-Level Structural Evaluation</span>
        </div>
      </div>

      {/* Toggle Features Section */}
      {Object.keys(features).length > 0 && (
        <div className="pt-1">
          <button
            type="button"
            onClick={() => setShowFeatures(!showFeatures)}
            className="flex items-center justify-between w-full p-2.5 rounded-lg bg-[#181c23] hover:bg-[#1f242d] border border-white/[0.08] text-xs font-medium text-slate-300 transition-colors"
          >
            <span className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-slate-400" />
              <span>Extracted Lexical Feature Vectors ({Object.keys(features).length})</span>
            </span>
            {showFeatures ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showFeatures && (
            <div className="mt-2.5 p-3 rounded-lg bg-[#101216] border border-white/[0.06] grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 text-xs font-mono">
              {Object.entries(features).map(([key, val]) => (
                <div key={key} className="p-2 rounded bg-[#181c23] border border-white/[0.06]">
                  <div className="text-[10px] text-slate-400 truncate" title={key}>
                    {key}
                  </div>
                  <div className="font-semibold text-slate-200 tabular-nums mt-0.5">{String(val)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
