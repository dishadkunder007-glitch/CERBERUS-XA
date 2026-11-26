import React from 'react';
import { 
  BrainCircuit, 
  Scale, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  FileWarning, 
  Clock, 
  Layers,
  ShieldCheck,
  ArrowRight
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const ReasoningPage = () => {
  const { investigationReport, setActiveTab } = useInvestigation();

  const reasoningSteps = [
    { step: 1, title: "User Question & Hypothesis Analysis", desc: "Parsed semantic entities: 'Nordic Freight Forwarding', 'MV Polaris', 'Valuation & Arrival Date'." },
    { step: 2, title: "Cross-Modal Evidence Retrieval", desc: "Retrieved 5 heterogeneous files (1 PDF, 2 Images, 1 XLSX, 1 CSV) and 75 normalized claims." },
    { step: 3, title: "Supporting Evidence Identification", desc: "Identified 3 mutually corroborating sources confirming berthing on July 14 and valuation ~$4.95M-$4.98M." },
    { step: 4, title: "Contradictory Evidence Identification", desc: "Detected 3 severe contradictions in official PDF C88 (Valuation $1.42M, Arrival July 19, Mass 420T)." },
    { step: 5, title: "Source Reliability Evaluation", desc: "Audited cryptographic provenance: Port authority API (98%) vs self-reported customs filing (31%)." },
    { step: 6, title: "Evidence Sufficiency Assessment", desc: "Evidence threshold reached (94.2% confidence). Discrepancy is systemic, not accidental." },
    { step: 7, title: "Final Reasoning Result", desc: "Classification: CONFLICTED & POTENTIALLY MANIPULATED EVIDENCE. Backdating and tariff evasion confirmed." }
  ];

  return (
    <div className="space-y-8 pb-16">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan">
              NEURAL CONFLICT-AWARE VERIFICATION
            </span>
            <span className="px-1.5 py-0.2 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
              MEMBER 4 REASONING ENGINE
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
            AI Reasoning Engine Workspace
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
            Step-by-step investigation timeline demonstrating how contradictory claims are challenged, corroborated, and resolved into grounded decisions.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('report')}
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 text-white text-xs font-mono font-bold shadow-glow-blue transition-all flex items-center gap-2"
        >
          <span>Open Answer Studio</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* 4 Decision States Reference */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-cerberus-green/10 border border-emerald-200 dark:border-cerberus-green/30 space-y-1">
          <div className="flex items-center gap-2 text-emerald-700 dark:text-cerberus-green font-bold">
            <CheckCircle2 className="w-4 h-4" />
            <span>SUPPORTED</span>
          </div>
          <p className="text-slate-600 dark:text-slate-300 font-sans text-[11px]">
            Evidence sufficiently supports a consistent, corroborated conclusion.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-rose-50 dark:bg-cerberus-red/10 border border-rose-200 dark:border-cerberus-red/30 space-y-1">
          <div className="flex items-center gap-2 text-rose-700 dark:text-cerberus-red font-bold">
            <XCircle className="w-4 h-4" />
            <span>CONFLICTED</span>
          </div>
          <p className="text-slate-600 dark:text-slate-300 font-sans text-[11px]">
            Relevant evidence contains unresolved cross-modal contradictions.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-cerberus-amber/10 border border-amber-200 dark:border-cerberus-amber/30 space-y-1">
          <div className="flex items-center gap-2 text-amber-700 dark:text-cerberus-amber font-bold">
            <HelpCircle className="w-4 h-4" />
            <span>INSUFFICIENT</span>
          </div>
          <p className="text-slate-600 dark:text-slate-300 font-sans text-[11px]">
            Available evidence does not establish a reliable conclusion.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-purple-50 dark:bg-purple-500/10 border border-purple-200 dark:border-purple-500/30 space-y-1">
          <div className="flex items-center gap-2 text-purple-700 dark:text-purple-400 font-bold">
            <FileWarning className="w-4 h-4" />
            <span>POTENTIALLY MANIPULATED</span>
          </div>
          <p className="text-slate-600 dark:text-slate-300 font-sans text-[11px]">
            Indicators of deliberate tampering, backdating, or adversarial fabrication.
          </p>
        </div>
      </div>

      {/* 7-Step Step-by-Step Investigation Timeline */}
      <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-5">
        <div className="border-b border-slate-200 dark:border-cerberus-border pb-3">
          <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
            Investigation Timeline & Conflict Resolution Process
          </h3>
          <p className="text-xs text-slate-500 dark:text-cerberus-muted font-mono mt-0.5">
            Traceable execution path of the Member 4 neural reasoning verifier
          </p>
        </div>

        <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-cerberus-border">
          {reasoningSteps.map((step) => (
            <div key={step.step} className="relative">
              <div className="absolute -left-6 top-0 w-4 h-4 rounded-full bg-white dark:bg-cerberus-card border-2 border-blue-600 dark:border-cerberus-cyan flex items-center justify-center">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600 dark:bg-cerberus-cyan" />
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border text-xs font-mono">
                <div className="flex items-center justify-between text-[10px] text-blue-700 dark:text-cerberus-cyan font-bold mb-1">
                  <span>STEP {step.step}</span>
                  <span>COMPLETED</span>
                </div>
                <h4 className="font-bold text-sm text-slate-900 dark:text-white mb-1">
                  {step.title}
                </h4>
                <p className="text-slate-600 dark:text-cerberus-muted font-sans text-xs">
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Active Determination Summary */}
      {investigationReport && (
        <div className="p-6 rounded-2xl bg-cerberus-red/10 border border-cerberus-red/40 shadow-panel space-y-3">
          <span className="text-[10px] font-mono uppercase text-cerberus-red font-bold block">
            Current Case Determination
          </span>
          <h2 className="text-xl font-bold font-mono text-white">
            Verdict: {investigationReport.finalVerdict} (Classification: {investigationReport.verdictClassification})
          </h2>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            {investigationReport.summaryAnswer}
          </p>
        </div>
      )}

    </div>
  );
};

export default ReasoningPage;
