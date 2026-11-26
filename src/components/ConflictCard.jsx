import React, { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { 
  GitCommit, 
  AlertOctagon, 
  ArrowRight, 
  FileText, 
  Table as TableIcon, 
  Image as ImageIcon,
  ShieldAlert,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export const ConflictCard = ({ conflict }) => {
  const [expanded, setExpanded] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  const {
    id,
    entity,
    category,
    severity = 'HIGH',
    description,
    evidenceReferences = [],
    delta,
    verdictImplication
  } = conflict;

  const severityColor = {
    CRITICAL: 'text-rose-600 dark:text-cerberus-red bg-rose-50 dark:bg-cerberus-red/10 border-rose-300 dark:border-cerberus-red/40',
    HIGH: 'text-amber-600 dark:text-cerberus-amber bg-amber-50 dark:bg-cerberus-amber/10 border-amber-300 dark:border-cerberus-amber/40',
    MEDIUM: 'text-blue-600 dark:text-cerberus-cyan bg-blue-50 dark:bg-cerberus-cyan/10 border-blue-300 dark:border-cerberus-cyan/40',
    LOW: 'text-slate-600 dark:text-cerberus-muted bg-slate-50 dark:bg-cerberus-card border-slate-200 dark:border-cerberus-border',
  }[severity] || 'text-rose-600 dark:text-cerberus-red bg-rose-50 dark:bg-cerberus-red/10 border-rose-300 dark:border-cerberus-red/40';

  return (
    <motion.div 
      whileHover={shouldReduceMotion ? {} : { y: -2, transition: { duration: 0.2 } }}
      className="rounded-2xl border border-rose-300/80 dark:border-cerberus-red/40 bg-white dark:bg-cerberus-card/90 p-6 shadow-sm dark:shadow-panel hover:border-rose-500 dark:hover:border-cerberus-red/70 transition-all space-y-4"
    >
      
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-cerberus-border pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-rose-50 dark:bg-cerberus-red/15 text-rose-600 dark:text-cerberus-red border border-rose-200 dark:border-cerberus-red/30">
            <AlertOctagon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-rose-600 dark:text-cerberus-red font-bold">{id}</span>
              <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white font-display">
                {entity}
              </h3>
            </div>
            <span className="text-xs text-slate-500 dark:text-cerberus-muted font-mono">{category}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold tracking-wider uppercase border ${severityColor}`}>
            {severity} SEVERITY
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-cerberus-card text-slate-500 dark:text-cerberus-muted transition-colors"
            title={expanded ? "Collapse Details" : "Expand Details"}
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
        {description}
      </p>

      {/* Delta Callout */}
      {delta && (
        <div className="p-3 rounded-xl bg-rose-50 dark:bg-cerberus-red/10 border border-rose-200 dark:border-cerberus-red/30 flex items-center gap-2.5">
          <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-cerberus-red shrink-0" />
          <span className="text-xs font-mono font-bold text-rose-800 dark:text-rose-200">
            Discrepancy Delta: {delta}
          </span>
        </div>
      )}

      {/* Side-by-Side Contradictory Evidence Matrix */}
      <div className="space-y-2">
        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-cerberus-muted block">
          Cross-Modal Contradiction Nodes:
        </span>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {evidenceReferences.map((ref, idx) => (
            <motion.div
              key={idx}
              whileHover={shouldReduceMotion ? {} : { scale: 1.01 }}
              className={`p-3.5 rounded-xl border text-xs font-mono flex flex-col justify-between ${
                ref.type?.includes('CLAIM_A')
                  ? 'bg-rose-50/70 dark:bg-cerberus-red/10 border-rose-200 dark:border-cerberus-red/40 text-rose-900 dark:text-rose-200'
                  : ref.type?.includes('CLAIM_B')
                  ? 'bg-blue-50/70 dark:bg-cerberus-blue/15 border-blue-200 dark:border-cerberus-blue/40 text-blue-900 dark:text-blue-200'
                  : 'bg-emerald-50/70 dark:bg-cerberus-green/10 border-emerald-200 dark:border-cerberus-green/40 text-emerald-900 dark:text-emerald-200'
              }`}
            >
              <div>
                <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-cerberus-muted mb-1.5">
                  <span className="uppercase font-bold">{ref.modality}</span>
                  <span>{ref.location}</span>
                </div>
                <p className="font-bold text-slate-900 dark:text-white text-sm mt-1">
                  {ref.value}
                </p>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-200 dark:border-cerberus-border text-[10px] text-slate-600 dark:text-cerberus-muted truncate">
                File: {ref.source}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Forensic Verdict Implication (Expandable with animation) */}
      <AnimatePresence>
        {(expanded || verdictImplication) && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="pt-3 border-t border-slate-200 dark:border-cerberus-border flex items-start gap-2 text-xs text-slate-600 dark:text-cerberus-muted font-sans overflow-hidden"
          >
            <Info className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan shrink-0 mt-0.5" />
            <span><strong className="text-slate-900 dark:text-white font-mono">Forensic Deduction:</strong> {verdictImplication || "Evidence discrepancies indicate conflicting modal telemetry requiring jury verification."}</span>
          </motion.div>
        )}
      </AnimatePresence>

    </motion.div>
  );
};

export default ConflictCard;
