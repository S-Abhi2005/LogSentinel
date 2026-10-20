import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Download,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  X,
  Send,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../api/client';
import { LogEntry, LogListResponse, ServiceItem, LogSeverity } from '../types';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';

export const LogsExplorerPage: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(50);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [severity, setSeverity] = useState<string>('');
  const [serviceName, setServiceName] = useState<string>('');
  const [environment, setEnvironment] = useState<string>('');
  const [search, setSearch] = useState<string>('');
  const [traceId, setTraceId] = useState<string>('');
  const [timeRange, setTimeRange] = useState<string>('24h');

  // Expanded log row for metadata inspection
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Ingest Test Log Modal State
  const [isIngestModalOpen, setIsIngestModalOpen] = useState<boolean>(false);
  const [ingestApiKey, setIngestApiKey] = useState<string>('');
  const [ingestService, setIngestService] = useState<string>('');
  const [ingestEnv, setIngestEnv] = useState<string>('production');
  const [ingestSeverity, setIngestSeverity] = useState<LogSeverity>('INFO');
  const [ingestMessage, setIngestMessage] = useState<string>('');
  const [ingestTraceId, setIngestTraceId] = useState<string>('');
  const [ingestSubmitting, setIngestSubmitting] = useState<boolean>(false);
  const [ingestResult, setIngestResult] = useState<{ text: string; error: boolean } | null>(null);

  const fetchServices = async () => {
    try {
      const data = await api.get<ServiceItem[]>('/services');
      setServices(data);
      if (data.length > 0 && !ingestService) {
        setIngestService(data[0].name);
        setIngestEnv(data[0].environment);
      }
    } catch (err) {
      console.error('Failed to load services for filter:', err);
    }
  };

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      let startTime = '';
      const now = new Date();
      if (timeRange === '1h') startTime = new Date(now.getTime() - 60 * 60 * 1000).toISOString();
      else if (timeRange === '6h') startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString();
      else if (timeRange === '24h') startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
      else if (timeRange === '7d') startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();

      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (severity) params.append('severity', severity);
      if (serviceName) params.append('service_name', serviceName);
      if (environment) params.append('environment', environment);
      if (search.trim()) params.append('search', search.trim());
      if (traceId.trim()) params.append('trace_id', traceId.trim());
      if (startTime) params.append('start_time', startTime);

      const res = await api.get<LogListResponse>(`/logs?${params.toString()}`);
      setLogs(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load logs', err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, severity, serviceName, environment, search, traceId, timeRange]);

  useEffect(() => {
    fetchServices();
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  const clearFilters = () => {
    setSeverity('');
    setServiceName('');
    setEnvironment('');
    setSearch('');
    setTraceId('');
    setTimeRange('24h');
    setPage(1);
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleExportCSV = async () => {
    let startTime = '';
    const now = new Date();
    if (timeRange === '1h') startTime = new Date(now.getTime() - 60 * 60 * 1000).toISOString();
    else if (timeRange === '6h') startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString();
    else if (timeRange === '24h') startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    else if (timeRange === '7d') startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();

    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (serviceName) params.append('service_name', serviceName);
    if (environment) params.append('environment', environment);
    if (search.trim()) params.append('search', search.trim());
    if (traceId.trim()) params.append('trace_id', traceId.trim());
    if (startTime) params.append('start_time', startTime);

    await api.downloadBlob(`/logs/export?${params.toString()}`, `logsentinel_export_${Date.now()}.csv`);
  };

  const handleIngestLog = async (e: React.FormEvent) => {
    e.preventDefault();
    setIngestResult(null);

    if (!ingestApiKey.trim()) {
      setIngestResult({ text: 'Please enter an ingestion API key.', error: true });
      return;
    }
    if (!ingestMessage.trim()) {
      setIngestResult({ text: 'Log message cannot be empty.', error: true });
      return;
    }

    setIngestSubmitting(true);
    try {
      const payload = {
        service_name: ingestService,
        environment: ingestEnv,
        severity: ingestSeverity,
        message: ingestMessage.trim(),
        timestamp: new Date().toISOString(),
        source: 'manual-ui-ingest',
        trace_id: ingestTraceId.trim() || undefined,
        metadata: { ingested_via: 'web-ui', time: Date.now() },
      };

      const res = await fetch('/api/v1/logs/ingest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': ingestApiKey.trim(),
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        let errText = 'Failed to ingest log';
        try {
          const errData = await res.json();
          errText = errData?.detail?.message || errData?.detail || errText;
        } catch (_) {}
        throw new Error(errText);
      }

      setIngestResult({ text: 'Log event ingested successfully!', error: false });
      setIngestMessage('');
      setIngestTraceId('');
      await fetchLogs();
      setTimeout(() => {
        setIsIngestModalOpen(false);
        setIngestResult(null);
      }, 1200);
    } catch (err: any) {
      setIngestResult({ text: err?.message || 'Ingestion request failed.', error: true });
    } finally {
      setIngestSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Logs Explorer</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">Search, stream, and query ingested application telemetry</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              setIngestResult(null);
              setIsIngestModalOpen(true);
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition shadow-sm cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Ingest Test Log</span>
          </button>
          <button
            onClick={fetchLogs}
            className="flex items-center space-x-2 px-3 py-1.5 bg-white dark:bg-navy-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-charcoal-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 transition cursor-pointer shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button
            onClick={handleExportCSV}
            className="flex items-center space-x-2 px-3 py-1.5 bg-brand-600 hover:bg-brand-500 rounded-lg text-xs font-medium text-white transition shadow-sm cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Filter Control Bar */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-4 shadow-sm space-y-3 transition-colors duration-150">
        {/* Keyword Search input */}
        <form onSubmit={handleSearchSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search log messages (e.g., 'NullReferenceException', 'timeout', 'commit failed')..."
              className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-brand-500 transition font-mono"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-white rounded-lg text-xs font-medium transition cursor-pointer"
          >
            Search
          </button>
        </form>

        {/* Filter Dropdowns */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 pt-2 border-t border-slate-100 dark:border-slate-800/80">
          {/* Time Range */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Time Window</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="1h">Last 1 hour</option>
              <option value="6h">Last 6 hours</option>
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="all">All Available</option>
            </select>
          </div>

          {/* Severity */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Severity</label>
            <select
              value={severity}
              onChange={(e) => {
                setSeverity(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="ERROR">ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
              <option value="DEBUG">DEBUG</option>
            </select>
          </div>

          {/* Service */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Service</label>
            <select
              value={serviceName}
              onChange={(e) => {
                setServiceName(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Services</option>
              {services.map((s) => (
                <option key={s.id} value={s.name}>
                  {s.name} ({s.environment})
                </option>
              ))}
            </select>
          </div>

          {/* Environment */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Environment</label>
            <select
              value={environment}
              onChange={(e) => {
                setEnvironment(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Environments</option>
              <option value="production">production</option>
              <option value="staging">staging</option>
              <option value="testing">testing</option>
              <option value="development">development</option>
            </select>
          </div>

          {/* Trace ID Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Trace ID</label>
            <input
              type="text"
              value={traceId}
              onChange={(e) => setTraceId(e.target.value)}
              placeholder="e.g. trc-12345"
              className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>
        </div>

        {/* Clear Filters indicator */}
        {(severity || serviceName || environment || search || traceId || timeRange !== '24h') && (
          <div className="flex items-center justify-between pt-2 text-xs text-slate-500 dark:text-slate-400">
            <span>Filtered results</span>
            <button
              onClick={clearFilters}
              className="text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 font-medium flex items-center gap-1 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
              <span>Reset all filters</span>
            </button>
          </div>
        )}
      </div>

      {/* Logs Table */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl overflow-hidden shadow-sm transition-colors duration-150">
        <div className="px-5 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>
            Showing {logs.length} of <strong className="text-slate-800 dark:text-slate-200">{total}</strong> matched logs
          </span>
          <span className="font-mono">Page {page} of {totalPages || 1}</span>
        </div>

        {loading ? (
          <div className="p-6">
            <LoadingSkeleton rows={6} height="h-12" />
          </div>
        ) : logs.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Logs Matched"
              description="No logs found matching your filter criteria. Try expanding the time window or clearing search terms."
              actionText="Reset Filters"
              onAction={clearFilters}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-50 dark:bg-navy-950 text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 w-8"></th>
                  <th className="py-2.5 px-3 w-44">Timestamp (UTC)</th>
                  <th className="py-2.5 px-3 w-28">Severity</th>
                  <th className="py-2.5 px-3 w-40">Service</th>
                  <th className="py-2.5 px-3">Message</th>
                  <th className="py-2.5 px-3 w-36">Trace ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/70">
                {logs.map((log) => {
                  const isExpanded = expandedLogId === log.id;
                  return (
                    <React.Fragment key={log.id}>
                      <tr
                        onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                        className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition ${
                          isExpanded ? 'bg-slate-50/80 dark:bg-slate-800/30' : ''
                        }`}
                      >
                        <td className="py-2.5 px-3 text-slate-400">
                          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                          {new Date(log.timestamp).toISOString().replace('T', ' ').slice(0, 19)}
                        </td>
                        <td className="py-2.5 px-3">
                          <SeverityBadge severity={log.severity} size="sm" />
                        </td>
                        <td className="py-2.5 px-3 text-slate-700 dark:text-slate-300">
                          <span className="font-semibold text-slate-800 dark:text-slate-200">{log.service_name}</span>
                          <span className="text-[10px] text-slate-400 ml-1">[{log.environment}]</span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-800 dark:text-slate-200 font-sans line-clamp-1">
                          {log.message}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 dark:text-slate-400 text-[11px] truncate">
                          {log.trace_id || '-'}
                        </td>
                      </tr>

                      {/* Expanded Structured Details */}
                      {isExpanded && (
                        <tr className="bg-slate-50/80 dark:bg-navy-950/90 border-b border-slate-200 dark:border-slate-800">
                          <td colSpan={6} className="p-4 pl-12 font-sans">
                            <div className="space-y-3 bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm">
                              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                                <div className="flex items-center space-x-3 text-xs">
                                  <span className="text-slate-500 dark:text-slate-400">Log ID:</span>
                                  <span className="font-mono text-slate-700 dark:text-slate-300">{log.id}</span>
                                  <button
                                    onClick={() => copyToClipboard(log.id, `id-${log.id}`)}
                                    className="p-1 hover:text-slate-800 dark:hover:text-white text-slate-400 transition"
                                    title="Copy Log ID"
                                  >
                                    {copiedId === `id-${log.id}` ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                                  </button>
                                </div>
                                {log.trace_id && (
                                  <div className="flex items-center space-x-2 text-xs">
                                    <span className="text-slate-500 dark:text-slate-400">Trace:</span>
                                    <span className="font-mono text-brand-600 dark:text-brand-400">{log.trace_id}</span>
                                    <button
                                      onClick={() => copyToClipboard(log.trace_id!, `trc-${log.id}`)}
                                      className="p-1 hover:text-slate-800 dark:hover:text-white text-slate-400 transition"
                                      title="Copy Trace ID"
                                    >
                                      {copiedId === `trc-${log.id}` ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                                    </button>
                                  </div>
                                )}
                              </div>

                              <div>
                                <span className="text-xs font-semibold text-slate-700 dark:text-slate-400 block mb-1">Full Message</span>
                                <pre className="p-3 bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-mono text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                                  {log.message}
                                </pre>
                              </div>

                              {log.metadata_json && Object.keys(log.metadata_json).length > 0 && (
                                <div>
                                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-400 block mb-1">Structured Metadata</span>
                                  <pre className="p-3 bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-mono text-blue-600 dark:text-blue-300 overflow-x-auto">
                                    {JSON.stringify(log.metadata_json, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="px-5 py-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center space-x-2">
            <span>Per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded px-2 py-1 text-slate-800 dark:text-slate-200"
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 disabled:opacity-40 text-slate-700 dark:text-slate-200 rounded transition cursor-pointer"
            >
              Previous
            </button>
            <span>
              Page <strong className="text-slate-900 dark:text-white">{page}</strong> of {totalPages || 1}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 disabled:opacity-40 text-slate-700 dark:text-slate-200 rounded transition cursor-pointer"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Ingest Test Log Modal */}
      {isIngestModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Send className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Ingest Test Telemetry Log</h3>
              </div>
              <button
                onClick={() => setIsIngestModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {ingestResult && (
              <div
                className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
                  ingestResult.error
                    ? 'bg-red-50 dark:bg-red-950/70 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
                    : 'bg-emerald-50 dark:bg-emerald-950/70 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
                }`}
              >
                {ingestResult.error ? <AlertCircle className="w-4 h-4 shrink-0" /> : <CheckCircle2 className="w-4 h-4 shrink-0" />}
                <span>{ingestResult.text}</span>
              </div>
            )}

            <form onSubmit={handleIngestLog} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
                  Ingestion API Key (X-API-Key) <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={ingestApiKey}
                  onChange={(e) => setIngestApiKey(e.target.value)}
                  placeholder="ls_live_... (issued from Services page)"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:border-brand-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Issue an active key from the <span className="font-semibold text-brand-600 dark:text-brand-400">Services</span> page.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Target Service</label>
                  <select
                    value={ingestService}
                    onChange={(e) => {
                      setIngestService(e.target.value);
                      const svc = services.find((s) => s.name === e.target.value);
                      if (svc) setIngestEnv(svc.environment);
                    }}
                    className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                  >
                    {services.map((s) => (
                      <option key={s.id} value={s.name}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Environment</label>
                  <input
                    type="text"
                    value={ingestEnv}
                    onChange={(e) => setIngestEnv(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Severity</label>
                  <select
                    value={ingestSeverity}
                    onChange={(e) => setIngestSeverity(e.target.value as LogSeverity)}
                    className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500 font-semibold"
                  >
                    <option value="INFO">INFO</option>
                    <option value="DEBUG">DEBUG</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Trace ID (Optional)</label>
                  <input
                    type="text"
                    value={ingestTraceId}
                    onChange={(e) => setIngestTraceId(e.target.value)}
                    placeholder="trc-test-999"
                    className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
                  Log Message <span className="text-red-500">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  value={ingestMessage}
                  onChange={(e) => setIngestMessage(e.target.value)}
                  placeholder="e.g. Database transaction timeout during payment verification"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 font-mono text-xs focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsIngestModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={ingestSubmitting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{ingestSubmitting ? 'Ingesting...' : 'Send Event'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
