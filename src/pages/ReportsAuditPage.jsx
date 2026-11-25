import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileCheck2, 
  Briefcase, 
  ScrollText, 
  Settings, 
  Activity,
  CheckCircle2
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

import { InvestigationsPage } from './InvestigationsPage';
import { AuditPage } from './AuditPage';
import { SettingsPage } from './SettingsPage';

export const ReportsAuditPage = () => {
  const { subTabs, setSubTab, investigationsList, auditLogs } = useInvestigation();
  const currentSubTab = subTabs['reports-audit'] || 'cases';

  const tabs = [
    { 
      id: 'cases', 
      label: 'Investigation History', 
      icon: Briefcase,
      badge: `${investigationsList?.length || 0} Cases`
    },
    { 
      id: 'audit', 
      label: 'Audit Trail & Metrics', 
      icon: FileCheck2,
      badge: `${auditLogs?.length || 0} Records`
    },
    { 
      id: 'settings', 
      label: 'System Settings', 
      icon: Settings,
      badge: 'Config'
    }
  ];

  return (
    <div className="space-y-6 pb-12">
      
      {/* Top Hub Navigation Bar */}
      <div className="p-2 sm:p-2.5 rounded-2xl bg-white dark:bg-cerberus-card/90 border border-slate-200 dark:border-cerberus-border shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 px-2">
          <div className="p-2 rounded-xl bg-emerald-500/10 dark:bg-cerberus-green/15 text-emerald-600 dark:text-cerberus-green border border-emerald-500/20 dark:border-cerberus-green/30">
            <FileCheck2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-display font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white">
              Reports & Audit Center
            </h2>
            <p className="text-[10px] text-slate-500 dark:text-cerberus-muted font-sans">
              Case Dossiers • Tamper Audit Trail • Benchmark Evaluation
            </p>
          </div>
        </div>

        {/* Sub-tabs with smooth indicator */}
        <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-cerberus-bg-secondary p-1 rounded-xl border border-slate-200 dark:border-cerberus-border/70 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentSubTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSubTab('reports-audit', tab.id)}
                className={`relative flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono transition-colors whitespace-nowrap ${
                  isActive
                    ? 'text-emerald-700 dark:text-cerberus-green font-bold'
                    : 'text-slate-600 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="reportsAuditSubPill"
                    className="absolute inset-0 rounded-lg bg-white dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-green/40 shadow-sm"
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon className={`w-3.5 h-3.5 relative z-10 ${isActive ? 'text-emerald-600 dark:text-cerberus-green' : 'text-slate-400 dark:text-cerberus-muted'}`} />
                <span className="relative z-10">{tab.label}</span>
                <span className={`relative z-10 text-[9px] px-1.5 py-0.2 rounded font-mono ${
                  isActive 
                    ? 'bg-emerald-50 dark:bg-cerberus-green/20 text-emerald-800 dark:text-cerberus-green' 
                    : 'bg-slate-200/70 dark:bg-cerberus-bg text-slate-500 dark:text-cerberus-muted'
                }`}>
                  {tab.badge}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Sub-view Content with Animated Transitions */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentSubTab}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.2 }}
        >
          {currentSubTab === 'cases' && <InvestigationsPage />}
          {currentSubTab === 'audit' && <AuditPage />}
          {currentSubTab === 'settings' && <SettingsPage />}
        </motion.div>
      </AnimatePresence>

    </div>
  );
};

export default ReportsAuditPage;
