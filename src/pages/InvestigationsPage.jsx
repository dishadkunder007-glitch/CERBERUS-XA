import React from 'react';
import { 
  Briefcase, 
  Search, 
  Filter, 
  ArrowRight, 
  ShieldAlert, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  AlertTriangle,
  Plus
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const InvestigationsPage = () => {
  const { investigationsList, setActiveTab } = useInvestigation();

  return (
    <div className="space-y-6 pb-12">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-cerberus-cyan">
              CASE MANAGEMENT DOSSIERS
            </span>
            <span className="px-1.5 py-0.2 rounded bg-cerberus-blue/15 text-cerberus-cyan border border-cerberus-cyan/30 text-[10px] font-mono">
              OFFLINE INTELLIGENCE
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white font-mono">
            Active Investigations
          </h1>
          <p className="text-xs sm:text-sm text-cerberus-muted mt-1 max-w-2xl font-sans">
            Forensic dossiers evaluating cross-modal contradictions, suspicious provenance, and verifiable conclusions.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('upload')}
          className="px-4 py-2.5 rounded-xl bg-cerberus-blue hover:bg-blue-600 text-white text-xs font-mono font-bold shadow-glow-blue transition-all flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Investigation</span>
        </button>
      </div>

      {/* Case List Grid */}
      <div className="grid grid-cols-1 gap-4">
        {investigationsList.map((inv) => (
          <div
            key={inv.id}
            className="p-6 rounded-2xl bg-white dark:bg-cerberus-card/90 border border-slate-200 dark:border-cerberus-border hover:border-slate-300 dark:hover:border-cerberus-border-light shadow-sm dark:shadow-panel transition-all space-y-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-cerberus-border pb-3">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs px-2.5 py-1 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 font-bold">
                  {inv.id}
                </span>
                <div>
                  <h3 className="font-mono font-bold text-base text-slate-900 dark:text-white">
                    {inv.title}
                  </h3>
                  <span className="text-[11px] text-slate-500 dark:text-cerberus-muted font-mono">{inv.category}</span>
                </div>
              </div>

              <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold border uppercase ${
                inv.status === 'CONFLICT_DETECTED'
                  ? 'bg-rose-50 dark:bg-cerberus-red/15 text-rose-700 dark:text-cerberus-red border-rose-200 dark:border-cerberus-red/30'
                  : inv.status === 'SUPPORTED'
                  ? 'bg-emerald-50 dark:bg-cerberus-green/15 text-emerald-700 dark:text-cerberus-green border-emerald-200 dark:border-cerberus-green/30'
                  : 'bg-amber-50 dark:bg-cerberus-amber/15 text-amber-700 dark:text-cerberus-amber border-amber-200 dark:border-cerberus-amber/30'
              }`}>
                {inv.status.replace('_', ' ')}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">TARGET ENTITY</span>
                <span className="text-slate-900 dark:text-white font-semibold truncate block mt-0.5">{inv.leadEntity}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">EVIDENCE SOURCES</span>
                <span className="text-blue-600 dark:text-cerberus-cyan font-bold block mt-0.5">{inv.evidenceCount} Files</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">ATOMIC CLAIMS</span>
                <span className="text-slate-900 dark:text-white font-bold block mt-0.5">{inv.claimsCount} Claims</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">DETERMINATION</span>
                <span className="text-amber-700 dark:text-cerberus-amber font-semibold block mt-0.5">{inv.verdict}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-cerberus-border text-xs font-mono text-slate-500 dark:text-cerberus-muted">
              <span>Last updated: {new Date(inv.lastUpdated).toLocaleString()}</span>
              <button
                onClick={() => setActiveTab('report')}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-cerberus-card dark:hover:bg-cerberus-border text-blue-600 dark:text-cerberus-cyan font-bold flex items-center gap-1.5 transition-colors"
              >
                Inspect Dossier <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};

export default InvestigationsPage;
