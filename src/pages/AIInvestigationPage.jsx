import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BrainCircuit, 
  MessageSquareCode, 
  Scale, 
  Sparkles,
  HelpCircle,
  FileSearch
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

import { ReportPage } from './ReportPage';
import { ReasoningPage } from './ReasoningPage';

export const AIInvestigationPage = () => {
  const { subTabs, setSubTab } = useInvestigation();
  const currentSubTab = subTabs['ai-investigation'] || 'answer-studio';

  const tabs = [
    { 
      id: 'answer-studio', 
      label: 'Answer Studio & Inquiry', 
      icon: MessageSquareCode,
      badge: 'Traceable Answers'
    },
    { 
      id: 'reasoning', 
      label: 'Neural Reasoning Engine', 
      icon: BrainCircuit,
      badge: '7-Step Timeline'
    }
  ];

  return (
    <div className="space-y-6 pb-12">
      
      {/* Top Hub Navigation Bar */}
      <div className="p-2 sm:p-2.5 rounded-2xl bg-white dark:bg-cerberus-card/90 border border-slate-200 dark:border-cerberus-border shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 px-2">
          <div className="p-2 rounded-xl bg-blue-500/10 dark:bg-cerberus-blue/15 text-blue-600 dark:text-cerberus-cyan border border-blue-500/20 dark:border-cerberus-cyan/30">
            <BrainCircuit className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-display font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white">
              AI Investigation
            </h2>
            <p className="text-[10px] text-slate-500 dark:text-cerberus-muted font-sans">
              Hypothesis Inquiry • Conflict-Aware Reasoning • Traceable Citations
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
                onClick={() => setSubTab('ai-investigation', tab.id)}
                className={`relative flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono transition-colors whitespace-nowrap ${
                  isActive
                    ? 'text-blue-600 dark:text-cerberus-cyan font-bold'
                    : 'text-slate-600 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="aiInvestigationSubPill"
                    className="absolute inset-0 rounded-lg bg-white dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-cyan/40 shadow-sm"
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon className={`w-3.5 h-3.5 relative z-10 ${isActive ? 'text-blue-600 dark:text-cerberus-cyan' : 'text-slate-400 dark:text-cerberus-muted'}`} />
                <span className="relative z-10">{tab.label}</span>
                <span className={`relative z-10 text-[9px] px-1.5 py-0.2 rounded font-mono ${
                  isActive 
                    ? 'bg-blue-50 dark:bg-cerberus-blue/20 text-blue-700 dark:text-cerberus-cyan' 
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
          {currentSubTab === 'answer-studio' && <ReportPage />}
          {currentSubTab === 'reasoning' && <ReasoningPage />}
        </motion.div>
      </AnimatePresence>

    </div>
  );
};

export default AIInvestigationPage;
