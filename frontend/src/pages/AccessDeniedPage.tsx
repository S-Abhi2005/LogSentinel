import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, LayoutDashboard, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const AccessDeniedPage: React.FC<{
  requiredRole?: string;
  title?: string;
  message?: string;
}> = ({
  requiredRole = 'Super Administrator (super_admin)',
  title = 'Access Denied',
  message,
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-800 rounded-2xl p-8 text-center shadow-xl dark:shadow-2xl relative overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-48 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="w-16 h-16 mx-auto rounded-2xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 flex items-center justify-center text-rose-500 dark:text-rose-400 mb-6 shadow-inner">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight mb-2">{title}</h1>
        <p className="text-xs text-slate-600 dark:text-slate-300 mb-4 leading-relaxed">
          {message || (
            <>
              You are signed in as{' '}
              <span className="font-semibold text-slate-900 dark:text-white">{user?.full_name || 'Authenticated User'}</span>{' '}
              with role <span className="font-mono text-rose-600 dark:text-rose-300 font-semibold">{user?.role}</span>.
              This area is restricted to accounts with{' '}
              <span className="font-semibold text-rose-600 dark:text-rose-300">{requiredRole}</span> privileges.
            </>
          )}
        </p>

        <div className="p-3 bg-slate-50 dark:bg-navy-950/80 border border-slate-200 dark:border-charcoal-800/80 rounded-xl mb-6 text-left text-[11px] text-slate-600 dark:text-slate-400 font-mono space-y-1">
          <div className="flex justify-between">
            <span>Identity:</span>
            <span className="text-slate-900 dark:text-slate-200 font-medium">{user?.email || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span>Current Role:</span>
            <span className="text-slate-900 dark:text-slate-200 capitalize font-medium">{user?.role || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span>Policy Status:</span>
            <span className="text-rose-600 dark:text-rose-400 font-semibold">403 FORBIDDEN</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-2.5">
          <button
            onClick={() => navigate('/')}
            className="flex-1 py-2 px-3 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer shadow-sm"
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </button>
          <button
            onClick={() => navigate('/incidents')}
            className="flex-1 py-2 px-3 bg-slate-100 hover:bg-slate-200 dark:bg-navy-950 dark:hover:bg-charcoal-800 border border-slate-200 dark:border-charcoal-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
            <span>Incidents</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccessDeniedPage;
