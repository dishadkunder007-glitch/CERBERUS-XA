import React from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  Radio, 
  Server, 
  GitFork, 
  Layers, 
  ChevronRight, 
  ChevronLeft,
  Bell,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const RightPanel = () => {
  const { 
    rightPanelOpen, 
    setRightPanelOpen, 
    backendStatus, 
    verifyBackend, 
    conflicts, 
    adversarialAlerts,
    evidenceFiles,
    setActiveTab
  } = useInvestigation();

  if (!rightPanelOpen) {
    return (
      <button
        onClick={() => setRightPanelOpen(true)}
        className="fixed bottom-6 right-6 z-40 p-3 rounded-full bg-white dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-cyan/40 text-blue-600 dark:text-cerberus-cyan shadow-xl hover:scale-105 transition-all"
        title="Open Intelligence Status Panel"
      >
        <Radio className="w-5 h-5 animate-pulse" />
      </button>
    );
  }

  return (
    <aside className="w-80 border-l border-slate-200 dark:border-cerberus-border bg-white dark:bg-cerberus-bg-secondary/95 backdrop-blur-md flex flex-col z-20 shrink-0 h-full overflow-hidden transition-colors">
      
      {/* Panel Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-cerberus-border h-16">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan animate-pulse" />
          <h3 className="font-mono font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-cerberus-text">
            Intelligence Status
          </h3>
        </div>
        <button
          onClick={() => setRightPanelOpen(false)}
          className="p-1 rounded text-slate-500 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-cerberus-card transition-colors"
          title="Minimize Panel"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Content Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 text-xs font-mono">
        
        {/* System & API Connectivity Status */}
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase tracking-wider">
              API CONNECTIVITY
            </span>
            <button
              onClick={() => verifyBackend()}
              className="text-blue-600 dark:text-cerberus-cyan hover:text-slate-900 dark:hover:text-white"
              title="Ping Backend"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${backendStatus.online ? 'bg-emerald-500 dark:bg-cerberus-green animate-pulse' : 'bg-rose-500 dark:bg-cerberus-red'}`} />
            <span className={`font-bold ${backendStatus.online ? 'text-emerald-700 dark:text-cerberus-green' : 'text-rose-700 dark:text-cerberus-red'}`}>
              {backendStatus.online ? 'API ONLINE (CONFIRMED)' : 'API DISCONNECTED'}
            </span>
          </div>
          <p className="text-[10px] text-slate-500 dark:text-cerberus-muted mt-1 truncate">
            {backendStatus.apiUrl}
          </p>
        </div>

        {/* Active Conflicts Radar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase tracking-wider flex items-center gap-1.5">
              <GitFork className="w-3.5 h-3.5 text-rose-600 dark:text-cerberus-red" />
              Active Contradictions ({conflicts.length})
            </span>
            <button
              onClick={() => setActiveTab('conflicts')}
              className="text-[10px] text-blue-600 dark:text-cerberus-cyan hover:underline"
            >
              View Lab
            </button>
          </div>

          {conflicts.slice(0, 3).map((c) => (
            <div
              key={c.id}
              onClick={() => setActiveTab('conflicts')}
              className="p-2.5 rounded-xl bg-slate-50 dark:bg-cerberus-card/80 border border-rose-200 dark:border-cerberus-red/30 hover:border-rose-400 dark:hover:border-cerberus-red/60 cursor-pointer transition-colors"
            >
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-rose-600 dark:text-cerberus-red font-bold">{c.id}</span>
                <span className="px-1.5 py-0.2 rounded bg-rose-100 dark:bg-cerberus-red/10 text-rose-700 dark:text-cerberus-red border border-rose-200 dark:border-cerberus-red/20 text-[9px]">
                  {c.severity}
                </span>
              </div>
              <p className="text-slate-800 dark:text-slate-200 text-xs font-sans mt-1 line-clamp-1 font-medium">
                {c.entity}
              </p>
            </div>
          ))}
        </div>

        {/* Suspicious Evidence Alerts */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-cerberus-amber" />
              Adversarial Alerts ({adversarialAlerts.length})
            </span>
            <button
              onClick={() => setActiveTab('adversarial')}
              className="text-[10px] text-blue-600 dark:text-cerberus-cyan hover:underline"
            >
              Scanner
            </button>
          </div>

          {adversarialAlerts.slice(0, 2).map((a) => (
            <div
              key={a.id}
              onClick={() => setActiveTab('adversarial')}
              className="p-2.5 rounded-xl bg-slate-50 dark:bg-cerberus-card/80 border border-amber-200 dark:border-cerberus-amber/30 hover:border-amber-400 dark:hover:border-cerberus-amber/60 cursor-pointer transition-colors"
            >
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-amber-700 dark:text-cerberus-amber font-bold">{a.anomalyType}</span>
              </div>
              <p className="text-slate-700 dark:text-slate-300 text-[11px] font-sans mt-1 line-clamp-2">
                {a.explanation}
              </p>
            </div>
          ))}
        </div>

        {/* Evidence Ingest Activity */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-cyan" />
              Vault Files ({evidenceFiles.length})
            </span>
            <button
              onClick={() => setActiveTab('evidence')}
              className="text-[10px] text-blue-600 dark:text-cerberus-cyan hover:underline"
            >
              Vault
            </button>
          </div>

          <div className="space-y-1.5">
            {evidenceFiles.slice(0, 4).map((f) => (
              <div key={f.id} className="p-2 rounded-lg bg-slate-50 dark:bg-cerberus-card/60 border border-slate-200 dark:border-cerberus-border flex items-center justify-between text-[11px]">
                <span className="truncate text-slate-800 dark:text-slate-300 max-w-[170px]" title={f.filename}>
                  {f.filename}
                </span>
                <span className="text-[9px] px-1 rounded bg-slate-200 dark:bg-cerberus-bg text-blue-600 dark:text-cerberus-cyan border border-slate-300 dark:border-cerberus-border font-bold">
                  {f.format}
                </span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </aside>
  );
};

export default RightPanel;
