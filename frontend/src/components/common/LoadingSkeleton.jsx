import React from 'react';
import { cn } from '../../utils/cn';

export function LoadingSkeleton({ className, rows = 3 }) {
  return (
    <div className={cn('animate-pulse space-y-2.5', className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-5 rounded bg-[#1c2027]"
          style={{ width: `${Math.max(40, 100 - i * 15)}%` }}
        />
      ))}
    </div>
  );
}

export function CardSkeleton({ className }) {
  return (
    <div className={cn('animate-pulse rounded-xl border border-white/[0.08] bg-[#14171b] p-5 space-y-3', className)}>
      <div className="h-3.5 w-1/3 rounded bg-[#1c2027]" />
      <div className="h-7 w-1/2 rounded bg-[#1f242d]" />
      <div className="h-3 w-2/3 rounded bg-[#181c23]" />
    </div>
  );
}
