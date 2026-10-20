import React from 'react';
import { LogSeverity, IncidentSeverity } from '../../types';

interface SeverityBadgeProps {
  severity: LogSeverity | IncidentSeverity | string;
  size?: 'sm' | 'md';
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, size = 'md' }) => {
  const sev = (severity || '').toUpperCase();

  const styles: Record<string, string> = {
    CRITICAL: 'bg-red-100 text-red-700 border border-red-300 dark:bg-red-950/80 dark:text-red-400 dark:border-red-800/80',
    ERROR: 'bg-rose-100 text-rose-700 border border-rose-300 dark:bg-rose-950/70 dark:text-rose-300 dark:border-rose-800/60',
    HIGH: 'bg-red-100 text-red-700 border border-red-300 dark:bg-red-950/80 dark:text-red-400 dark:border-red-800/80',
    WARNING: 'bg-amber-100 text-amber-700 border border-amber-300 dark:bg-amber-950/70 dark:text-amber-300 dark:border-amber-700/60',
    MEDIUM: 'bg-amber-100 text-amber-700 border border-amber-300 dark:bg-amber-950/70 dark:text-amber-300 dark:border-amber-700/60',
    INFO: 'bg-blue-100 text-blue-700 border border-blue-300 dark:bg-blue-950/70 dark:text-blue-300 dark:border-blue-800/60',
    LOW: 'bg-blue-100 text-blue-700 border border-blue-300 dark:bg-blue-950/70 dark:text-blue-300 dark:border-blue-800/60',
    DEBUG: 'bg-slate-100 text-slate-700 border border-slate-300 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-700',
  };

  const badgeStyle = styles[sev] || 'bg-slate-100 text-slate-700 border border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span className={`inline-flex items-center rounded-md font-mono uppercase tracking-wider ${sizeClasses} ${badgeStyle}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-80" />
      {sev}
    </span>
  );
};
