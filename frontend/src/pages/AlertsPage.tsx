import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, CheckCheck, RefreshCw, ArrowRight } from 'lucide-react';
import { api } from '../api/client';
import { AlertItem } from '../types';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';

export const AlertsPage: React.FC = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterRead, setFilterRead] = useState<string>('');

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      let endpoint = '/alerts?limit=100';
      if (filterRead !== '') {
        endpoint += `&is_read=${filterRead === 'read'}`;
      }
      const data = await api.get<{ items: AlertItem[]; unread_count: number }>(endpoint);
      setAlerts(data.items);
      setUnreadCount(data.unread_count);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  }, [filterRead]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleMarkRead = async (alertId: string) => {
    try {
      await api.post(`/alerts/${alertId}/read`);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error('Failed to mark alert as read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/alerts/read-all');
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all alerts as read:', err);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Alert Notifications</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real-time incident signals and threshold breach notifications
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-semibold transition cursor-pointer shadow-sm"
            >
              <CheckCheck className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
              <span>Mark all read</span>
            </button>
          )}
          <button
            onClick={fetchAlerts}
            className="flex items-center space-x-2 px-3 py-1.5 bg-white dark:bg-navy-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-charcoal-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 transition cursor-pointer shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 p-1 bg-white dark:bg-navy-900 rounded-xl border border-slate-200 dark:border-charcoal-700 w-fit text-xs shadow-sm transition-colors duration-150">
        <button
          onClick={() => setFilterRead('')}
          className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
            filterRead === ''
              ? 'bg-brand-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          All Alerts ({alerts.length})
        </button>
        <button
          onClick={() => setFilterRead('unread')}
          className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
            filterRead === 'unread'
              ? 'bg-brand-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          Unread ({unreadCount})
        </button>
        <button
          onClick={() => setFilterRead('read')}
          className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
            filterRead === 'read'
              ? 'bg-brand-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          Archived / Read
        </button>
      </div>

      {/* Alerts List */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl overflow-hidden shadow-sm transition-colors duration-150">
        {loading ? (
          <div className="p-6">
            <LoadingSkeleton rows={5} height="h-16" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={Bell}
              title="No Alerts"
              description="You have no notifications in this view."
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition ${
                  !alert.is_read ? 'bg-brand-50/60 dark:bg-brand-500/5' : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="pt-0.5">
                    <SeverityBadge severity={alert.severity} size="sm" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{alert.title}</h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{alert.message}</p>
                    <span className="text-[11px] text-slate-400 dark:text-slate-500 font-mono mt-1 block">
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                  {!alert.is_read && (
                    <button
                      onClick={() => handleMarkRead(alert.id)}
                      className="px-2.5 py-1 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 text-xs rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
                    >
                      Mark read
                    </button>
                  )}
                  {alert.incident_id && (
                    <button
                      onClick={() => navigate(`/incidents/${alert.incident_id}`)}
                      className="px-3 py-1 bg-brand-50 hover:bg-brand-600 text-brand-600 hover:text-white dark:bg-brand-600/20 dark:hover:bg-brand-600 dark:text-brand-300 dark:hover:text-white border border-brand-200 dark:border-transparent rounded-lg text-xs font-medium flex items-center gap-1 transition cursor-pointer"
                    >
                      <span>Open Incident</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
