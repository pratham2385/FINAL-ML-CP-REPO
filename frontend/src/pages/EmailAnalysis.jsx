import React, { useState } from 'react';
import { Mail, Send, AlertCircle, RefreshCw, UserCheck } from 'lucide-react';
import { analyzeEmail } from '../api/analyzeService';
import { VerdictBanner } from '../components/common/VerdictBanner';
import { EmailResultCard } from '../components/results/EmailResultCard';
import { URLDetailTable } from '../components/results/URLDetailTable';
import { PhishingIntentCard } from '../components/results/PhishingIntentCard';
import { useToast } from '../components/common/Toast';

const PRESETS = [
  {
    name: 'Clean Team Update',
    badge: 'Ham Sample',
    sender: 'alex.chen@innovatecorp.com',
    subject: 'Quarterly Project Review & Roadmap Sync',
    message: 'Hi team, please find attached the quarterly expenditure and roadmap report for review before our Monday sync. Thanks!',
  },
  {
    name: 'BEC Wire Fraud',
    badge: 'BEC Attack',
    sender: 'CEO Johnathan Smith <ceo.executive.urgent@gmail.com>',
    subject: 'Urgent Wire Transfer Request - Confidential Acquisition',
    message: 'Are you at your desk right now? I need you to immediately execute an urgent wire transfer for an acquisition closing today. Treat this with strict confidentiality.',
  },
  {
    name: 'Credential Phishing',
    badge: 'Phishing Threat',
    sender: 'security@paypal-verification-alert.com',
    subject: 'URGENT: Unauthorized Security Access Detected On Your Account',
    message: 'Your account has been temporarily locked due to suspicious logins. Please verify your credentials immediately at http://secure-update-paypal-login.com/verify-account to prevent permanent termination.',
  },
  {
    name: 'Lottery Spam',
    badge: 'Spam Sample',
    sender: 'promo@intl-rewards-club.com',
    subject: 'CONGRATULATIONS! You have won $1,000,000 in the Mega Lottery!',
    message: 'Dear lucky winner, claim your cash reward immediately! Send your full bank account numbers and ID now to release the wire transfer immediately!',
  },
];

export function EmailAnalysis() {
  const [sender, setSender] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const toast = useToast();

  const handleApplyPreset = (preset) => {
    setSender(preset.sender || '');
    setSubject(preset.subject);
    setMessage(preset.message);
    setErrorMsg('');
  };

  const handleReset = () => {
    setSender('');
    setSubject('');
    setMessage('');
    setResult(null);
    setErrorMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!subject.trim() && !message.trim()) {
      setErrorMsg('Please enter either a subject line or email body content to analyze.');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    try {
      const data = await analyzeEmail({
        subject,
        message,
        sender: sender.trim() || undefined,
      });
      setResult(data);
      toast.success(`Analysis complete: ${data.verdict}`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to analyze email.');
      toast.error(err.message || 'Failed to analyze email.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="border-b border-white/[0.08] pb-3">
        <h2 className="text-xl font-semibold text-white tracking-tight flex items-center gap-2">
          <Mail className="w-5 h-5 text-slate-300" />
          <span>Email Threat Analysis</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Evaluates message body with TF-IDF Naive Bayes, extracts hyperlinks for lexical classification, and checks for deceptive intent.
        </p>
      </div>

      {/* Preset Badges */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-400 font-normal mr-1">
          Test samples:
        </span>
        {PRESETS.map((p, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleApplyPreset(p)}
            className="px-2.5 py-1 rounded-md text-xs font-mono bg-[#14171b] border border-white/[0.08] hover:border-white/[0.14] hover:bg-[#1c2027] text-slate-300 hover:text-white transition-colors"
          >
            {p.name}
          </button>
        ))}
      </div>

      {/* Main Analysis Form */}
      <form onSubmit={handleSubmit} className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 space-y-4">
        {errorMsg && (
          <div className="p-3 rounded-md bg-[#1a1416] border border-[#cf222e]/40 text-[#ff8182] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5 text-slate-400" />
              <span>Sender header (optional)</span>
            </label>
            <input
              type="text"
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              placeholder="e.g. CEO John <ceo@corp.com>"
              className="w-full px-3 py-2 rounded-md border border-white/[0.08] bg-[#101216] text-white placeholder-slate-500 text-xs focus:outline-none focus:border-[#1f6feb] transition-colors"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Subject line
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Account Security Notification / Wire Transfer Memo"
              className="w-full px-3 py-2 rounded-md border border-white/[0.08] bg-[#101216] text-white placeholder-slate-500 text-xs focus:outline-none focus:border-[#1f6feb] transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Email message content
          </label>
          <textarea
            rows={5}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Paste raw email body text or HTML payload here. Embedded URLs will be extracted and classified..."
            className="w-full px-3 py-2.5 rounded-md border border-white/[0.08] bg-[#101216] text-white placeholder-slate-500 text-xs focus:outline-none focus:border-[#1f6feb] transition-colors font-mono"
          />
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-1">
          {(subject || message || result) && (
            <button
              type="button"
              onClick={handleReset}
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-white/[0.08] bg-[#181c23] text-slate-300 hover:text-white hover:bg-[#1f242d] transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}

          <button
            type="submit"
            disabled={loading}
            className="px-4 py-1.5 rounded-md text-xs font-medium bg-[#1f6feb] hover:bg-[#388bfd] text-white disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Running evaluation...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Analyze email</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Analysis Output Result */}
      {result && (
        <div className="space-y-4">
          <VerdictBanner
            verdict={result.verdict}
            threatLevel={result.threat_level}
            riskScore={result.risk_score}
            recommendedAction={result.recommended_action}
            verdictExplanation={result.verdict_explanation}
            recordId={result.id}
          />

          {result.phishing_intent_analysis && (
            <PhishingIntentCard phishingIntent={result.phishing_intent_analysis} />
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <EmailResultCard
              emailAnalysis={result.email_analysis}
              urlSummary={result.url_summary}
            />

            <URLDetailTable urls={result.url_details || []} />
          </div>
        </div>
      )}
    </div>
  );
}
