import React, { useState } from 'react';
import { 
  BrainCircuit, 
  Send, 
  HelpCircle, 
  Sparkles, 
  AlertCircle, 
  RotateCcw,
  Scale,
  ShieldCheck,
  FileSearch,
  MessageSquareCode,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';
import { ReportViewer } from '../components/ReportViewer';
import { LoadingState } from '../components/LoadingState';

const INVESTIGATION_PRESETS = [
  "Did Nordic Freight Forwarding misrepresent shipment valuation, arrival dates, and cargo contents of Vessel MV Polaris to evade EU tariff duties?",
  "Which sources contain conflicting information regarding Vessel MV Polaris berthing arrival?",
  "Are there suspicious or manipulated records in Customs Form C88?",
  "Is the available evidence sufficient to establish whether cargo mass was under-reported?"
];

export const ReportPage = () => {
  const { 
    investigationReport, 
    handleRunInvestigation, 
    processingState, 
    investigationQuery, 
    setInvestigationQuery 
  } = useInvestigation();

  const [inputQuery, setInputQuery] = useState(investigationQuery);
  const [expandedCitation, setExpandedCitation] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputQuery.trim()) return;
    setInvestigationQuery(inputQuery);
    handleRunInvestigation(inputQuery);
  };

  const handleSelectPreset = (q) => {
    setInputQuery(q);
    setInvestigationQuery(q);
  };

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan">
            TRACEABLE EVIDENCE-BACKED AI ANSWERS
          </span>
          <span className="px-1.5 py-0.2 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
            MEMBER 4 ANSWER STUDIO
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
          Answer Studio & Investigation Dossier
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
          Ask precise forensic questions. Answers are generated strictly with traceable citations linked to exact source documents, page numbers, spreadsheet rows, or OCR coordinates.
        </p>
      </div>

      {/* Inquiry Console Input */}
      <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="text-xs font-mono uppercase tracking-wider text-slate-800 dark:text-cerberus-text font-bold flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
            Enter Investigation Question / Hypothesis
          </label>

          <div className="relative">
            <textarea
              rows={3}
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="e.g. Which sources contain conflicting information regarding shipment valuation? What evidence supports this claim?"
              className="w-full p-4 bg-slate-50 dark:bg-cerberus-bg border border-slate-200 dark:border-cerberus-border rounded-xl text-xs sm:text-sm text-slate-900 dark:text-cerberus-text placeholder-slate-400 dark:placeholder-cerberus-dark-muted focus:outline-none focus:border-blue-500 dark:focus:border-cerberus-cyan font-sans resize-none"
            />
          </div>

          {/* Quick Presets for Hackathon Judges */}
          <div className="space-y-1.5">
            <span className="text-[10px] font-mono text-slate-500 dark:text-cerberus-muted uppercase block font-semibold">
              Suggested Investigation Inquiries:
            </span>
            <div className="flex flex-wrap gap-2">
              {INVESTIGATION_PRESETS.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectPreset(q)}
                  className="text-left text-[11px] px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-cerberus-bg-secondary dark:hover:bg-cerberus-card text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white border border-slate-200 dark:border-cerberus-border transition-colors font-mono"
                >
                  "{q.slice(0, 75)}..."
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-cerberus-border">
            <span className="text-[11px] font-mono text-slate-500 dark:text-cerberus-muted">
              Endpoint Contract: <code className="text-blue-600 dark:text-cerberus-cyan font-bold">POST /investigate</code>
            </span>

            <button
              type="submit"
              disabled={processingState.isProcessing || !inputQuery.trim()}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-mono font-bold tracking-wider transition-all shadow-glow-blue flex items-center gap-2"
            >
              <Send className="w-3.5 h-3.5" />
              {processingState.isProcessing ? 'REASONING ACROSS EVIDENCE...' : 'SYNTHESIZE VERDICT'}
            </button>
          </div>
        </form>
      </div>

      {/* Loading state during AI inference */}
      {processingState.isProcessing && (
        <LoadingState
          message="Synthesizing Cross-Modal Neural Reasoning..."
          submessage="Evaluating page numbers, row coordinates, and optical OCR stamps across all 5 modalities."
        />
      )}

      {/* Error state if inquiry fails */}
      {!processingState.isProcessing && processingState.error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs font-mono text-rose-600 dark:text-cerberus-red flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{processingState.error}</span>
        </div>
      )}

      {/* Complete Report Viewer Component */}
      {!processingState.isProcessing && (
        <ReportViewer
          report={investigationReport}
          onNewQuery={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        />
      )}

    </div>
  );
};

export default ReportPage;
