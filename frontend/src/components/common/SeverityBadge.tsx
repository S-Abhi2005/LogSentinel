import React from 'react';
import { LogSeverity, IncidentSeverity } from '../../types';

interface SeverityBadgeProps {
  severity: LogSeverity | IncidentSeverity | string;
  size?: 'sm' | 'md';
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, size = 'md' }) => {
  const sev = (severity || '').toUpperCase();

  const styles: Record<string, string> = {
    CRITICAL: 'bg-red-950/80 text-red-400 border border-red-800/80 shadow-[0_0_12px_rgba(239,68,68,0.25)]',
    ERROR: 'bg-rose-950/70 text-rose-300 border border-rose-800/60',
    HIGH: 'bg-red-950/80 text-red-400 border border-red-800/80',
    WARNING: 'bg-amber-950/70 text-amber-300 border border-amber-700/60',
    MEDIUM: 'bg-amber-950/70 text-amber-300 border border-amber-700/60',
    INFO: 'bg-blue-950/70 text-blue-300 border border-blue-800/60',
    LOW: 'bg-blue-950/70 text-blue-300 border border-blue-800/60',
    DEBUG: 'bg-slate-900 text-slate-400 border border-slate-700',
  };

  const badgeStyle = styles[sev] || 'bg-slate-800 text-slate-300 border border-slate-700';
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span className={`inline-flex items-center rounded-md font-mono uppercase tracking-wider ${sizeClasses} ${badgeStyle}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-80" />
      {sev}
    </span>
  );
};
