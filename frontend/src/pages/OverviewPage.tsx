import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  AlertCircle,
  Server,
  FileText,
  Bell,
  RefreshCw,
  ArrowRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { api } from '../api/client';
import { DashboardAllData, Incident } from '../types';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { useTheme } from '../context/ThemeContext';

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [data, setData] = useState<DashboardAllData | null>(null);
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [allData, incData] = await Promise.all([
        api.get<DashboardAllData>('/dashboard/all'),
        api.get<{ items: Incident[] }>('/incidents?page_size=5'),
      ]);
      setData(allData);
      setRecentIncidents(incData.items);
    } catch (err: any) {
      setError(err?.message || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const SEVERITY_COLORS: Record<string, string> = {
    CRITICAL: '#ef4444',
    ERROR: '#f43f5e',
    WARNING: '#f59e0b',
    INFO: '#3b82f6',
    DEBUG: '#64748b',
  };

  const tooltipStyle = isDark
    ? { backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc', borderRadius: '8px', fontSize: '12px' }
    : { backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a', borderRadius: '8px', fontSize: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' };
  const gridStroke = isDark ? '#1e293b' : '#e2e8f0';
  const tickStroke = isDark ? '#64748b' : '#94a3b8';

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-24 bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-xl animate-pulse" />
          ))}
        </div>
        <LoadingSkeleton rows={4} height="h-64" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center bg-white dark:bg-navy-900 border border-red-200 dark:border-red-900/50 rounded-2xl shadow-sm max-w-lg mx-auto my-12">
        <AlertCircle className="w-12 h-12 text-red-500 dark:text-red-400 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-900 dark:text-white">Error Loading Dashboard</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">{error}</p>
        <button
          onClick={fetchDashboardData}
          className="mt-4 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-medium cursor-pointer transition shadow-sm"
        >
          Try Again
        </button>
      </div>
    );
  }

  const summary = data?.summary;

  return (
    <div className="space-y-8">
      {/* Header controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">System Telemetry & Health</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">Real-time incident response and log intelligence metrics</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDashboardData}
            className="flex items-center space-x-2 px-3 py-1.5 bg-white dark:bg-navy-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-charcoal-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 transition cursor-pointer shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 6 Key Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-xl p-4 shadow-sm transition-colors duration-150">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs mb-1">
            <span>Total Logs</span>
            <FileText className="w-4 h-4 text-brand-500 dark:text-brand-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">{summary?.total_logs ?? 0}</div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Aggregated events</div>
        </div>

        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-xl p-4 shadow-sm transition-colors duration-150">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs mb-1">
            <span>Error Logs</span>
            <AlertCircle className="w-4 h-4 text-rose-500 dark:text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-500 dark:text-rose-400 tracking-tight">{summary?.error_logs ?? 0}</div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">ERROR & CRITICAL</div>
        </div>

        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-xl p-4 shadow-sm transition-colors duration-150">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs mb-1">
            <span>Active Incidents</span>
            <AlertTriangle className="w-4 h-4 text-amber-500 dark:text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-500 dark:text-amber-400 tracking-tight">{summary?.active_incidents ?? 0}</div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Requires triage</div>
        </div>

        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-xl p-4 shadow-sm transition-colors duration-150">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs mb-1">
            <span>Critical Incidents</span>
            <AlertTriangle className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-red-500 dark:text-red-400 tracking-tight">{summary?.critical_incidents ?? 0}</div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Highest severity</div>
        </div>

        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-xl p-4 shadow-sm transition-colors duration-150">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs mb-1">
            <span>Healthy Services</span>
            <Server className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 tracking-tight">
            {summary?.healthy_services ?? 0} / {summary?.total_services ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Operational nodes</div>
        </div>

        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-xl p-4 shadow-sm transition-colors duration-150">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs mb-1">
            <span>Active Alerts</span>
            <Bell className="w-4 h-4 text-blue-500 dark:text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-500 dark:text-blue-400 tracking-tight">{summary?.unacknowledged_alerts ?? 0}</div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Unread notifications</div>
        </div>
      </div>

      {/* Row 1: Log Volume Time-series & Severity Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Log Volume Over Time */}
        <div className="lg:col-span-2 bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm transition-colors duration-150">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Log & Error Volume (Past 24 Hours)</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Total telemetry events vs error spikes</p>
            </div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              1h Buckets
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.log_volume || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.5} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="timestamp" stroke={tickStroke} fontSize={11} tickLine={false} />
                <YAxis stroke={tickStroke} fontSize={11} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="count" stroke="#3b82f6" fillOpacity={1} fill="url(#colorCount)" name="Total Logs" />
                <Area type="monotone" dataKey="errors" stroke="#ef4444" fillOpacity={1} fill="url(#colorErrors)" name="Errors" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Breakdown Pie */}
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm flex flex-col justify-between transition-colors duration-150">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Logs by Severity</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Proportion of events across severities</p>
          </div>
          <div className="h-48 my-auto">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.severity_breakdown || []}
                  dataKey="count"
                  nameKey="severity"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                >
                  {(data?.severity_breakdown || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.severity] || '#64748b'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 justify-center pt-2 border-t border-slate-100 dark:border-slate-800">
            {(data?.severity_breakdown || []).map((item) => (
              <div key={item.severity} className="flex items-center text-xs text-slate-600 dark:text-slate-300 gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: SEVERITY_COLORS[item.severity] || '#64748b' }} />
                <span>{item.severity}:</span>
                <span className="font-bold text-slate-900 dark:text-white">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 2: Incident Trends & Service Incident Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Incident Trends 7 Days */}
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm transition-colors duration-150">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Incident Trends (Past 7 Days)</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Opened vs Resolved incident progression</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.incident_trends || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="date" stroke={tickStroke} fontSize={11} tickLine={false} />
                <YAxis stroke={tickStroke} fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="opened" fill="#f59e0b" name="Opened" radius={[4, 4, 0, 0]} />
                <Bar dataKey="resolved" fill="#10b981" name="Resolved" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Incidents by Service */}
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm transition-colors duration-150">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Incidents by Service</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Service concentration of detection triggers</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data?.incidents_by_service || []}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 40, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis type="number" stroke={tickStroke} fontSize={11} tickLine={false} allowDecimals={false} />
                <YAxis type="category" dataKey="service_name" stroke={tickStroke} fontSize={11} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="incident_count" fill="#3b82f6" name="Total Incidents" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 3: Recent Incidents Table & Service Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Incidents (2 cols) */}
        <div className="lg:col-span-2 bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm transition-colors duration-150">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Recent Active Incidents</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Triggered by detection engine</p>
            </div>
            <button
              onClick={() => navigate('/incidents')}
              className="text-xs text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 font-medium flex items-center gap-1 cursor-pointer"
            >
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-navy-950 text-slate-500 dark:text-slate-400 uppercase font-mono tracking-wider border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Title / Trigger</th>
                  <th className="py-2.5 px-3">Service</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Last Detected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {recentIncidents.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      No active incidents detected.
                    </td>
                  </tr>
                ) : (
                  recentIncidents.map((inc) => (
                    <tr
                      key={inc.id}
                      onClick={() => navigate(`/incidents/${inc.id}`)}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition"
                    >
                      <td className="py-3 px-3">
                        <SeverityBadge severity={inc.severity} size="sm" />
                      </td>
                      <td className="py-3 px-3">
                        <div className="font-semibold text-slate-800 dark:text-slate-200 line-clamp-1">{inc.title}</div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-1">{inc.error_signature || 'Rule triggered'}</div>
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-600 dark:text-slate-300">
                        {inc.service_name}
                        <span className="text-[10px] text-slate-400 ml-1">({inc.environment})</span>
                      </td>
                      <td className="py-3 px-3">
                        <StatusBadge status={inc.status} />
                      </td>
                      <td className="py-3 px-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                        {new Date(inc.last_detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Service Health (1 col) */}
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm flex flex-col justify-between transition-colors duration-150">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Service Health</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">Fleet telemetry status</p>
              </div>
              <button
                onClick={() => navigate('/services')}
                className="text-xs text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 font-medium"
              >
                Manage
              </button>
            </div>

            <div className="space-y-3 mt-4">
              {(data?.service_health || []).map((svc) => (
                <div
                  key={svc.service_id}
                  onClick={() => navigate('/services')}
                  className="p-3 bg-slate-50 dark:bg-navy-950 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition cursor-pointer flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                      <span>{svc.service_name}</span>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">[{svc.environment}]</span>
                    </div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      {svc.error_count_last_hour} errors past hour
                    </div>
                  </div>
                  <div>
                    <StatusBadge status={svc.status} type="health" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 mt-4 text-center">
            <span className="text-[11px] text-slate-400">
              Evaluated every 60s against configured telemetry windows
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
