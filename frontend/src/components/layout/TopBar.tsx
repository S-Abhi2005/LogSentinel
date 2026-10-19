import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { AlertItem } from '../../types';
import { SeverityBadge } from '../common/SeverityBadge';

export const TopBar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isAlertsOpen, setIsAlertsOpen] = useState<boolean>(false);
  const [backendHealthy, setBackendHealthy] = useState<boolean>(true);

  // Map route to title
  const pageTitles: Record<string, string> = {
    '/': 'Overview Dashboard',
    '/logs': 'Logs Explorer',
    '/incidents': 'Incident Management',
    '/rules': 'Detection Rules',
    '/services': 'Service Registry & Ingestion Keys',
    '/alerts': 'Alert Notifications',
    '/audit': 'Audit & Security Logs',
    '/settings': 'System Settings & Profile',
  };

  const currentTitle = pageTitles[location.pathname] || 'LogSentinel';

  const fetchAlerts = async () => {
    try {
      const data = await api.get<{ items: AlertItem[]; unread_count: number }>('/alerts?limit=5');
      setAlerts(data.items);
      setUnreadCount(data.unread_count);
      setBackendHealthy(true);
    } catch (err) {
      setBackendHealthy(false);
      console.warn('Backend health check or alert fetch failed:', err);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const timer = setInterval(fetchAlerts, 15000); // refresh alerts every 15s
    return () => clearInterval(timer);
  }, []);

  const markAllRead = async () => {
    try {
      await api.post('/alerts/read-all');
      setUnreadCount(0);
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
    } catch (err) {
      console.error('Failed to mark alerts as read:', err);
    }
  };

  return (
    <header className="h-16 bg-navy-900 border-b border-charcoal-800 px-6 flex items-center justify-between z-20 shrink-0">
      {/* Title & Breadcrumbs */}
      <div>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <span>Platform</span>
          <span>/</span>
          <span className="text-slate-200 capitalize font-medium">{location.pathname.replace('/', '') || 'Overview'}</span>
        </div>
        <h2 className="text-base font-bold text-white tracking-tight">{currentTitle}</h2>
      </div>

      {/* Right Action Icons */}
      <div className="flex items-center space-x-4">
        {/* Live System Status Indicator */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-navy-950 rounded-full border border-slate-800 text-xs">
          <span className={`w-2 h-2 rounded-full ${backendHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-slate-300 font-medium">
            {backendHealthy ? 'Live Ingestion Active' : 'API Connecting...'}
          </span>
        </div>

        {/* Alerts Bell Popover */}
        <div className="relative">
          <button
            onClick={() => setIsAlertsOpen(!isAlertsOpen)}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg relative transition"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-navy-900">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {isAlertsOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-navy-900 border border-charcoal-700 rounded-xl shadow-2xl py-3 z-50">
              <div className="flex items-center justify-between px-4 pb-2 border-b border-slate-800">
                <span className="text-xs font-bold text-white uppercase tracking-wider">Recent Alerts</span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-[11px] text-brand-400 hover:text-brand-300 transition"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-64 overflow-y-auto divide-y divide-slate-800/60">
                {alerts.length === 0 ? (
                  <div className="py-6 text-center text-xs text-slate-400">No alerts triggered</div>
                ) : (
                  alerts.map((alert) => (
                    <div
                      key={alert.id}
                      onClick={() => {
                        setIsAlertsOpen(false);
                        navigate('/alerts');
                      }}
                      className={`p-3 text-left hover:bg-slate-800/50 cursor-pointer transition ${
                        !alert.is_read ? 'bg-brand-500/5' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <SeverityBadge severity={alert.severity} size="sm" />
                        <span className="text-[10px] text-slate-400">
                          {new Date(alert.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-xs font-medium text-slate-200 line-clamp-1">{alert.title}</div>
                      <div className="text-[11px] text-slate-400 line-clamp-1">{alert.message}</div>
                    </div>
                  ))
                )}
              </div>

              <div className="px-4 pt-2 border-t border-slate-800 text-center">
                <button
                  onClick={() => {
                    setIsAlertsOpen(false);
                    navigate('/alerts');
                  }}
                  className="text-xs text-brand-400 hover:text-brand-300 font-medium"
                >
                  View all alerts &rarr;
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User Role Pill */}
        <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-xs font-bold text-white ring-1 ring-brand-400">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
        </div>
      </div>
    </header>
  );
};
