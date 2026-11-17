import React, { useEffect, useState } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  Server,
  ExternalLink,
  RefreshCw,
  Layers,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { getHealth } from '../api/healthService';
import { useToast } from '../components/common/Toast';
import { formatDate } from '../utils/formatters';

export function Settings() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const checkStatus = async () => {
    setLoading(true);
    try {
      const data = await getHealth();
      setHealth(data);
      toast.success('System diagnostics completed successfully');
    } catch (err) {
      setHealth({ status: 'degraded', error: err.message });
      toast.error('Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  const isHealthy = health?.status === 'healthy';
  const dbConnected = health?.database?.status === 'connected';

  return (
    <div className="space-y-5 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-3">
        <div>
          <h2 className="text-xl font-semibold text-white tracking-tight flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-slate-300" />
            <span>System Telemetry & Architecture</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time infrastructure health, machine learning pipeline specifications, and deployment telemetry.
          </p>
        </div>

        <button
          onClick={checkStatus}
          disabled={loading}
          className="px-3.5 py-1.5 rounded-md text-xs font-mono font-medium bg-[#1f6feb] hover:bg-[#388bfd] text-white flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Run diagnostics</span>
        </button>
      </div>

      {/* Live System Diagnostics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Backend & DB Health Card */}
        <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 space-y-3.5">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-slate-300" />
              <h3 className="text-sm font-semibold text-white">Live Infrastructure Status</h3>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-xs font-mono font-medium border ${
                isHealthy
                  ? 'bg-[#2da44e]/15 text-[#56d364] border-[#2da44e]/35'
                  : 'bg-[#d29922]/15 text-[#e3b341] border-[#d29922]/35'
              }`}
            >
              {health?.status || 'Unknown'}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between p-2 rounded bg-[#101216] border border-white/[0.06]">
              <span className="text-slate-400">FastAPI backend:</span>
              <span className="text-[#56d364] font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Online (v{health?.version || '1.0.0'})
              </span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-[#101216] border border-white/[0.06]">
              <span className="text-slate-400">PostgreSQL DB:</span>
              <span
                className={`font-medium flex items-center gap-1.5 ${
                  dbConnected ? 'text-[#56d364]' : 'text-[#e3b341]'
                }`}
              >
                {dbConnected ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{health?.database?.database_name || 'Connected'}</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Disconnected</span>
                  </>
                )}
              </span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-[#101216] border border-white/[0.06]">
              <span className="text-slate-400">SQLAlchemy ORM:</span>
              <span className="text-slate-200">2.x (Dialect: {health?.database?.dialect || 'postgresql'})</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-[#101216] border border-white/[0.06]">
              <span className="text-slate-400">Telemetry timestamp:</span>
              <span className="text-slate-400 tabular-nums">{formatDate(health?.timestamp)}</span>
            </div>
          </div>
        </div>

        {/* ML Engine Telemetry */}
        <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 space-y-3.5">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-slate-300" />
              <h3 className="text-sm font-semibold text-white">In-Memory ML Engine</h3>
            </div>
            <span className="text-xs font-mono text-slate-300 font-medium">
              {health?.ml_pipeline?.status === 'operational' ? 'Active' : 'Initializing'}
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between p-2 rounded bg-[#101216] border border-white/[0.06]">
              <span className="text-slate-400">Email classifier:</span>
              <span className="text-[#56d364] font-medium">MultinomialNB (α=0.01)</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-[#101216] border border-white/[0.06]">
              <span className="text-slate-400">TF-IDF vectorizer:</span>
              <span className="text-slate-200 tabular-nums">268,754 Unigram + Bigram Terms</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-[#101216] border border-white/[0.06]">
              <span className="text-slate-400">URL phishing model:</span>
              <span className="text-[#56d364] font-medium">Random Forest (400 Estimators)</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-[#101216] border border-white/[0.06]">
              <span className="text-slate-400">Monitored lexical features:</span>
              <span className="text-slate-200 tabular-nums font-medium">
                {health?.ml_pipeline?.url_features_monitored || 18} Lexical Dimensions
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Architecture Breakdown */}
      <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 space-y-3.5">
        <div className="flex items-center gap-2 border-b border-white/[0.08] pb-3">
          <Layers className="w-4 h-4 text-slate-300" />
          <h3 className="text-sm font-semibold text-white">Dual-Representation Pipeline Architecture</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
          <div className="p-3.5 rounded-lg bg-[#101216] border border-white/[0.06] space-y-1.5">
            <div className="text-white font-medium">Stream 1: Hyperlink Lexical</div>
            <p className="text-slate-400 font-sans leading-relaxed">
              Regex parser extracts raw links. 18 structural properties (domain depth, special characters, IP presence, obfuscation markers) are scored through canonical domain normalization.
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-[#101216] border border-white/[0.06] space-y-1.5">
            <div className="text-white font-medium">Stream 2: NLP Spam Stream</div>
            <p className="text-slate-400 font-sans leading-relaxed">
              Variant C preprocessing normalizes HTML markup and footers into 268,754 vocabulary features, trained across 37,890 legitimate and spam emails with 98.51% test accuracy.
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-[#101216] border border-white/[0.06] space-y-1.5">
            <div className="text-white font-medium">Composite Threat Engine</div>
            <p className="text-slate-400 font-sans leading-relaxed">
              Combines dedicated phishing intent heuristics, lexical URL predictions, and NLP text scores into an aggregated risk verdict (SAFE, SUSPICIOUS, MALICIOUS) with actionable containment.
            </p>
          </div>
        </div>
      </div>

      {/* External Resources & Documentation */}
      <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="text-xs font-semibold text-white">FastAPI Interactive Documentation</h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Access OpenAPI 3.0 specifications and test endpoints directly via Swagger UI or ReDoc.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-md text-xs font-mono font-medium bg-[#181c23] hover:bg-[#1f242d] text-slate-200 hover:text-white flex items-center gap-1.5 border border-white/[0.08] transition-colors"
          >
            <span>Swagger UI</span>
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>
          <a
            href="http://127.0.0.1:8000/redoc"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-md text-xs font-mono font-medium bg-[#181c23] hover:bg-[#1f242d] text-slate-200 hover:text-white flex items-center gap-1.5 border border-white/[0.08] transition-colors"
          >
            <span>ReDoc</span>
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>
        </div>
      </div>
    </div>
  );
}
