import React from 'react';
import { 
  AlertTriangle, 
  ShieldAlert, 
  FileWarning, 
  Eye, 
  CheckCircle2, 
  Clock, 
  Lock,
  ExternalLink
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const AdversarialPage = () => {
  const { adversarialAlerts } = useInvestigation();

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-rose-600 dark:text-cerberus-red">
            RED FLAG & ADVERSARIAL CONTENT SCANNER
          </span>
          <span className="px-1.5 py-0.2 rounded bg-rose-50 dark:bg-cerberus-red/15 text-rose-600 dark:text-cerberus-red border border-rose-200 dark:border-cerberus-red/30 text-[10px] font-mono">
            SECURITY INTELLIGENCE
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
          Adversarial & Tamper Analysis
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
          Scans for suspicious metadata inconsistencies, backdated timestamps, resampled OCR typography, and embedded prompt injection attempts in uploaded evidence.
        </p>
      </div>

      {/* Untrusted Data Banner */}
      <div className="p-4 rounded-2xl bg-rose-50 dark:bg-cerberus-red/10 border border-rose-200 dark:border-cerberus-red/30 flex items-start gap-3 text-xs font-mono">
        <ShieldAlert className="w-5 h-5 text-rose-600 dark:text-cerberus-red shrink-0 mt-0.5" />
        <div>
          <span className="text-rose-700 dark:text-cerberus-red font-bold uppercase">Security Directive:</span>
          <p className="text-rose-800 dark:text-rose-200/80 font-sans mt-0.5">
            Uploaded document contents are treated strictly as untrusted forensic data, never as executable instructions to the AI reasoning engine.
          </p>
        </div>
      </div>

      {/* Red Flag Alerts List */}
      <div className="space-y-4">
        {adversarialAlerts.map((alert) => (
          <div
            key={alert.id}
            className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-rose-200 dark:border-cerberus-red/40 shadow-sm dark:shadow-panel space-y-4 hover:border-rose-400 dark:hover:border-cerberus-red/70 transition-all"
          >
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-cerberus-border pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-rose-50 dark:bg-cerberus-red/10 text-rose-600 dark:text-cerberus-red border border-rose-200 dark:border-cerberus-red/30">
                  <FileWarning className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-rose-600 dark:text-cerberus-red font-bold">{alert.id}</span>
                    <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                      {alert.anomalyType}
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500 dark:text-cerberus-muted">{alert.filename}</span>
                </div>
              </div>

              <span className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold border uppercase ${
                alert.riskClassification.includes('CRITICAL') ? 'bg-rose-50 dark:bg-cerberus-red/20 text-rose-700 dark:text-cerberus-red border-rose-200 dark:border-cerberus-red/50 shadow-sm dark:shadow-glow-red' :
                'bg-amber-50 dark:bg-cerberus-amber/20 text-amber-700 dark:text-cerberus-amber border-amber-200 dark:border-cerberus-amber/50'
              }`}>
                {alert.riskClassification}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">EVIDENCE LOCATION</span>
                <span className="text-slate-900 dark:text-white block mt-0.5">{alert.location}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">REVIEW STATUS</span>
                <span className="text-blue-600 dark:text-cerberus-cyan font-bold block mt-0.5">{alert.reviewStatus}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-cerberus-bg/90 border border-slate-200 dark:border-cerberus-border text-xs">
              <span className="text-[10px] font-mono text-rose-600 dark:text-cerberus-red uppercase font-bold block mb-1">
                Forensic Anomaly Explanation:
              </span>
              <p className="text-slate-700 dark:text-slate-300 font-sans leading-relaxed">
                {alert.explanation}
              </p>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};

export default AdversarialPage;
