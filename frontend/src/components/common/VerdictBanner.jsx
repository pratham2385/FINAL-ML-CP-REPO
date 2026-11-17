import React from 'react';
import { Database } from 'lucide-react';
import { ThreatBadge } from './ThreatBadge';
import { RiskGauge } from './RiskGauge';
import { getThreatTierConfig } from '../../utils/formatters';
import { cn } from '../../utils/cn';

export function VerdictBanner({
  verdict,
  threatLevel,
  riskScore,
  recommendedAction,
  verdictExplanation,
  recordId,
  className
}) {
  const config = getThreatTierConfig(threatLevel || verdict);
  const isDangerous = (threatLevel || '').toUpperCase() === 'CRITICAL' || 
                      (threatLevel || '').toUpperCase() === 'HIGH' ||
                      (verdict || '').toUpperCase() === 'MALICIOUS';
  const isSuspicious = (threatLevel || '').toUpperCase() === 'MEDIUM' ||
                       (threatLevel || '').toUpperCase() === 'LOW_SUSPICIOUS' ||
                       (verdict || '').toUpperCase() === 'SUSPICIOUS';

  const getActionBadgeColor = (action) => {
    switch (action) {
      case 'QUARANTINE_AND_BLOCK':
      case 'BLOCK':
        return 'bg-[#cf222e]/15 text-[#ff8182] border-[#cf222e]/40';
      case 'MOVE_TO_JUNK':
      case 'WARN_USER':
        return 'bg-[#d29922]/15 text-[#e3b341] border-[#d29922]/40';
      case 'ALLOW':
      default:
        return 'bg-[#2da44e]/15 text-[#56d364] border-[#2da44e]/40';
    }
  };

  const defaultExplanation = isDangerous
    ? 'High-confidence indicators of malicious deception or phishing attack detected. Immediate containment advised.'
    : isSuspicious
    ? 'Anomalous or unsolicited communication indicators detected. Exercise caution before trusting links or sender requests.'
    : 'Security parameters conform to normal legitimate communication patterns. No anomalous indicators found.';

  const displayVerdict = (verdict || 'Threat analysis complete');

  return (
    <div
      className={cn(
        'relative rounded-xl border p-5 transition-colors',
        config.bg,
        className
      )}
    >
      <div className="flex flex-col md:flex-row items-center justify-between gap-5">
        {/* Left Side: Verdict & Action */}
        <div className="flex-1 space-y-2.5 text-center md:text-left">
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-2">
            <ThreatBadge threatLevel={threatLevel || verdict} size="md" />
            <span className="inline-flex items-center text-xs text-slate-300 bg-white/[0.04] border border-white/[0.08] rounded px-2 py-0.5">
              Overall Security Verdict
            </span>
            {recordId && (
              <span className="inline-flex items-center gap-1 text-xs font-mono text-slate-400 bg-white/[0.03] border border-white/[0.06] rounded px-2 py-0.5">
                <Database className="w-3 h-3 text-slate-400" />
                <span>Audit ID: #{recordId}</span>
              </span>
            )}
          </div>

          <div>
            <h2 className="text-xl md:text-2xl font-semibold tracking-tight text-white capitalize">
              {displayVerdict}
            </h2>
            <p className="mt-1 text-xs text-slate-300 leading-relaxed max-w-2xl font-sans">
              {verdictExplanation || defaultExplanation}
            </p>
          </div>

          {/* Action Recommendation */}
          <div className="pt-1 flex flex-wrap items-center justify-center md:justify-start gap-2.5 text-xs">
            <span className="text-slate-400 font-normal">Recommended action:</span>
            <span className={cn('px-2.5 py-0.5 rounded font-mono text-xs border font-medium', getActionBadgeColor(recommendedAction))}>
              {recommendedAction || 'ALLOW'}
            </span>
          </div>
        </div>

        {/* Right Side: Risk Score Meter */}
        <div className="flex flex-col items-center justify-center p-3 rounded-lg bg-[#0d0f12]/80 border border-white/[0.06] shrink-0">
          <RiskGauge score={riskScore} size={100} strokeWidth={8} />
        </div>
      </div>
    </div>
  );
}
