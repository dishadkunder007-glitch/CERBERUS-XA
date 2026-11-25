import React, { useState } from 'react';
import { 
  Settings, 
  Server, 
  Code2, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  ShieldCheck,
  RotateCcw
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const SettingsPage = () => {
  const { 
    backendStatus, 
    verifyBackend, 
    isDemoMode, 
    setIsDemoMode,
    handleClearSession 
  } = useInvestigation();

  const integrationContracts = [
    {
      member: 'Member 2',
      specialty: 'Multimodal Data Ingestion',
      endpoints: [
        { method: 'POST', path: '/process-file', purpose: 'Single document / image / spreadsheet parsing & claims extraction' },
        { method: 'POST', path: '/process-batch', purpose: 'Multi-file parallel evidence ingestion' },
        { method: 'GET', path: '/claims', purpose: 'Retrieve all normalized claims with provenance coordinates' }
      ]
    },
    {
      member: 'Member 3',
      specialty: 'Knowledge Graph & Conflict Detection',
      endpoints: [
        { method: 'GET', path: '/conflicts', purpose: 'Retrieve detected contradictions across modalities' },
        { method: 'GET', path: '/graph', purpose: 'Retrieve topological nodes and cross-modal edges' },
        { method: 'GET', path: '/entity-resolution', purpose: 'Retrieve entity resolution and alias matches' }
      ]
    },
    {
      member: 'Member 4',
      specialty: 'AI Reasoning & Evidence Verification',
      endpoints: [
        { method: 'POST', path: '/investigate', purpose: 'Submit query and generate cross-modal reasoning' },
        { method: 'GET', path: '/investigation-report/{id}', purpose: 'Retrieve complete forensic verdict dossier' },
        { method: 'GET', path: '/reliability', purpose: 'Retrieve source reliability scores' },
        { method: 'GET', path: '/adversarial', purpose: 'Retrieve detected red flags and tamper indicators' },
        { method: 'GET', path: '/audit', purpose: 'Retrieve system evaluation & audit telemetry' }
      ]
    }
  ];

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan">
            SYSTEM & ARCHITECTURE
          </span>
          <span className="px-1.5 py-0.2 rounded bg-slate-100 dark:bg-cerberus-card text-slate-600 dark:text-cerberus-muted border border-slate-200 dark:border-cerberus-border text-[10px] font-mono">
            CONFIGURATION
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
          API Settings & Integration Contracts
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
          FastAPI backend connectivity, environment configuration, and cross-team integration contracts for Members 2, 3, and 4.
        </p>
      </div>

      {/* FastAPI Host Card */}
      <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl border ${
              backendStatus.online 
                ? 'bg-emerald-50 dark:bg-cerberus-green/10 text-emerald-700 dark:text-cerberus-green border-emerald-200 dark:border-cerberus-green/30' 
                : 'bg-rose-50 dark:bg-cerberus-red/10 text-rose-700 dark:text-cerberus-red border-rose-200 dark:border-cerberus-red/30'
            }`}>
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold font-mono text-slate-900 dark:text-white">
                FastAPI Host Connection
              </h3>
              <p className="text-xs text-slate-500 dark:text-cerberus-muted font-mono">
                {backendStatus.apiUrl}
              </p>
            </div>
          </div>

          <button
            onClick={() => verifyBackend()}
            className="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-cerberus-bg-secondary dark:hover:bg-cerberus-card text-blue-600 dark:text-cerberus-cyan border border-slate-200 dark:border-cerberus-cyan/30 text-xs font-mono flex items-center gap-2 transition-colors font-bold"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Ping /health
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
            <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">SERVER STATUS</span>
            <span className={`font-bold mt-0.5 block ${backendStatus.online ? 'text-emerald-600 dark:text-cerberus-green' : 'text-rose-600 dark:text-cerberus-red'}`}>
              {backendStatus.online ? '● ONLINE & RESPONSIVE' : '○ DISCONNECTED / UNREACHABLE'}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
            <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">CONFIGURED URL</span>
            <span className="text-slate-900 dark:text-white mt-0.5 block truncate">
              VITE_API_BASE_URL
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
            <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">DATASET MODE</span>
            <span className="text-amber-700 dark:text-cerberus-amber mt-0.5 block font-bold">
              {isDemoMode ? 'DEMO BENCHMARK DATASET' : 'LIVE BACKEND INGEST'}
            </span>
          </div>
        </div>
      </div>

      {/* Integration Contracts Documentation */}
      <div className="space-y-4">
        <h2 className="text-base font-bold font-mono text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
          <Code2 className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
          Cross-Team REST Integration Contracts
        </h2>

        <div className="space-y-4">
          {integrationContracts.map((team, idx) => (
            <div key={idx} className="p-5 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel">
              <div className="flex items-center justify-between mb-3 border-b border-slate-200 dark:border-cerberus-border pb-2.5">
                <h3 className="text-sm font-bold font-mono text-blue-600 dark:text-cerberus-cyan">
                  {team.member}: {team.specialty}
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-cerberus-bg-secondary text-slate-600 dark:text-cerberus-muted border border-slate-200 dark:border-cerberus-border">
                  STANDARD REST
                </span>
              </div>

              <div className="space-y-2">
                {team.endpoints.map((ep, eIdx) => (
                  <div key={eIdx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border text-xs font-mono">
                    <div className="flex items-center gap-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        ep.method === 'POST' ? 'bg-blue-50 dark:bg-cerberus-blue/20 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30' : 'bg-emerald-50 dark:bg-cerberus-green/20 text-emerald-700 dark:text-cerberus-green border border-emerald-200 dark:border-cerberus-green/30'
                      }`}>
                        {ep.method}
                      </span>
                      <span className="text-slate-900 dark:text-white font-bold">{ep.path}</span>
                    </div>
                    <span className="text-slate-600 dark:text-cerberus-muted text-[11px] font-sans">
                      {ep.purpose}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Session Memory Reset */}
      <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-xs font-bold font-mono uppercase text-slate-900 dark:text-white">
            Reset Active Session State
          </h3>
          <p className="text-xs text-slate-500 dark:text-cerberus-muted mt-0.5 font-sans">
            Clear in-memory evidence caches, active queries, and temporary live responses.
          </p>
        </div>
        <button
          onClick={handleClearSession}
          className="px-4 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 dark:bg-cerberus-red/20 dark:hover:bg-cerberus-red/30 text-rose-700 dark:text-cerberus-red border border-rose-200 dark:border-cerberus-red/40 text-xs font-mono font-bold transition-colors"
        >
          Clear Session Cache
        </button>
      </div>

    </div>
  );
};

export default SettingsPage;
