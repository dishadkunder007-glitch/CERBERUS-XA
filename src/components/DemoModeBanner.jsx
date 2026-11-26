import React from 'react';
import { AlertTriangle, ArrowRight, Sparkles } from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const DemoModeBanner = () => {
  const { isDemoMode, setIsDemoMode, setActiveTab } = useInvestigation();

  if (!isDemoMode) return null;

  return (
    <div className="bg-amber-100/90 dark:bg-cerberus-card/95 border-b border-amber-300 dark:border-cerberus-amber/30 px-4 py-2 text-xs text-amber-900 dark:text-cerberus-amber backdrop-blur-md z-40 shrink-0 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-500 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-600"></span>
          </span>
          <span className="font-mono font-bold tracking-wide uppercase text-amber-900 dark:text-cerberus-amber">
            [JURY BENCHMARK DATASET ACTIVE]
          </span>
          <span className="text-slate-700 dark:text-slate-300 hidden sm:inline font-sans">
            Pre-loaded case: <strong className="text-slate-900 dark:text-white font-mono">Operation Boreas (MV Polaris Dual-Manifest)</strong>
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('conflicts')}
            className="flex items-center gap-1 font-semibold text-blue-700 dark:text-cerberus-cyan hover:underline underline-offset-2 font-mono"
          >
            Conflict Lab <ArrowRight className="w-3 h-3" />
          </button>
          <span className="text-amber-300 dark:text-cerberus-border">|</span>
          <button
            onClick={() => setIsDemoMode(false)}
            className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-200/80 hover:bg-amber-300 dark:bg-cerberus-amber/15 dark:hover:bg-cerberus-amber/25 text-amber-900 dark:text-cerberus-amber border border-amber-400 dark:border-cerberus-amber/30 font-bold"
          >
            Switch to Live Ingest
          </button>
        </div>
      </div>
    </div>
  );
};

export default DemoModeBanner;
