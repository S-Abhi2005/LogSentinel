import React from 'react';

interface LoadingSkeletonProps {
  rows?: number;
  height?: string;
  className?: string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  rows = 4,
  height = 'h-10',
  className = '',
}) => {
  return (
    <div className={`space-y-3 animate-pulse ${className}`}>
      {Array.from({ length: rows }).map((_, idx) => (
        <div
          key={idx}
          className={`w-full bg-slate-200/80 dark:bg-slate-800/60 rounded-lg ${height} border border-slate-300/60 dark:border-slate-700/40`}
        />
      ))}
    </div>
  );
};
