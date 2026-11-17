import React, { useState } from 'react';
import { Globe, Search, AlertCircle, RefreshCw } from 'lucide-react';
import { analyzeUrl } from '../api/analyzeService';
import { VerdictBanner } from '../components/common/VerdictBanner';
import { URLResultCard } from '../components/results/URLResultCard';
import { useToast } from '../components/common/Toast';

const URL_PRESETS = [
  { name: 'Legitimate Domain', url: 'https://www.wikipedia.org' },
  { name: 'Legitimate Deep Path', url: 'https://github.com/torvalds/linux' },
  { name: 'Credential Harvester', url: 'http://secure-update-paypal-login.com/verify-account' },
  { name: 'Raw IP Target', url: 'http://192.168.1.1/bank-security/login.php' },
];

export function URLAnalysis() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const toast = useToast();

  const handleApplyPreset = (targetUrl) => {
    setUrl(targetUrl);
    setErrorMsg('');
  };

  const handleReset = () => {
    setUrl('');
    setResult(null);
    setErrorMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const cleanUrl = url.trim();
    if (!cleanUrl) {
      setErrorMsg('Please enter a valid URL to analyze.');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    try {
      const data = await analyzeUrl(cleanUrl);
      setResult(data);
      toast.success(`URL Evaluated: ${data.classification}`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to analyze URL.');
      toast.error(err.message || 'Failed to analyze URL.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="border-b border-white/[0.08] pb-3">
        <h2 className="text-xl font-semibold text-white tracking-tight flex items-center gap-2">
          <Globe className="w-5 h-5 text-slate-300" />
          <span>Standalone URL Phishing Classification</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Extracts 18 lexical properties from the URL string and applies dual-level Random Forest evaluation (canonical domain + deep path) to detect phishing lures.
        </p>
      </div>

      {/* Preset Badges */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-400 font-normal mr-1">
          Test samples:
        </span>
        {URL_PRESETS.map((p, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleApplyPreset(p.url)}
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

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Target URL to inspect
          </label>
          <div className="relative">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="e.g. http://login-update-paypal-verify.com/login.php"
              className="w-full px-3 py-2.5 rounded-md border border-white/[0.08] bg-[#101216] text-white placeholder-slate-500 text-xs focus:outline-none focus:border-[#1f6feb] transition-colors font-mono"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-1">
          {(url || result) && (
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
                <Search className="w-3.5 h-3.5" />
                <span>Inspect URL</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Analysis Output Result */}
      {result && (
        <div className="space-y-4">
          <VerdictBanner
            verdict={result.classification}
            threatLevel={result.threat_level}
            riskScore={result.risk_score}
            recommendedAction={result.recommended_action}
            verdictExplanation={result.explanation}
            recordId={result.id}
          />

          <URLResultCard urlData={result} />
        </div>
      )}
    </div>
  );
}
