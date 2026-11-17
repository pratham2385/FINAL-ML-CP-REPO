import React from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '../../utils/cn';

export function EmptyState({
  icon: Icon = Inbox,
  title = 'No records found',
  description = 'No analysis logs match your current filter parameters or the audit database is currently empty.',
  action,
  className
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center p-10 text-center rounded-xl border border-dashed border-white/[0.08] bg-[#14171b]/50', className)}>
      <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-[#181c23] border border-white/[0.08] text-slate-400 mb-3">
        <Icon className="w-5 h-5 text-slate-300" />
      </div>
      <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      <p className="mt-1 text-xs text-slate-400 max-w-sm leading-relaxed">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
