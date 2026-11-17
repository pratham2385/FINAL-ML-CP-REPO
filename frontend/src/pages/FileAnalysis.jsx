import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Send,
  Trash2,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
  FileCheck2,
  FileX
} from 'lucide-react';
import { analyzeFiles } from '../api/analyzeService';
import { VerdictBanner } from '../components/common/VerdictBanner';
import { ThreatBadge } from '../components/common/ThreatBadge';
import { EmailResultCard } from '../components/results/EmailResultCard';
import { URLDetailTable } from '../components/results/URLDetailTable';
import { PhishingIntentCard } from '../components/results/PhishingIntentCard';
import { useToast } from '../components/common/Toast';

const MAX_FILES_PER_BATCH = 100;
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const MAX_BATCH_SIZE_BYTES = 100 * 1024 * 1024; // 100MB

export function FileAnalysis() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [batchResult, setBatchResult] = useState(null);
  const [expandedIndices, setExpandedIndices] = useState({});
  const [filterType, setFilterType] = useState('ALL'); // 'ALL', 'SPAM', 'HAM', 'FAILED'
  const [errorMsg, setErrorMsg] = useState('');
  
  const fileInputRef = useRef(null);
  const toast = useToast();

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  const handleFilesAdded = (incomingFiles) => {
    if (!incomingFiles || incomingFiles.length === 0) return;

    setErrorMsg('');
    const newItems = [];
    let rejectedCount = 0;

    for (let i = 0; i < incomingFiles.length; i++) {
      const f = incomingFiles[i];
      const isEml = f.name.toLowerCase().endsWith('.eml');
      const isTooLarge = f.size > MAX_FILE_SIZE_BYTES;

      let error = null;
      if (!isEml) {
        error = 'Invalid extension (only .eml accepted)';
        rejectedCount++;
      } else if (isTooLarge) {
        error = `Exceeds 10MB limit (${formatFileSize(f.size)})`;
        rejectedCount++;
      }

      newItems.push({
        id: `${f.name}-${f.size}-${f.lastModified}-${Math.random().toString(36).substring(2, 7)}`,
        file: f,
        name: f.name,
        size: f.size,
        error: error,
      });
    }

    const updated = [...selectedFiles, ...newItems];

    if (updated.length > MAX_FILES_PER_BATCH) {
      setErrorMsg(`Batch exceeds maximum allowed limit of ${MAX_FILES_PER_BATCH} files.`);
      toast.error(`Maximum batch limit is ${MAX_FILES_PER_BATCH} files.`);
      return;
    }

    const totalBatchBytes = updated.reduce((sum, item) => sum + item.size, 0);
    if (totalBatchBytes > MAX_BATCH_SIZE_BYTES) {
      setErrorMsg(`Combined batch size exceeds 100MB limit (${formatFileSize(totalBatchBytes)}).`);
      toast.error(`Combined batch size exceeds 100MB limit.`);
      return;
    }

    setSelectedFiles(updated);

    if (rejectedCount > 0) {
      toast.info(`${rejectedCount} file(s) flagged with validation issues.`);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesAdded(Array.from(e.dataTransfer.files));
    }
  };

  const handleRemoveFile = (indexToRemove) => {
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
    setBatchResult(null);
    setExpandedIndices({});
    setErrorMsg('');
    setUploadProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const toggleExpand = (index) => {
    setExpandedIndices((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const expandAll = () => {
    if (!batchResult || !batchResult.results) return;
    const all = {};
    batchResult.results.forEach((_, idx) => {
      all[idx] = true;
    });
    setExpandedIndices(all);
  };

  const collapseAll = () => {
    setExpandedIndices({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validItems = selectedFiles.filter((item) => !item.error);

    if (validItems.length === 0) {
      setErrorMsg('Please select at least one valid .eml email file to analyze.');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    setUploadProgress(10);

    const actualFiles = validItems.map((item) => item.file);

    try {
      const data = await analyzeFiles(actualFiles, (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 90) / progressEvent.total);
          setUploadProgress(percent);
        }
      });

      setUploadProgress(100);
      setBatchResult(data);
      
      const successCount = data.summary.successful_count;
      const totalCount = data.summary.total_files;
      toast.success(`Evaluated ${successCount}/${totalCount} files successfully.`);

      if (data.results && data.results.length === 1) {
        setExpandedIndices({ 0: true });
      }
    } catch (err) {
      setErrorMsg(err.message || 'Batch email upload analysis failed.');
      toast.error(err.message || 'Batch email analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const totalSelectedBytes = selectedFiles.reduce((sum, item) => sum + item.size, 0);
  const invalidFilesCount = selectedFiles.filter((f) => f.error).length;

  const filteredResults = batchResult?.results
    ? batchResult.results.filter((res) => {
        if (filterType === 'ALL') return true;
        if (filterType === 'SPAM') return res.email_classification === 'Spam';
        if (filterType === 'HAM') return res.email_classification === 'Ham';
        if (filterType === 'FAILED') return res.status === 'failed';
        return true;
      })
    : [];

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="border-b border-white/[0.08] pb-3">
        <h2 className="text-xl font-semibold text-white tracking-tight flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-slate-300" />
          <span>Batch Email File Inspector (.eml)</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Upload single or multiple raw MIME email files. Automatically extracts headers, parses multipart HTML and plain text, and runs dual-stream threat evaluation.
        </p>

        {/* Configured Limits Tags */}
        <div className="flex flex-wrap items-center gap-2.5 mt-2.5 text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1 bg-[#14171b] px-2 py-0.5 rounded border border-white/[0.08]">
            <span className="text-slate-500">Max files:</span>
            <span className="text-white font-medium">{MAX_FILES_PER_BATCH}</span>
          </span>
          <span className="flex items-center gap-1 bg-[#14171b] px-2 py-0.5 rounded border border-white/[0.08]">
            <span className="text-slate-500">Max file size:</span>
            <span className="text-white font-medium">10 MB</span>
          </span>
          <span className="flex items-center gap-1 bg-[#14171b] px-2 py-0.5 rounded border border-white/[0.08]">
            <span className="text-slate-500">Max batch size:</span>
            <span className="text-white font-medium">100 MB</span>
          </span>
          <span className="flex items-center gap-1 bg-[#14171b] px-2 py-0.5 rounded border border-white/[0.08]">
            <span className="text-slate-500">Concurrency:</span>
            <span className="text-[#56d364] font-medium">5 workers</span>
          </span>
        </div>
      </div>

      {/* Global Error Alert */}
      {errorMsg && (
        <div className="p-3 rounded-md bg-[#1a1416] border border-[#cf222e]/40 text-[#ff8182] text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Upload Dropzone Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer rounded-xl border border-dashed p-7 text-center transition-colors ${
            dragOver
              ? 'border-[#1f6feb] bg-[#1f6feb]/5'
              : 'border-white/[0.12] hover:border-white/[0.2] bg-[#14171b]/50 hover:bg-[#14171b]'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".eml"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFilesAdded(Array.from(e.target.files));
              }
            }}
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center space-y-2.5">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-[#181c23] border border-white/[0.08] text-slate-300">
              <UploadCloud className="w-5 h-5 text-slate-300" />
            </div>

            <div>
              <p className="text-xs font-medium text-white">
                Click to browse or drag and drop .eml email files
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Select single or multiple RFC 822 .eml files (up to 100 files, 10MB each)
              </p>
            </div>
          </div>
        </div>

        {/* Selected Files Queue */}
        {selectedFiles.length > 0 && (
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-4 space-y-3">
            {/* Queue Summary Header */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-slate-400" />
                  <span>Selected files ({selectedFiles.length})</span>
                </span>
                <span className="text-xs font-mono tabular-nums text-slate-400 bg-[#101216] px-2 py-0.5 rounded border border-white/[0.06]">
                  Total: {formatFileSize(totalSelectedBytes)}
                </span>
                {invalidFilesCount > 0 && (
                  <span className="text-xs font-mono text-[#e3b341] bg-[#d29922]/15 px-2 py-0.5 rounded border border-[#d29922]/35">
                    {invalidFilesCount} invalid
                  </span>
                )}
              </div>

              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs font-medium text-slate-400 hover:text-[#ff8182] flex items-center gap-1 px-2 py-0.5 rounded bg-[#181c23] hover:bg-[#1a1416] border border-white/[0.08] transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear all</span>
              </button>
            </div>

            {/* Scrollable File List */}
            <div className="max-h-60 overflow-y-auto space-y-1.5 pr-1">
              {selectedFiles.map((item, idx) => (
                <div
                  key={item.id}
                  className={`flex items-center justify-between p-2 rounded-md border text-xs font-mono transition-colors ${
                    item.error
                      ? 'bg-[#1a1416] border-[#cf222e]/40 text-[#ff8182]'
                      : 'bg-[#101216] border-white/[0.06] text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className="text-slate-500 w-5 shrink-0 text-right">{idx + 1}.</span>
                    {item.error ? (
                      <AlertCircle className="w-3.5 h-3.5 text-[#cf222e] shrink-0" />
                    ) : (
                      <FileCheck2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    )}
                    <span className="truncate text-slate-200" title={item.name}>
                      {item.name}
                    </span>
                    <span className="text-[11px] text-slate-500 tabular-nums shrink-0">
                      ({formatFileSize(item.size)})
                    </span>
                    {item.error && (
                      <span className="text-[10px] text-[#ff8182] bg-[#cf222e]/20 px-1.5 py-0.5 rounded border border-[#cf222e]/30 truncate shrink-0">
                        {item.error}
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveFile(idx)}
                    className="p-1 rounded text-slate-500 hover:text-white hover:bg-[#181c23] transition-colors ml-2 shrink-0"
                    title="Remove file"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upload Progress Bar */}
        {loading && (
          <div className="space-y-1.5 p-3 rounded-lg border border-white/[0.08] bg-[#14171b]">
            <div className="flex justify-between text-xs font-mono text-slate-300">
              <span className="flex items-center gap-2">
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Processing batch upload & evaluation...</span>
              </span>
              <span className="tabular-nums">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-[#101216] h-1.5 rounded-full overflow-hidden border border-white/[0.06]">
              <div
                className="bg-[#1f6feb] h-full rounded-full transition-all duration-200"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-1">
          <div className="text-xs font-mono text-slate-400">
            {selectedFiles.length > 0 ? (
              <span className="flex items-center gap-1.5 text-slate-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#2da44e]" />
                <span>
                  {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} queued (
                  {formatFileSize(totalSelectedBytes)})
                </span>
              </span>
            ) : (
              <span>No files currently selected</span>
            )}
          </div>

          <div className="flex items-center gap-2.5">
            {(selectedFiles.length > 0 || batchResult) && (
              <button
                type="button"
                onClick={handleClearAll}
                className="px-3 py-1.5 rounded-md text-xs font-medium border border-white/[0.08] bg-[#181c23] text-slate-300 hover:text-white hover:bg-[#1f242d] transition-colors flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>
            )}

            <button
              type="submit"
              disabled={loading || selectedFiles.length === 0 || selectedFiles.every((f) => f.error)}
              className="px-4 py-1.5 rounded-md text-xs font-medium bg-[#1f6feb] hover:bg-[#388bfd] text-white disabled:opacity-40 transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Evaluating batch...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>
                    Upload & analyze {selectedFiles.length > 0 ? `(${selectedFiles.length})` : ''}
                  </span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Analysis Output Section */}
      {batchResult && (
        <div className="space-y-5">
          {/* If single file analysis, render high-profile VerdictBanner seamlessly */}
          {batchResult.results.length === 1 && batchResult.results[0].status === 'completed' && (
            <>
              <VerdictBanner
                verdict={batchResult.results[0].verdict}
                threatLevel={batchResult.results[0].threat_level}
                riskScore={batchResult.results[0].overall_risk_score}
                recommendedAction={batchResult.results[0].recommended_action}
                verdictExplanation={batchResult.results[0].verdict_explanation}
                recordId={batchResult.results[0].id}
              />

              {batchResult.results[0].phishing_intent_analysis && (
                <PhishingIntentCard phishingIntent={batchResult.results[0].phishing_intent_analysis} />
              )}
            </>
          )}

          {/* Batch Summary Metric Cards */}
          <div className="rounded-xl border border-white/[0.08] bg-[#14171b] p-4 space-y-3.5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-3">
              <div>
                <h3 className="text-sm font-semibold text-white">
                  Batch Inspection Summary
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Processed in {batchResult.summary.total_processing_time_ms} ms · Concurrency 5 · Total payload {formatFileSize(batchResult.summary.total_size_bytes)}
                </p>
              </div>

              {/* Expand / Collapse All Controls */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={expandAll}
                  className="px-2 py-0.5 text-xs font-mono rounded bg-[#101216] border border-white/[0.08] text-slate-300 hover:text-white hover:border-white/[0.14] transition-colors"
                >
                  Expand all
                </button>
                <button
                  type="button"
                  onClick={collapseAll}
                  className="px-2 py-0.5 text-xs font-mono rounded bg-[#101216] border border-white/[0.08] text-slate-300 hover:text-white hover:border-white/[0.14] transition-colors"
                >
                  Collapse all
                </button>
              </div>
            </div>

            {/* Metric KPI Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
              <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
                <span className="text-[11px] font-mono text-slate-400 block">Total files</span>
                <span className="text-xl font-semibold font-mono tabular-nums text-white mt-0.5 block">
                  {batchResult.summary.total_files}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
                <span className="text-[11px] font-mono text-[#56d364] block">Successful</span>
                <span className="text-xl font-semibold font-mono tabular-nums text-[#56d364] mt-0.5 block">
                  {batchResult.summary.successful_count}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
                <span className="text-[11px] font-mono text-[#56d364] block">Ham detected</span>
                <span className="text-xl font-semibold font-mono tabular-nums text-[#56d364] mt-0.5 block">
                  {batchResult.summary.ham_count}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08]">
                <span className="text-[11px] font-mono text-[#ff8182] block">Spam detected</span>
                <span className="text-xl font-semibold font-mono tabular-nums text-[#ff8182] mt-0.5 block">
                  {batchResult.summary.spam_count}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-[#181c23] border border-white/[0.08] col-span-2 sm:col-span-1">
                <span className="text-[11px] font-mono text-[#e3b341] block">Failed / errors</span>
                <span className={`text-xl font-semibold font-mono tabular-nums mt-0.5 block ${batchResult.summary.failed_count > 0 ? 'text-[#e3b341]' : 'text-slate-400'}`}>
                  {batchResult.summary.failed_count}
                </span>
              </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2 pt-1 border-t border-white/[0.06]">
              <span className="text-xs font-mono text-slate-500 mr-1">Filter view:</span>
              {[
                { id: 'ALL', label: `All (${batchResult.results.length})` },
                { id: 'SPAM', label: `Spam (${batchResult.summary.spam_count})` },
                { id: 'HAM', label: `Ham (${batchResult.summary.ham_count})` },
                { id: 'FAILED', label: `Failed (${batchResult.summary.failed_count})` },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setFilterType(tab.id)}
                  className={`px-2.5 py-0.5 rounded text-xs font-mono transition-colors ${
                    filterType === tab.id
                      ? 'bg-[#1f6feb] text-white border border-[#388bfd] font-medium'
                      : 'bg-[#101216] text-slate-400 hover:text-slate-200 border border-white/[0.08]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Individual File Results List */}
          <div className="space-y-3.5">
            <h4 className="text-xs font-semibold text-white flex items-center justify-between">
              <span>Detailed inspection results ({filteredResults.length})</span>
              <span className="text-xs font-normal text-slate-400 font-mono">
                Click any file card to view complete header and threat telemetry
              </span>
            </h4>

            {filteredResults.length === 0 ? (
              <div className="p-6 text-center rounded-xl border border-white/[0.08] bg-[#14171b] text-slate-400 text-xs font-mono">
                No files match the selected filter.
              </div>
            ) : (
              filteredResults.map((item, idx) => {
                const isExpanded = !!expandedIndices[idx];
                const isSpam = item.email_classification === 'Spam';
                const isFailed = item.status === 'failed';

                return (
                  <div
                    key={`${item.filename}-${idx}`}
                    className={`rounded-xl border transition-colors overflow-hidden ${
                      isFailed
                        ? 'border-[#cf222e]/40 bg-[#1a1416]/50'
                        : isSpam
                        ? 'border-[#cf222e]/30 bg-[#14171b] hover:border-[#cf222e]/50'
                        : 'border-white/[0.08] bg-[#14171b] hover:border-white/[0.14]'
                    }`}
                  >
                    {/* Header Row Bar */}
                    <div
                      onClick={() => toggleExpand(idx)}
                      className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer select-none"
                    >
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div
                          className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 border ${
                            isFailed
                              ? 'bg-[#cf222e]/20 border-[#cf222e]/40 text-[#ff8182]'
                              : isSpam
                              ? 'bg-[#cf222e]/15 border-[#cf222e]/35 text-[#ff8182]'
                              : 'bg-[#2da44e]/15 border-[#2da44e]/35 text-[#56d364]'
                          }`}
                        >
                          {isFailed ? (
                            <FileX className="w-3.5 h-3.5" />
                          ) : isSpam ? (
                            <ShieldAlert className="w-3.5 h-3.5" />
                          ) : (
                            <ShieldCheck className="w-3.5 h-3.5" />
                          )}
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-medium text-white truncate max-w-xs sm:max-w-md font-mono" title={item.filename}>
                              {item.filename}
                            </span>
                            <span className="text-[11px] font-mono text-slate-500 tabular-nums">
                              ({formatFileSize(item.file_size_bytes)})
                            </span>
                            {item.id && (
                              <span className="text-[10px] font-mono text-slate-400 bg-[#101216] px-1.5 py-0.5 rounded border border-white/[0.06]">
                                DB #{item.id}
                              </span>
                            )}
                          </div>
                          {item.eml_metadata?.subject && (
                            <p className="text-xs text-slate-400 truncate mt-0.5">
                              Subject: <span className="text-slate-300">{item.eml_metadata.subject}</span>
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Right-side Badges & Toggle */}
                      <div className="flex items-center gap-2.5 shrink-0 self-end sm:self-center">
                        {isFailed ? (
                          <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-[#cf222e]/15 text-[#ff8182] border border-[#cf222e]/40">
                            Failed
                          </span>
                        ) : (
                          <>
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-mono font-medium ${
                                isSpam
                                  ? 'bg-[#cf222e]/15 text-[#ff8182] border border-[#cf222e]/40'
                                  : 'bg-[#2da44e]/15 text-[#56d364] border border-[#2da44e]/35'
                              }`}
                            >
                              {item.email_classification}
                            </span>

                            <ThreatBadge threatLevel={item.threat_level} size="sm" />

                            <div className="text-right font-mono">
                              <span className="text-slate-500 block text-[10px]">Risk</span>
                              <span
                                className={`text-xs font-semibold tabular-nums ${
                                  (item.overall_risk_score || 0) >= 50 ? 'text-[#ff8182]' : 'text-[#56d364]'
                                }`}
                              >
                                {(item.overall_risk_score || 0).toFixed(1)}%
                              </span>
                            </div>
                          </>
                        )}

                        <div className="p-1 rounded bg-[#101216] border border-white/[0.06] text-slate-400 hover:text-white transition-colors">
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </div>
                      </div>
                    </div>

                    {/* Collapsible Details Body */}
                    {isExpanded && (
                      <div className="p-4 border-t border-white/[0.06] bg-[#101216]/60 space-y-4">
                        {/* Error state display */}
                        {isFailed ? (
                          <div className="p-3.5 rounded-lg bg-[#1a1416] border border-[#cf222e]/40 text-[#ff8182] text-xs space-y-1">
                            <div className="font-semibold flex items-center gap-1.5">
                              <AlertCircle className="w-3.5 h-3.5 text-[#cf222e]" />
                              <span>Analysis error</span>
                            </div>
                            <p className="font-mono text-slate-300 pl-5 text-xs">
                              {item.error_message || 'Unknown processing error.'}
                            </p>
                          </div>
                        ) : (
                          <>
                            {/* Parsed RFC 822 Email Headers */}
                            {item.eml_metadata && (
                              <div className="rounded-lg border border-white/[0.08] bg-[#14171b] p-3.5 space-y-2">
                                <h5 className="text-xs font-semibold text-white flex items-center gap-1.5 font-mono">
                                  <FileText className="w-3.5 h-3.5 text-slate-400" />
                                  <span>RFC 822 Email Headers</span>
                                </h5>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
                                  <div className="p-2 rounded bg-[#101216] border border-white/[0.06]">
                                    <span className="text-slate-500 text-[10px] block">Sender:</span>
                                    <span className="text-slate-200 break-all">{item.eml_metadata.sender || '—'}</span>
                                  </div>

                                  <div className="p-2 rounded bg-[#101216] border border-white/[0.06]">
                                    <span className="text-slate-500 text-[10px] block">Recipient:</span>
                                    <span className="text-slate-200 break-all">{item.eml_metadata.recipient || '—'}</span>
                                  </div>

                                  <div className="p-2 rounded bg-[#101216] border border-white/[0.06]">
                                    <span className="text-slate-500 text-[10px] block">Date:</span>
                                    <span className="text-slate-200 tabular-nums">{item.eml_metadata.date || '—'}</span>
                                  </div>

                                  <div className="p-2 rounded bg-[#101216] border border-white/[0.06]">
                                    <span className="text-slate-500 text-[10px] block">Subject:</span>
                                    <span className="text-slate-200 font-medium">{item.eml_metadata.subject || '—'}</span>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Overall Security Assessment Explanation */}
                            {item.verdict_explanation && (
                              <div className="p-3 rounded-lg bg-[#14171b] border border-white/[0.08] text-xs text-slate-300 leading-relaxed font-sans">
                                <span className="font-semibold text-white font-mono text-[11px] block mb-1">
                                  Overall security assessment:
                                </span>
                                {item.verdict_explanation}
                              </div>
                            )}

                            {/* Phishing Intent Card */}
                            {item.phishing_intent_analysis && (
                              <PhishingIntentCard phishingIntent={item.phishing_intent_analysis} />
                            )}

                            {/* Dual Representation Threat Cards */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              {item.email_analysis && (
                                <EmailResultCard
                                  emailAnalysis={item.email_analysis}
                                  urlSummary={item.url_summary}
                                />
                              )}

                              <URLDetailTable urls={item.url_details || []} />
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
