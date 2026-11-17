import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  ShieldCheck,
  Mail,
  Globe,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Activity,
  Layers,
  Database
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import { getHistoryStats, getHistory } from '../api/historyService';
import { ThreatBadge } from '../components/common/ThreatBadge';
import { CardSkeleton, LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { formatDate } from '../utils/formatters';

const THREAT_COLORS = {
  CRITICAL: '#cf222e',
  HIGH: '#da3633',
  MEDIUM: '#d29922',
  LOW_SUSPICIOUS: '#bb8009',
  SAFE: '#2da44e',
};

export function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentHistory, setRecentHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, historyData] = await Promise.all([
        getHistoryStats(),
        getHistory({ limit: 5, offset: 0 }),
      ]);
      setStats(statsData);
      setRecentHistory(historyData.items || []);
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const threatChartData = stats?.threat_distribution
    ? Object.entries(stats.threat_distribution).map(([level, count]) => ({
        name: level.replace('_', ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()),
        value: count,
        color: THREAT_COLORS[level] || '#1f6feb',
      }))
    : [];

  const typeChartData = stats?.type_distribution
    ? [
        { name: 'Email Scans', count: stats.type_distribution.email || 0, fill: '#1f6feb' },
        { name: 'URL Scans', count: stats.type_distribution.url || 0, fill: '#388bfd' },
        { name: 'Batch Files', count: stats.type_distribution.file || 0, fill: '#79c0ff' },
      ]
    : [];

  const isEmpty = (stats?.total_analyses || 0) === 0;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-white/[0.08]">
        <div>
          <h2 className="text-xl font-semibold text-white tracking-tight">
            Threat Intelligence Overview
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time security telemetry from dual-representation ML models and audit logs.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            to="/email"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-[#1f6feb] hover:bg-[#388bfd] text-white transition-colors"
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Scan email</span>
          </Link>
          <Link
            to="/url"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-white/[0.08] bg-[#181c23] hover:bg-[#1f242d] text-slate-200 transition-colors"
          >
            <Globe className="w-3.5 h-3.5 text-slate-400" />
            <span>Scan URL</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Card 1: Total */}
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-4 transition-colors hover:border-white/[0.14]">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium text-slate-400">Total scans</span>
              <Activity className="w-4 h-4 text-slate-400" />
            </div>
            <div className="mt-2 text-2xl font-semibold font-mono tabular-nums text-white">
              {stats?.total_analyses || 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Audit events recorded</span>
          </div>

          {/* Card 2: Phishing */}
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-4 transition-colors hover:border-white/[0.14]">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium text-slate-400">Phishing threats</span>
              <ShieldAlert className="w-4 h-4 text-[#cf222e]" />
            </div>
            <div className="mt-2 text-2xl font-semibold font-mono tabular-nums text-[#ff8182]">
              {stats?.phishing_count || 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Critical lures blocked</span>
          </div>

          {/* Card 3: Spam */}
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-4 transition-colors hover:border-white/[0.14]">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium text-slate-400">Spam detected</span>
              <AlertTriangle className="w-4 h-4 text-[#d29922]" />
            </div>
            <div className="mt-2 text-2xl font-semibold font-mono tabular-nums text-[#e3b341]">
              {stats?.spam_count || 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Junk communications</span>
          </div>

          {/* Card 4: Safe */}
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-4 transition-colors hover:border-white/[0.14]">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium text-slate-400">Verified clean</span>
              <ShieldCheck className="w-4 h-4 text-[#2da44e]" />
            </div>
            <div className="mt-2 text-2xl font-semibold font-mono tabular-nums text-[#56d364]">
              {stats?.safe_count || 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Legitimate communications</span>
          </div>

          {/* Card 5: Threat Ratio */}
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-4 transition-colors hover:border-white/[0.14]">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium text-slate-400">Threat rate</span>
              <TrendingUp className="w-4 h-4 text-slate-400" />
            </div>
            <div className="mt-2 text-2xl font-semibold font-mono tabular-nums text-white">
              {(stats?.threat_percentage || 0).toFixed(1)}%
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Malicious / total ratio</span>
          </div>
        </div>
      )}

      {/* Visual Analytics Charts */}
      {isEmpty && !loading ? (
        <EmptyState
          icon={Database}
          title="Audit database is empty"
          description="Perform your first email or URL threat analysis to populate metrics and charts."
          action={
            <Link
              to="/email"
              className="px-3 py-1.5 rounded-md text-xs font-medium bg-[#1f6feb] hover:bg-[#388bfd] text-white transition-colors"
            >
              Start first scan
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Chart 1: Threat Distribution */}
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-white flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-slate-400" />
                <span>Threat severity breakdown</span>
              </h3>
              <span className="text-[11px] font-mono text-slate-500">PostgreSQL JSONB</span>
            </div>

            <div className="h-60 w-full">
              {loading ? (
                <LoadingSkeleton rows={5} />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={threatChartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={3}
                    >
                      {threatChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} stroke="#101216" strokeWidth={2} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#181c23',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderRadius: '6px',
                        color: '#f0f2f5',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                      }}
                    />
                    <Legend
                      formatter={(val) => <span className="text-xs font-mono text-slate-300">{val}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Chart 2: Analysis Type Distribution */}
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-slate-400" />
                <span>Modality workload distribution</span>
              </h3>
              <span className="text-[11px] font-mono text-slate-500">Email vs URL vs Batch</span>
            </div>

            <div className="h-60 w-full">
              {loading ? (
                <LoadingSkeleton rows={5} />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={typeChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis
                      dataKey="name"
                      stroke="#6e7681"
                      fontSize={11}
                      fontFamily="monospace"
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#6e7681"
                      fontSize={11}
                      fontFamily="monospace"
                      allowDecimals={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#181c23',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderRadius: '6px',
                        color: '#f0f2f5',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={36} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity Table */}
      {!isEmpty && (
        <div className="rounded-xl border border-white/[0.08] bg-[#14171b] overflow-hidden">
          <div className="p-4 border-b border-white/[0.08] flex items-center justify-between">
            <h3 className="text-xs font-semibold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-slate-400" />
              <span>Recent threat evaluations</span>
            </h3>
            <Link
              to="/history"
              className="inline-flex items-center gap-1 text-xs text-slate-300 hover:text-white font-medium transition-colors"
            >
              <span>View full audit log</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#101216] text-slate-400 border-b border-white/[0.06] text-[11px] font-medium">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Audit ID</th>
                  <th className="py-2.5 px-4 font-medium">Modality</th>
                  <th className="py-2.5 px-4 font-medium">Subject / target URL</th>
                  <th className="py-2.5 px-4 font-medium">Verdict</th>
                  <th className="py-2.5 px-4 font-medium">Threat level</th>
                  <th className="py-2.5 px-4 font-medium">Risk score</th>
                  <th className="py-2.5 px-4 font-medium">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {recentHistory.map((item) => (
                  <tr key={item.id} className="hover:bg-[#181c23]/60 transition-colors">
                    <td className="py-2.5 px-4 text-slate-300 font-semibold">#{item.id}</td>
                    <td className="py-2.5 px-4 text-slate-300">
                      <span className="px-1.5 py-0.5 rounded bg-[#181c23] text-[11px] border border-white/[0.06]">
                        {item.analysis_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-200 max-w-xs truncate">
                      {item.subject || item.submitted_url || '—'}
                    </td>
                    <td className="py-2.5 px-4 font-sans font-medium text-white capitalize">
                      {item.overall_verdict}
                    </td>
                    <td className="py-2.5 px-4">
                      <ThreatBadge threatLevel={item.threat_level} size="sm" />
                    </td>
                    <td className="py-2.5 px-4 tabular-nums font-semibold">
                      <span className={item.risk_score >= 50 ? 'text-[#ff8182]' : 'text-[#56d364]'}>
                        {item.risk_score.toFixed(1)}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 tabular-nums text-[11px]">
                      {formatDate(item.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
