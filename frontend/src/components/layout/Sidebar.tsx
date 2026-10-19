import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Terminal,
  AlertTriangle,
  ShieldCheck,
  Server,
  Bell,
  FileText,
  Settings,
  LogOut,
  Radio,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();

  const navItems = [
    { label: 'Overview', to: '/', icon: LayoutDashboard },
    { label: 'Logs Explorer', to: '/logs', icon: Terminal },
    { label: 'Incidents', to: '/incidents', icon: AlertTriangle },
    { label: 'Detection Rules', to: '/rules', icon: ShieldCheck },
    { label: 'Services', to: '/services', icon: Server },
    { label: 'Alerts', to: '/alerts', icon: Bell },
    { label: 'Audit Logs', to: '/audit', icon: FileText, adminOnly: true },
    { label: 'Settings', to: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-navy-900 border-r border-charcoal-800 flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-charcoal-800 space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-blue-400 flex items-center justify-center shadow-md shadow-brand-500/20 ring-1 ring-blue-400/40">
          <Radio className="w-5 h-5 text-white animate-pulse" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
            LogSentinel
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
              v1.0
            </span>
          </h1>
          <p className="text-[11px] text-slate-400 font-medium">Cloud Log Intelligence</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Observability
        </div>
        {navItems.map((item) => {
          if (item.adminOnly && user?.role !== 'super_admin') {
            return null;
          }
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-600/15 text-brand-400 border border-brand-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 mr-3 shrink-0" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      {/* User Footer Profile */}
      <div className="p-3 border-t border-charcoal-800">
        <div className="p-2.5 rounded-xl bg-navy-950/80 border border-slate-800 flex items-center justify-between">
          <div className="truncate mr-2">
            <div className="text-xs font-semibold text-slate-200 truncate">
              {user?.full_name || 'User'}
            </div>
            <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="capitalize">{user?.role?.replace('_', ' ')}</span>
            </div>
          </div>
          <button
            onClick={logout}
            title="Log Out"
            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-950/40 rounded-lg transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
