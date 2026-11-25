import React from 'react';
import { 
  ShieldCheck, 
  AlertCircle, 
  FileCheck2, 
  HelpCircle,
  Info
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';
import { ReliabilityCard } from '../components/ReliabilityCard';

export const ReliabilityPage = () => {
  const { reliabilityRecords } = useInvestigation();

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-600 dark:text-cerberus-green">
            PROVENANCE & TRUST INTELLIGENCE
          </span>
          <span className="px-1.5 py-0.2 rounded bg-emerald-50 dark:bg-cerberus-blue/15 text-emerald-700 dark:text-cerberus-cyan border border-emerald-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
            MEMBER 4 VERIFIER
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
          Source Reliability Analysis
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
          Evaluates source provenance, cryptographic integrity, internal consistency, and independent cross-corroboration. A reliability assessment is not proof that a source is true.
        </p>
      </div>

      {/* Trust Notice Box */}
      <div className="p-4 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border flex items-start gap-3 text-xs font-mono shadow-sm">
        <Info className="w-5 h-5 text-emerald-600 dark:text-cerberus-cyan shrink-0 mt-0.5" />
        <div>
          <span className="text-slate-900 dark:text-white font-bold uppercase">Truthful Verification Principle:</span>
          <p className="text-slate-600 dark:text-cerberus-muted font-sans mt-0.5">
            Numerical reliability scores are strictly computed from backend provenance checks and cryptographically signed feeds. The system never fabricates scores without verifiable grounding.
          </p>
        </div>
      </div>

      {/* Reliability Cards List */}
      <div className="grid grid-cols-1 gap-5">
        {reliabilityRecords.map((rec) => (
          <ReliabilityCard key={rec.id} record={rec} />
        ))}
      </div>

    </div>
  );
};

export default ReliabilityPage;
