import React, { useEffect, useState } from 'react';
import {
  History,
  Search,
  Trash2,
  Eye,
  ChevronLeft,
  ChevronRight,
  Database,
  RefreshCw
} from 'lucide-react';
import { getHistory, deleteHistoryById } from '../api/historyService';
import { ThreatBadge } from '../components/common/ThreatBadge';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { HistoryDetailModal } from './HistoryDetailModal';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { useToast } from '../components/common/Toast';
import { formatDate } from '../utils/formatters';

const TYPE_FILTERS = [
  { label: 'All modalities', value: '' },
  { label: 'Emails', value: 'email' },
  { label: 'URLs', value: 'url' },
  { label: 'EML files', value: 'file' },
];

export function AnalysisHistory() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(15);
  const [offset, setOffset] = useState(0);
  const [selectedType, setSelectedType] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  // Modals state
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [recordToDelete, setRecordToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const toast = useToast();

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params = {
        limit,
        offset,
      };
      if (selectedType) {
        params.analysis_type = selectedType;
      }
      const data = await getHistory(params);
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      toast.error(err.message || 'Failed to fetch history logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [limit, offset, selectedType]);

  const handleTypeChange = (typeVal) => {
    setSelectedType(typeVal);
    setOffset(0);
  };

  const handleDeleteConfirm = async () => {
    if (!recordToDelete) return;
    setDeleting(true);
    try {
      await deleteHistoryById(recordToDelete.id);
      toast.success(`Record #${recordToDelete.id} deleted successfully`);
      setRecordToDelete(null);
      fetchHistory();
    } catch (err) {
      toast.error(err.message || 'Failed to delete record');
    } finally {
      setDeleting(false);
    }
  };

  // Client-side search filter
  const filteredItems = items.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const target = (item.subject || item.submitted_url || '').toLowerCase();
    const verdict = (item.overall_verdict || '').toLowerCase();
    return target.includes(q) || verdict.includes(q) || String(item.id).includes(q);
  });

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-3">
        <div>
          <h2 className="text-xl font-semibold text-white tracking-tight flex items-center gap-2">
            <History className="w-5 h-5 text-slate-300" />
            <span>Audit History</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Complete audit trail persisted in PostgreSQL database with deep JSONB inspection results.
          </p>
        </div>

        <button
          onClick={fetchHistory}
          disabled={loading}
          className="self-start sm:self-auto px-3 py-1.5 rounded-md text-xs font-mono border border-white/[0.08] bg-[#14171b] hover:bg-[#1c2027] text-slate-300 hover:text-white flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-slate-400' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Type Filter Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {TYPE_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => handleTypeChange(f.value)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                selectedType === f.value
                  ? 'bg-[#1f6feb] text-white border border-[#388bfd] font-medium'
                  : 'bg-[#14171b] text-slate-400 border border-white/[0.08] hover:text-slate-200 hover:bg-[#1c2027]'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Search Bar */}
        <div className="relative min-w-[260px]">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search subject, URL, or verdict..."
            className="w-full pl-8 pr-3 py-1.5 rounded-md border border-white/[0.08] bg-[#101216] text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-[#1f6feb] transition-colors"
          />
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2" />
        </div>
      </div>

      {/* Data Table */}
      <div className="rounded-xl border border-white/[0.08] bg-[#14171b] overflow-hidden">
        {loading ? (
          <div className="p-6">
            <LoadingSkeleton rows={8} />
          </div>
        ) : filteredItems.length === 0 ? (
          <EmptyState
            icon={Database}
            title={searchQuery ? 'No matching records' : 'No analysis history'}
            description={
              searchQuery
                ? `No records found matching "${searchQuery}".`
                : 'No analyses have been logged in the audit database yet.'
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#101216] text-slate-400 border-b border-white/[0.06] text-[11px] font-medium">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Audit ID</th>
                  <th className="py-2.5 px-4 font-medium">Type</th>
                  <th className="py-2.5 px-4 font-medium">Target subject / URL</th>
                  <th className="py-2.5 px-4 font-medium">Verdict</th>
                  <th className="py-2.5 px-4 font-medium">Threat level</th>
                  <th className="py-2.5 px-4 font-medium">Risk score</th>
                  <th className="py-2.5 px-4 font-medium">Timestamp</th>
                  <th className="py-2.5 px-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredItems.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-[#181c23]/60 transition-colors group cursor-pointer"
                    onClick={() => setSelectedRecordId(item.id)}
                  >
                    <td className="py-2.5 px-4 text-slate-300 font-semibold">#{item.id}</td>
                    <td className="py-2.5 px-4 text-slate-300">
                      <span className="px-1.5 py-0.5 rounded bg-[#181c23] text-[11px] border border-white/[0.06]">
                        {item.analysis_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-200 max-w-xs truncate font-sans">
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
                    <td className="py-2.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => setSelectedRecordId(item.id)}
                          className="p-1 rounded text-slate-400 hover:text-white hover:bg-[#1c2027] transition-colors"
                          title="Inspect deep details"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setRecordToDelete(item)}
                          className="p-1 rounded text-slate-400 hover:text-[#ff8182] hover:bg-[#1a1416] transition-colors"
                          title="Delete record"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {!loading && total > 0 && (
          <div className="p-3.5 border-t border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-slate-400">
            <div>
              Showing {Math.min(offset + 1, total)} - {Math.min(offset + limit, total)} of {total} records
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - limit))}
                className="px-2.5 py-1 rounded border border-white/[0.08] bg-[#181c23] hover:bg-[#1f242d] text-slate-300 disabled:opacity-30 disabled:pointer-events-none transition-colors flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>

              <span className="px-2">
                Page {currentPage} of {totalPages}
              </span>

              <button
                type="button"
                disabled={offset + limit >= total}
                onClick={() => setOffset(offset + limit)}
                className="px-2.5 py-1 rounded border border-white/[0.08] bg-[#181c23] hover:bg-[#1f242d] text-slate-300 disabled:opacity-30 disabled:pointer-events-none transition-colors flex items-center gap-1"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Inspection Modal */}
      {selectedRecordId && (
        <HistoryDetailModal
          recordId={selectedRecordId}
          onClose={() => setSelectedRecordId(null)}
        />
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(recordToDelete)}
        title="Delete Analysis Record"
        message={`Are you sure you want to delete audit record #${recordToDelete?.id}? This will permanently remove it from the PostgreSQL database.`}
        confirmText="Confirm Delete"
        isLoading={deleting}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setRecordToDelete(null)}
      />
    </div>
  );
}
