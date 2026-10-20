import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'incident' | 'health';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'incident' }) => {
  const s = (status || '').toUpperCase();

  const incidentStyles: Record<string, string> = {
    OPEN: 'bg-red-100 text-red-700 border border-red-300 dark:bg-red-950/70 dark:text-red-400 dark:border-red-800/80 animate-pulse',
    ACKNOWLEDGED: 'bg-amber-100 text-amber-800 border border-amber-300 dark:bg-amber-950/70 dark:text-amber-300 dark:border-amber-800/60',
    INVESTIGATING: 'bg-blue-100 text-blue-800 border border-blue-300 dark:bg-blue-950/70 dark:text-blue-300 dark:border-blue-800/60',
    RESOLVED: 'bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/70 dark:text-emerald-400 dark:border-emerald-800/60',
  };

  const healthStyles: Record<string, string> = {
    HEALTHY: 'bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/70 dark:text-emerald-400 dark:border-emerald-800/60',
    DEGRADED: 'bg-amber-100 text-amber-800 border border-amber-300 dark:bg-amber-950/70 dark:text-amber-300 dark:border-amber-800/60',
    CRITICAL: 'bg-red-100 text-red-700 border border-red-300 dark:bg-red-950/80 dark:text-red-400 dark:border-red-800/80 animate-pulse',
    UNKNOWN: 'bg-slate-100 text-slate-700 border border-slate-300 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-700',
  };

  const styleMap = type === 'health' ? healthStyles : incidentStyles;
  const currentStyle = styleMap[s] || 'bg-slate-100 text-slate-700 border border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide ${currentStyle}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-90" />
      {s}
    </span>
  );
};
