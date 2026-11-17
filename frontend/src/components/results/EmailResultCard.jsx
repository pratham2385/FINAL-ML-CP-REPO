import React from 'react';
import { Mail, ShieldAlert, CheckCircle, FileText, Globe } from 'lucide-react';
import { formatPercent } from '../../utils/formatters';

export function EmailResultCard({ emailAnalysis, urlSummary }) {
  if (!emailAnalysis) return null;

  const isSpam = emailAnalysis.is_spam;
  const spamProb = (emailAnalysis.spam_probability || 0) * 100;

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-2">
          <Mail className="w-4 h-4 text-slate-300" />
          <h3 className="text-sm font-semibold text-white">Email NLP Classification</h3>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-mono font-medium border ${
            isSpam
              ? 'bg-[#d29922]/15 text-[#e3b341] border-[#d29922]/40'
              : 'bg-[#2da44e]/15 text-[#56d364] border-[#2da44e]/40'
          }`}
        >
          {isSpam ? <ShieldAlert className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
          <span>{emailAnalysis.label || (isSpam ? 'Spam' : 'Ham')}</span>
        </span>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
          <span className="text-xs text-slate-400 block">Spam probability</span>
          <span className="text-xl font-semibold font-mono tabular-nums text-white mt-1 block">
            {formatPercent(spamProb)}
          </span>
          <div className="w-full bg-[#1c2027] h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${isSpam ? 'bg-[#d29922]' : 'bg-[#2da44e]'}`}
              style={{ width: `${Math.min(spamProb, 100)}%` }}
            />
          </div>
        </div>

        <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
          <span className="text-xs text-slate-400 block">Confidence score</span>
          <span className="text-xl font-semibold font-mono tabular-nums text-slate-100 mt-1 block">
            {formatPercent(emailAnalysis.confidence_percent || 0)}
          </span>
          <span className="text-[11px] text-slate-500 mt-1 block">TF-IDF Vectorized Model</span>
        </div>

        <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
          <span className="text-xs text-slate-400 block">Hyperlinks detected</span>
          <span className="text-xl font-semibold font-mono tabular-nums text-white mt-1 block flex items-center gap-1.5">
            <Globe className="w-4 h-4 text-slate-400" />
            {urlSummary?.total_urls_found || 0}
          </span>
          <span className={`text-[11px] mt-1 block ${urlSummary?.phishing_urls_count > 0 ? 'text-[#ff8182] font-medium' : 'text-slate-500'}`}>
            {urlSummary?.phishing_urls_count || 0} flagged malicious
          </span>
        </div>
      </div>

      {/* Cleaned text preview */}
      {emailAnalysis.cleaned_text_preview && (
        <div className="pt-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium mb-1.5">
            <FileText className="w-3.5 h-3.5 text-slate-400" />
            <span>Preprocessed Tokenized Stream (Model Input)</span>
          </div>
          <p className="text-xs font-mono text-slate-300 bg-[#101216] p-3 rounded-lg border border-white/[0.06] line-clamp-3 leading-relaxed">
            {emailAnalysis.cleaned_text_preview}
          </p>
        </div>
      )}
    </div>
  );
}
