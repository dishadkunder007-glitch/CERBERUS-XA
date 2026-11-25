import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  GitFork, 
  ShieldCheck, 
  AlertTriangle, 
  ShieldAlert,
  FileWarning,
  CheckCircle2
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

import { ConflictPage } from './ConflictPage';
import { ReliabilityPage } from './ReliabilityPage';
import { AdversarialPage } from './AdversarialPage';

export const ConflictTrustPage = () => {
  const { subTabs, setSubTab, conflicts, adversarialAlerts, reliabilityRecords } = useInvestigation();
  const currentSubTab = subTabs['conflict-trust'] || 'conflicts';

  const tabs = [
    { 
      id: 'conflicts', 
      label: 'Contradiction Lab', 
      icon: GitFork,
      badge: `${conflicts?.length || 0} Clashes`,
      badgeColor: 'bg-rose-100 dark:bg-cerberus-red/20 text-rose-700 dark:text-cerberus-red'
    },
    { 
      id: 'reliability', 
      label: 'Source Reliability', 
      icon: ShieldCheck,
      badge: `${reliabilityRecords?.length || 0} Audited`,
      badgeColor: 'bg-emerald-100 dark:bg-cerberus-green/20 text-emerald-700 dark:text-cerberus-green'
    },
    { 
      id: 'adversarial', 
      label: 'Adversarial Scanner', 
      icon: AlertTriangle,
      badge: `${adversarialAlerts?.length || 0} Red Flags`,
      badgeColor: 'bg-amber-100 dark:bg-cerberus-amber/20 text-amber-700 dark:text-cerberus-amber'
    }
  ];

  return (
    <div className="space-y-6 pb-12">
      
      {/* Top Hub Navigation Bar */}
      <div className="p-2 sm:p-2.5 rounded-2xl bg-white dark:bg-cerberus-card/90 border border-slate-200 dark:border-cerberus-border shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 px-2">
          <div className="p-2 rounded-xl bg-rose-500/10 dark:bg-cerberus-red/15 text-rose-600 dark:text-cerberus-red border border-rose-500/20 dark:border-cerberus-red/30">
            <GitFork className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-display font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white">
              Conflict & Trust Analysis
            </h2>
            <p className="text-[10px] text-slate-500 dark:text-cerberus-muted font-sans">
              Contradiction Discovery • Source Reliability • Adversarial Content
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
                onClick={() => setSubTab('conflict-trust', tab.id)}
                className={`relative flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono transition-colors whitespace-nowrap ${
                  isActive
                    ? 'text-rose-700 dark:text-cerberus-red font-bold'
                    : 'text-slate-600 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="conflictTrustSubPill"
                    className="absolute inset-0 rounded-lg bg-white dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-red/40 shadow-sm"
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon className={`w-3.5 h-3.5 relative z-10 ${isActive ? 'text-rose-600 dark:text-cerberus-red' : 'text-slate-400 dark:text-cerberus-muted'}`} />
                <span className="relative z-10">{tab.label}</span>
                <span className={`relative z-10 text-[9px] px-1.5 py-0.2 rounded font-mono font-bold ${
                  isActive 
                    ? tab.badgeColor
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
          {currentSubTab === 'conflicts' && <ConflictPage />}
          {currentSubTab === 'reliability' && <ReliabilityPage />}
          {currentSubTab === 'adversarial' && <AdversarialPage />}
        </motion.div>
      </AnimatePresence>

    </div>
  );
};

export default ConflictTrustPage;
