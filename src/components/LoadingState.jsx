import React from 'react';
import { Loader2, Radio, ShieldCheck } from 'lucide-react';

export const LoadingState = ({ message = 'Processing multimodal evidence...', submessage = 'Synthesizing cross-modal entities & running conflict detection algorithms' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl bg-dark-900/60 border border-dark-700/60 my-6">
      <div className="relative flex items-center justify-center w-16 h-16 rounded-full bg-dark-800 border border-accent-blue/30 mb-4 shadow-glow-blue">
        <Loader2 className="w-8 h-8 text-accent-blue animate-spin" />
        <Radio className="w-4 h-4 text-accent-cyan absolute animate-ping opacity-75" />
      </div>
      <h3 className="text-base font-semibold text-slate-100 font-mono tracking-wide">
        {message}
      </h3>
      <p className="text-xs text-slate-400 max-w-md mt-1 font-sans">
        {submessage}
      </p>
      <div className="mt-4 flex items-center gap-2 text-[11px] font-mono text-slate-500">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
        <span>MEMBER 2 (Ingest) &rarr; MEMBER 3 (Graph) &rarr; MEMBER 4 (Reasoning)</span>
      </div>
    </div>
  );
};

export const EmptyState = ({ title = 'No Evidence Ingested', message = 'Upload files (PDF, PNG, JPG, XLSX, CSV) or toggle Demo Mode to inspect benchmark cases.', actionText, onAction }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl bg-dark-900/40 border border-dashed border-dark-700 my-6">
      <ShieldCheck className="w-12 h-12 text-slate-600 mb-3" />
      <h3 className="text-base font-semibold text-slate-300 font-mono">
        {title}
      </h3>
      <p className="text-xs text-slate-500 max-w-sm mt-1 mb-5">
        {message}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-glow-blue transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
