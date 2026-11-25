import React from 'react';
import { ShieldCheck, AlertCircle, FileCheck, ExternalLink } from 'lucide-react';

export const ReliabilityCard = ({ record }) => {
  const {
    id,
    sourceName,
    origin,
    provenance,
    authStatus,
    consistencyScore,
    completeness,
    corroboration,
    score,
    assessment,
    reason
  } = record;

  const getStatusColor = (status = '') => {
    if (status.includes('AUTHENTIC')) return 'text-cerberus-green bg-cerberus-green/10 border-cerberus-green/30';
    if (status.includes('SUSPECT')) return 'text-cerberus-red bg-cerberus-red/10 border-cerberus-red/30';
    return 'text-cerberus-cyan bg-cerberus-cyan/10 border-cerberus-cyan/30';
  };

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-cerberus-border bg-white dark:bg-cerberus-card/90 p-5 shadow-sm dark:shadow-panel space-y-4 hover:border-slate-300 dark:hover:border-cerberus-border-light transition-all">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 dark:border-cerberus-border pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-blue/30 font-bold">
              {id}
            </span>
            <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-cerberus-text">
              {sourceName}
            </h3>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-cerberus-muted font-mono mt-0.5">
            Origin: <strong className="text-slate-700 dark:text-slate-300">{origin}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase text-slate-500 dark:text-cerberus-muted block">Trust Index</span>
            <span className={`text-base font-bold font-mono ${score >= 0.8 ? 'text-emerald-600 dark:text-cerberus-green' : score >= 0.5 ? 'text-amber-600 dark:text-cerberus-amber' : 'text-rose-600 dark:text-cerberus-red'}`}>
              {(score * 100).toFixed(0)}%
            </span>
          </div>
          <span className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold border uppercase ${getStatusColor(authStatus)}`}>
            {authStatus}
          </span>
        </div>
      </div>

      {/* Grid of Attributes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
          <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">PROVENANCE & INTEGRITY</span>
          <p className="text-slate-800 dark:text-slate-200 font-sans text-xs mt-1">{provenance}</p>
        </div>

        <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
          <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">CROSS-CORROBORATION</span>
          <p className="text-slate-800 dark:text-slate-200 font-sans text-xs mt-1">{corroboration}</p>
        </div>
      </div>

      {/* Rationale & Assessment */}
      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-cerberus-bg/80 border border-slate-200 dark:border-cerberus-border text-xs">
        <span className="text-[10px] font-mono text-blue-600 dark:text-cerberus-cyan uppercase font-bold block mb-1">
          Deduction & Reason For Assessment:
        </span>
        <p className="text-slate-700 dark:text-slate-300 font-sans leading-relaxed">
          {reason || assessment}
        </p>
      </div>
    </div>
  );
};

export default ReliabilityCard;
