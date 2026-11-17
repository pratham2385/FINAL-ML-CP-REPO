import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

export function ConfirmModal({
  isOpen,
  title = 'Confirm action',
  message = 'Are you sure you want to proceed? This action cannot be undone.',
  confirmText = 'Confirm delete',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  isDestructive = true,
  isLoading = false,
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="relative w-full max-w-md overflow-hidden rounded-xl border border-white/[0.08] bg-[#14171b] p-5 shadow-2xl">
        <button
          onClick={onCancel}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-start gap-3.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#cf222e]/10 border border-[#cf222e]/30 text-[#ff8182] shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-white">{title}</h3>
            <p className="mt-1.5 text-xs text-slate-300 leading-relaxed">{message}</p>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-end gap-2.5">
          <button
            type="button"
            disabled={isLoading}
            onClick={onCancel}
            className="px-3 py-1.5 text-xs font-medium rounded-md border border-white/[0.08] bg-[#181c23] text-slate-300 hover:bg-[#1f242d] hover:text-white transition-colors"
          >
            {cancelText}
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={onConfirm}
            className={`px-3 py-1.5 text-xs font-medium rounded-md text-white transition-colors ${
              isDestructive
                ? 'bg-[#cf222e] hover:bg-[#b62324]'
                : 'bg-[#1f6feb] hover:bg-[#388bfd]'
            }`}
          >
            {isLoading ? 'Processing...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
