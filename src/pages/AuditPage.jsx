import React from 'react';
import { 
  FileCheck2, 
  Activity, 
  Database, 
  ShieldCheck, 
  Users, 
  GitFork, 
  CheckCircle2, 
  Clock,
  BarChart3
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const AuditPage = () => {
  const { auditLogs, evaluationMetrics } = useInvestigation();

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan">
            SYSTEM AUDIT & EVALUATION MATRIX
          </span>
          <span className="px-1.5 py-0.2 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
            INTELLIGENCE AUDIT LOG
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
          Audit Trail & Benchmark Evaluation
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
          Immutable history of evidence ingestions, human verification actions, contradiction alerts, and quantitative benchmark evaluation metrics.
        </p>
      </div>

      {/* System Benchmark Evaluation Metrics */}
      {evaluationMetrics && (
        <div className="space-y-3">
          <h3 className="font-mono font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
            Evaluation Benchmark Performance Metrics
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs font-mono">
            <div className="p-3.5 rounded-xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase block">Entity Match Accuracy</span>
              <span className="text-lg font-bold text-emerald-600 dark:text-cerberus-green mt-1 block">{evaluationMetrics.entityResolutionAccuracy}%</span>
            </div>
            <div className="p-3.5 rounded-xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase block">Conflict Precision</span>
              <span className="text-lg font-bold text-blue-600 dark:text-cerberus-cyan mt-1 block">{evaluationMetrics.conflictDetectionPrecision}%</span>
            </div>
            <div className="p-3.5 rounded-xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase block">Conflict Recall</span>
              <span className="text-lg font-bold text-indigo-600 dark:text-cerberus-blue mt-1 block">{evaluationMetrics.conflictDetectionRecall}%</span>
            </div>
            <div className="p-3.5 rounded-xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase block">Extraction Quality</span>
              <span className="text-lg font-bold text-blue-600 dark:text-cerberus-cyan mt-1 block">{evaluationMetrics.extractionQualityScore}%</span>
            </div>
            <div className="p-3.5 rounded-xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase block">Citation Correctness</span>
              <span className="text-lg font-bold text-emerald-600 dark:text-cerberus-green mt-1 block">{evaluationMetrics.citationCorrectness}%</span>
            </div>
            <div className="p-3.5 rounded-xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase block">Adversarial Scanner</span>
              <span className="text-lg font-bold text-amber-600 dark:text-cerberus-amber mt-1 block">{evaluationMetrics.adversarialDetectionScore}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Audit Action Log */}
      <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3">
          <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
            Immutable Audit Trail ({auditLogs.length} Events)
          </h3>
          <span className="text-[10px] font-mono text-slate-500 dark:text-cerberus-muted">
            Cryptographically logged operations
          </span>
        </div>

        <div className="divide-y divide-slate-100 dark:divide-cerberus-border/70">
          {auditLogs.map((log) => (
            <div key={log.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-blue-600 dark:text-cerberus-cyan font-bold">{log.id}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-cerberus-bg-secondary text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-cerberus-border font-semibold">
                    {log.action}
                  </span>
                  <span className="text-slate-500 dark:text-cerberus-muted text-[10px]">{log.user}</span>
                </div>
                <p className="text-slate-700 dark:text-slate-300 font-sans text-xs">
                  {log.details}
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted font-mono">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-cerberus-green/10 text-emerald-700 dark:text-cerberus-green border border-emerald-200 dark:border-cerberus-green/30 text-[10px] font-bold">
                  {log.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};

export default AuditPage;
