import React from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  UserX,
  CreditCard,
  KeyRound,
  FileText,
  BadgeAlert,
  CheckCircle2
} from 'lucide-react';
import { formatPercent } from '../../utils/formatters';

export function PhishingIntentCard({ phishingIntent }) {
  if (!phishingIntent) return null;

  const {
    primary_intent,
    intent_risk_level = 'NONE',
    intent_score = 0,
    detected_signals = [],
    evidence = [],
    sender_indicators,
    mitigating_factors = []
  } = phishingIntent;

  const getCategoryLabel = (category) => {
    switch (category) {
      case 'BUSINESS_EMAIL_COMPROMISE':
        return 'Business Email Compromise (BEC)';
      case 'CREDENTIAL_THEFT':
        return 'Credential Theft & Account Access';
      case 'FINANCIAL_FRAUD':
        return 'Payment & Financial Fraud';
      case 'SOCIAL_ENGINEERING_IMPERSONATION':
        return 'Social Engineering & Impersonation';
      case 'MALICIOUS_DOCUMENT_LURE':
        return 'Malicious Document & Cloud Lure';
      case 'NONE':
      default:
        return 'No Deceptive Intent Detected';
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'BUSINESS_EMAIL_COMPROMISE':
        return <UserX className="w-4 h-4 text-[#ff8182]" />;
      case 'CREDENTIAL_THEFT':
        return <KeyRound className="w-4 h-4 text-[#ff8182]" />;
      case 'FINANCIAL_FRAUD':
        return <CreditCard className="w-4 h-4 text-[#e3b341]" />;
      case 'SOCIAL_ENGINEERING_IMPERSONATION':
        return <BadgeAlert className="w-4 h-4 text-[#d29922]" />;
      case 'MALICIOUS_DOCUMENT_LURE':
        return <FileText className="w-4 h-4 text-slate-300" />;
      case 'NONE':
      default:
        return <ShieldCheck className="w-4 h-4 text-[#56d364]" />;
    }
  };

  const getRiskBadge = (level) => {
    switch ((level || '').toUpperCase()) {
      case 'HIGH':
        return 'bg-[#cf222e]/15 text-[#ff8182] border-[#cf222e]/40';
      case 'MEDIUM':
        return 'bg-[#d29922]/15 text-[#e3b341] border-[#d29922]/40';
      case 'LOW':
        return 'bg-[#bb8009]/15 text-[#d29922] border-[#bb8009]/30';
      case 'NONE':
      default:
        return 'bg-[#2da44e]/15 text-[#56d364] border-[#2da44e]/35';
    }
  };

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-2">
          {getCategoryIcon(primary_intent)}
          <h3 className="text-sm font-semibold text-white">Phishing Intent Analysis</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Risk level:</span>
          <span
            className={`px-2 py-0.5 rounded text-xs font-mono font-medium border ${getRiskBadge(
              intent_risk_level
            )}`}
          >
            {intent_risk_level}
          </span>
        </div>
      </div>

      {/* Primary Category Banner */}
      <div className="p-3.5 rounded-lg bg-[#181c23] border border-white/[0.08] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-[11px] text-slate-400 block">Primary intent pattern</span>
          <span className="text-sm font-semibold text-white flex items-center gap-1.5 mt-0.5">
            {getCategoryLabel(primary_intent)}
          </span>
        </div>

        <div className="sm:text-right shrink-0">
          <span className="text-[11px] text-slate-400 block">Intent threat score</span>
          <span className="text-lg font-semibold font-mono tabular-nums text-white">
            {formatPercent(intent_score)}
          </span>
        </div>
      </div>

      {/* Sender & Content Indicators */}
      {detected_signals && detected_signals.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-xs text-slate-400 block">
            Detected attack signals & indicators
          </span>
          <div className="flex flex-wrap gap-2">
            {detected_signals.map((sig, idx) => (
              <span
                key={idx}
                className="px-2 py-1 rounded text-xs font-mono bg-[#101216] border border-white/[0.08] text-slate-200 flex items-center gap-1.5"
              >
                <AlertTriangle className="w-3 h-3 text-[#d29922] shrink-0" />
                <span>{sig}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Sender Diagnostics */}
      {sender_indicators?.sender_address && (
        <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08] text-xs font-mono space-y-1">
          <div className="text-slate-400 text-[11px]">Sender verification diagnostics:</div>
          <div className="text-slate-300 break-all">
            Sender: <span className="text-white font-medium">{sender_indicators.sender_address}</span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {sender_indicators.is_freemail && (
              <span className="px-2 py-0.5 rounded text-[11px] bg-[#d29922]/15 text-[#e3b341] border border-[#d29922]/35">
                Free webmail domain
              </span>
            )}
            {sender_indicators.display_name_impersonation && (
              <span className="px-2 py-0.5 rounded text-[11px] bg-[#cf222e]/15 text-[#ff8182] border border-[#cf222e]/35">
                Executive / authority display name mismatch
              </span>
            )}
            {!sender_indicators.is_freemail && !sender_indicators.display_name_impersonation && (
              <span className="px-2 py-0.5 rounded text-[11px] bg-[#101216] text-slate-400 border border-white/[0.06]">
                Standard sender syntax
              </span>
            )}
          </div>
        </div>
      )}

      {/* Specific Evidence & Reasons */}
      {evidence && evidence.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs text-slate-400 block">
            Evidence & evaluation reasons
          </span>
          <div className="space-y-1.5">
            {evidence.map((ev, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 p-2.5 rounded-lg bg-[#101216] border border-white/[0.06] text-xs text-slate-300 leading-relaxed font-sans"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 shrink-0" />
                <span>{ev}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mitigating Factors */}
      {mitigating_factors && mitigating_factors.length > 0 && (
        <div className="p-3 rounded-lg bg-[#101713] border border-[#2da44e]/30 text-xs text-[#56d364] flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 text-[#2da44e] shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block text-[#56d364]">Mitigating context:</span>
            <span className="text-slate-300">{mitigating_factors.join('; ')}</span>
          </div>
        </div>
      )}
    </div>
  );
}
