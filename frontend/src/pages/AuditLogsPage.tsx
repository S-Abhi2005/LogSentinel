import React, { useState, useEffect, useCallback } from 'react';
import { Search, RefreshCw, Shield } from 'lucide-react';
import { api } from '../api/client';
import { AuditLogItem } from '../types';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const pageSize = 25;
  const [totalPages, setTotalPages] = useState<number>(1);
  const [actionSearch, setActionSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAuditLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (actionSearch.trim()) params.append('action', actionSearch.trim());

      const res = await api.get<{ items: AuditLogItem[]; total: number; total_pages: number }>(
        `/audit-logs?${params.toString()}`
      );
      setLogs(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      if (err?.status === 403) {
        setError('Forbidden: Only Super Administrators can view audit and security logs.');
      } else {
        setError(err?.message || 'Failed to load audit logs');
      }
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, actionSearch]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchAuditLogs();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Audit & Security Logs</h1>
          <p className="text-xs text-slate-400">
            Immutable append-only record of administrative operations and authentication events
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchAuditLogs}
            className="flex items-center space-x-2 px-3 py-1.5 bg-navy-900 hover:bg-slate-800 border border-charcoal-700 rounded-lg text-xs font-medium text-slate-200 transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <Shield className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Bar */}
      <div className="bg-navy-900 border border-charcoal-700 rounded-2xl p-4 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
            <input
              type="text"
              value={actionSearch}
              onChange={(e) => setActionSearch(e.target.value)}
              placeholder="Search action or event (e.g. 'LOGIN_SUCCESS', 'SERVICE_CREATED', 'RULE_UPDATED')..."
              className="w-full bg-navy-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium cursor-pointer"
          >
            Filter
          </button>
        </form>
      </div>

      {/* Audit Table */}
      <div className="bg-navy-900 border border-charcoal-700 rounded-2xl overflow-hidden shadow-sm">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>
            Total <strong className="text-slate-200">{total}</strong> security audit entries
          </span>
          <span>Page {page} of {totalPages || 1}</span>
        </div>

        {loading ? (
          <div className="p-6">
            <LoadingSkeleton rows={6} height="h-12" />
          </div>
        ) : logs.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={Shield}
              title="No Audit Records"
              description="No audit events matched your search criteria."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-navy-950 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4 w-44">Timestamp (UTC)</th>
                  <th className="py-2.5 px-4">Action</th>
                  <th className="py-2.5 px-4">Actor</th>
                  <th className="py-2.5 px-4">Target Type</th>
                  <th className="py-2.5 px-4">Details</th>
                  <th className="py-2.5 px-4 w-28">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(log.created_at).toISOString().replace('T', ' ').slice(0, 19)}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-200 px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      <div>{log.actor_email}</div>
                      <span className="text-[10px] text-slate-400 font-sans capitalize">
                        {log.actor_role?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 capitalize font-sans">
                      {log.target_type}
                      {log.target_id && <span className="block text-[10px] font-mono text-slate-400">{log.target_id.slice(0, 12)}...</span>}
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-slate-400 text-[11px]">
                      {log.details_json ? JSON.stringify(log.details_json) : '-'}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {log.ip_address || 'internal'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="px-5 py-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing page {page} of {totalPages || 1}
          </div>
          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded transition cursor-pointer"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded transition cursor-pointer"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
