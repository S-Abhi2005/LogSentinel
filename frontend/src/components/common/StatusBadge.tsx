import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'incident' | 'health';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'incident' }) => {
  const s = (status || '').toUpperCase();

  const incidentStyles: Record<string, string> = {
    OPEN: 'bg-red-950/70 text-red-400 border border-red-800/80 animate-pulse',
    ACKNOWLEDGED: 'bg-amber-950/70 text-amber-300 border border-amber-800/60',
    INVESTIGATING: 'bg-blue-950/70 text-blue-300 border border-blue-800/60',
    RESOLVED: 'bg-emerald-950/70 text-emerald-400 border border-emerald-800/60',
  };

  const healthStyles: Record<string, string> = {
    HEALTHY: 'bg-emerald-950/70 text-emerald-400 border border-emerald-800/60',
    DEGRADED: 'bg-amber-950/70 text-amber-300 border border-amber-800/60',
    CRITICAL: 'bg-red-950/80 text-red-400 border border-red-800/80 animate-pulse',
    UNKNOWN: 'bg-slate-900 text-slate-400 border border-slate-700',
  };

  const styleMap = type === 'health' ? healthStyles : incidentStyles;
  const currentStyle = styleMap[s] || 'bg-slate-800 text-slate-300 border border-slate-700';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide ${currentStyle}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-90" />
      {s}
    </span>
  );
};
