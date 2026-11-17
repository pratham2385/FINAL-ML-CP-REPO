import React, { useEffect, useState } from 'react';
import { X, Database, Copy, Check } from 'lucide-react';
import { getHistoryById } from '../api/historyService';
import { ThreatBadge } from '../components/common/ThreatBadge';
import { RiskGauge } from '../components/common/RiskGauge';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { formatDate } from '../utils/formatters';

export function HistoryDetailModal({ recordId, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' | 'raw_json'

  useEffect(() => {
    if (!recordId) return;
    setLoading(true);
    getHistoryById(recordId)
      .then((res) => setData(res))
      .catch((err) => setErrorMsg(err.message || 'Failed to load details'))
      .finally(() => setLoading(false));
  }, [recordId]);

  const handleCopyJSON = () => {
    if (!data) return;
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!recordId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-xl border border-white/[0.08] bg-[#14171b] shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/[0.08] bg-[#101216]">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#181c23] border border-white/[0.08] text-slate-300">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-white font-mono">
                  Audit record #{recordId}
                </h3>
                {data && <ThreatBadge threatLevel={data.threat_level} size="sm" />}
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                {data ? formatDate(data.created_at) : 'Loading audit trail...'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-[#181c23] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Tabs */}
        <div className="flex border-b border-white/[0.08] px-4 pt-2 bg-[#101216]/60 gap-4 text-xs font-mono">
          <button
            onClick={() => setActiveTab('summary')}
            className={`pb-2 font-medium transition-colors border-b-2 ${
              activeTab === 'summary'
                ? 'border-[#1f6feb] text-white'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Inspection summary
          </button>
          <button
            onClick={() => setActiveTab('raw_json')}
            className={`pb-2 font-medium transition-colors border-b-2 ${
              activeTab === 'raw_json'
                ? 'border-[#1f6feb] text-white'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Complete JSON payload
          </button>
        </div>

        {/* Modal Body Content */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          {loading ? (
            <LoadingSkeleton rows={6} />
          ) : errorMsg ? (
            <div className="p-3.5 rounded-lg bg-[#1a1416] border border-[#cf222e]/40 text-[#ff8182] text-xs">
              {errorMsg}
            </div>
          ) : activeTab === 'raw_json' ? (
            <div className="relative">
              <button
                onClick={handleCopyJSON}
                className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded text-xs font-mono bg-[#181c23] hover:bg-[#1f242d] text-slate-200 flex items-center gap-1.5 border border-white/[0.08] transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-[#56d364]" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
                <span>{copied ? 'Copied' : 'Copy JSON'}</span>
              </button>
              <pre className="p-3.5 rounded-lg bg-[#0d0f12] border border-white/[0.06] text-slate-300 font-mono text-xs overflow-x-auto max-h-[50vh]">
                {JSON.stringify(data.complete_analysis_result, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Top Banner Row */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-lg bg-[#181c23] border border-white/[0.08]">
                <div>
                  <span className="text-[11px] text-slate-400 font-mono">Overall verdict</span>
                  <div className="text-lg font-semibold text-white mt-0.5 capitalize">{data.overall_verdict}</div>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs text-slate-400 font-mono">Recommended action:</span>
                    <span className="px-2 py-0.5 rounded bg-[#101216] border border-white/[0.08] text-xs font-mono text-slate-200 font-medium">
                      {data.recommended_action}
                    </span>
                  </div>
                </div>

                <RiskGauge score={data.risk_score} size={84} strokeWidth={7} />
              </div>

              {data.complete_analysis_result?.verdict_explanation && (
                <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08] text-xs text-slate-300 leading-relaxed font-sans">
                  <span className="font-semibold text-white font-mono text-[11px] block mb-1">
                    Security verdict explanation:
                  </span>
                  {data.complete_analysis_result.verdict_explanation}
                </div>
              )}

              {/* Target / Subject Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
                  <span className="text-slate-400 text-[10px] block">Analysis modality:</span>
                  <span className="text-white font-medium capitalize">{data.analysis_type}</span>
                </div>

                <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
                  <span className="text-slate-400 text-[10px] block">Target subject / URL:</span>
                  <span className="text-slate-200 break-all">{data.subject || data.submitted_url || '—'}</span>
                </div>

                {data.email_prediction && (
                  <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
                    <span className="text-slate-400 text-[10px] block">Email classification:</span>
                    <span className={data.email_prediction === 'Spam' ? 'text-[#e3b341] font-semibold' : 'text-[#56d364] font-semibold'}>
                      {data.email_prediction}
                    </span>
                  </div>
                )}

                {data.spam_probability !== null && (
                  <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
                    <span className="text-slate-400 text-[10px] block">Spam probability:</span>
                    <span className="text-white font-semibold tabular-nums">{(data.spam_probability * 100).toFixed(1)}%</span>
                  </div>
                )}
              </div>

              {/* Extracted URLs List */}
              <div>
                <h4 className="text-xs font-mono text-slate-400 mb-2">
                  Discovered hyperlinks ({data.extracted_urls?.length || 0})
                </h4>
                {data.extracted_urls && data.extracted_urls.length > 0 ? (
                  <div className="space-y-1.5">
                    {data.extracted_urls.map((u, i) => (
                      <div key={i} className="p-2 rounded bg-[#101216] border border-white/[0.06] text-xs font-mono text-slate-300 break-all">
                        {u}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 font-mono">No hyperlinks recorded for this scan.</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
