import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  FileWarning, 
  Download, 
  HelpCircle, 
  CheckCircle, 
  XCircle, 
  FileText, 
  BrainCircuit, 
  Scale, 
  Layers,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Loader2,
  FileJson,
  FileSpreadsheet,
  FileType2
} from 'lucide-react';
import { exportInvestigationReport } from '../services/investigationService';

export const ReportViewer = ({ report, onNewQuery }) => {
  const [expandedCitation, setExpandedCitation] = useState(null);
  const [exportingFormat, setExportingFormat] = useState(null);
  const [exportError, setExportError] = useState(null);

  if (!report) {
    return (
      <div className="p-8 text-center rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
        <BrainCircuit className="w-12 h-12 text-blue-600 dark:text-cerberus-muted mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-900 dark:text-white font-mono">No Investigation Report Generated Yet</h3>
        <p className="text-xs text-slate-600 dark:text-cerberus-muted max-w-md mx-auto mt-1 mb-4 font-sans">
          Submit an inquiry hypothesis to synthesize a cross-modal verification report with citation provenance.
        </p>
        {onNewQuery && (
          <button
            onClick={onNewQuery}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 text-white text-xs font-mono font-bold shadow-glow-blue"
          >
            Launch Investigation Inquiry
          </button>
        )}
      </div>
    );
  }

  const {
    reportId = 'REP-2026-091',
    caseId = 'CASE-2026-BOREAS-09X',
    timestamp = report.generatedAt || new Date().toISOString(),
    investigationQuestion = report.question || '',
    finalVerdict = report.verdict || 'Insufficient evidence',
    verdictConfidence = report.verdictConfidence ?? (typeof report.confidence === 'number' ? (report.confidence > 1 ? report.confidence / 100 : report.confidence) : 0),
    summaryAnswer = report.summary || report.answer || '',
    reasoningExplanation = [],
    supportingEvidence = [],
    contradictingEvidence = [],
    sourceReliability = [],
    citations = []
  } = report;

  const normalizedConfidence = typeof verdictConfidence === 'number'
    ? (verdictConfidence > 1 ? verdictConfidence / 100 : verdictConfidence)
    : 0;

  const getVerdictDetails = (v) => {
    const lower = String(v || '').toLowerCase();
    if (lower.includes('supported') || lower === 'answered') {
      return {
        badgeClass: 'bg-cerberus-green/15 text-cerberus-green border-cerberus-green/40',
        icon: <ShieldCheck className="w-5 h-5 text-cerberus-green" />,
        headline: 'SUPPORTED BY EVIDENCE',
      };
    }
    if (lower.includes('conflict')) {
      return {
        badgeClass: 'bg-cerberus-red/15 text-cerberus-red border-cerberus-red/40',
        icon: <AlertTriangle className="w-5 h-5 text-cerberus-red" />,
        headline: 'CONFLICTING EVIDENCE DETECTED',
      };
    }
    if (lower.includes('insufficient')) {
      return {
        badgeClass: 'bg-cerberus-amber/15 text-cerberus-amber border-cerberus-amber/40',
        icon: <HelpCircle className="w-5 h-5 text-cerberus-amber" />,
        headline: 'INSUFFICIENT EVIDENCE',
      };
    }
    if (lower.includes('partial')) {
      return {
        badgeClass: 'bg-cerberus-amber/15 text-cerberus-amber border-cerberus-amber/40',
        icon: <HelpCircle className="w-5 h-5 text-cerberus-amber" />,
        headline: 'PARTIALLY SUPPORTED / INCONCLUSIVE',
      };
    }
    return {
      badgeClass: 'bg-purple-500/15 text-purple-300 border-purple-500/40',
      icon: <FileWarning className="w-5 h-5 text-purple-400" />,
      headline: String(v || 'INVESTIGATION VERDICT').toUpperCase(),
    };
  };

  const verdictMeta = getVerdictDetails(finalVerdict);

  const handleExportMarkdown = () => {
    const content = `
# CERBERUS-XA FORENSIC INTELLIGENCE DOSSIER
============================================================
CASE REF: ${caseId}
REPORT ID: ${reportId}
TIMESTAMP: ${timestamp}
LEAD ENGINE: Member 4 (Cross-Modal Neural Conflict Verifier)
============================================================

## INVESTIGATION QUERY:
${investigationQuestion}

## FINAL DETERMINATION:
[ ${String(finalVerdict).toUpperCase()} ]
Confidence Metric: ${(normalizedConfidence * 100).toFixed(1)}%

## EXECUTIVE SUMMARY & SYNTHESIS:
${summaryAnswer}

## STEP-BY-STEP REASONING TREE:
${reasoningExplanation.map(r => `${r.step}. ${r.title}: ${r.detail}`).join('\n')}

## CONTRADICTING EVIDENCE (MODALITY CLASHES):
${contradictingEvidence.map(c => `- [${c.criticality}] ${c.source}: "${c.claim}" (REFUTES: ${c.contradicts}) [Citation: ${c.citationRef || 'Direct Coordinate'}]`).join('\n')}

## SUPPORTING EVIDENCE:
${supportingEvidence.map(s => `- [${s.modality}] ${s.source}: "${s.finding}" (Reliability: ${(s.reliability * 100).toFixed(1)}%) [Citation: ${s.citationRef || 'Direct Coordinate'}]`).join('\n')}

## SOURCE RELIABILITY AUDIT:
${sourceReliability.map(sr => `- ${sr.sourceName}: Score ${(sr.score * 100).toFixed(1)}% [${sr.authStatus || sr.status}] - ${sr.reason || sr.assessment}`).join('\n')}

============================================================
GENERATED BY CERBERUS-XA AUTOMATED EVIDENCE REASONING SYSTEM
`.trim();

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `CERBERUS_DOSSIER_${reportId}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportFormat = async (format) => {
    setExportingFormat(format);
    setExportError(null);
    try {
      const blob = await exportInvestigationReport(report, format);
      const mimeMap = {
        json: 'application/json',
        csv: 'text/csv;charset=utf-8;',
        pdf: 'application/pdf',
      };
      const typedBlob = new Blob([blob], { type: mimeMap[format] || 'application/octet-stream' });
      const url = URL.createObjectURL(typedBlob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CERBERUS_DOSSIER_${reportId}.${format}`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(err?.message || `Failed to export ${format.toUpperCase()} report. Ensure backend is running.`);
    } finally {
      setExportingFormat(null);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Dossier Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-5 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs px-2.5 py-1 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 font-bold">
              {reportId}
            </span>
            <span className="text-xs font-mono text-slate-500 dark:text-cerberus-muted">
              Case Reference: <strong className="text-slate-900 dark:text-white">{caseId}</strong>
            </span>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-cerberus-muted font-mono mt-1">
            Generated: {new Date(timestamp).toLocaleString()} • Member 4 Verified
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleExportMarkdown}
            disabled={!!exportingFormat}
            className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-glow-blue transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            .MD
          </button>

          <button
            onClick={() => handleExportFormat('json')}
            disabled={!!exportingFormat}
            className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-cerberus-bg-secondary dark:hover:bg-cerberus-bg border border-slate-300 dark:border-cerberus-border disabled:opacity-50 text-slate-800 dark:text-cerberus-cyan text-xs font-mono font-bold flex items-center gap-1.5 transition-all"
          >
            {exportingFormat === 'json' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileJson className="w-3.5 h-3.5" />}
            JSON
          </button>

          <button
            onClick={() => handleExportFormat('csv')}
            disabled={!!exportingFormat}
            className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-cerberus-bg-secondary dark:hover:bg-cerberus-bg border border-slate-300 dark:border-cerberus-border disabled:opacity-50 text-slate-800 dark:text-emerald-400 text-xs font-mono font-bold flex items-center gap-1.5 transition-all"
          >
            {exportingFormat === 'csv' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileSpreadsheet className="w-3.5 h-3.5" />}
            CSV
          </button>

          <button
            onClick={() => handleExportFormat('pdf')}
            disabled={!!exportingFormat}
            className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-cerberus-bg-secondary dark:hover:bg-cerberus-bg border border-slate-300 dark:border-cerberus-border disabled:opacity-50 text-slate-800 dark:text-rose-400 text-xs font-mono font-bold flex items-center gap-1.5 transition-all"
          >
            {exportingFormat === 'pdf' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileType2 className="w-3.5 h-3.5" />}
            PDF
          </button>
        </div>
      </div>

      {exportError && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs font-mono text-rose-500 dark:text-cerberus-red flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{exportError}</span>
        </div>
      )}

      {/* Inquiry Question Prompt Box */}
      <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-1">
        <span className="text-[10px] font-mono uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan font-bold block flex items-center gap-1.5">
          <BrainCircuit className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-cyan" />
          INVESTIGATION INQUIRY QUESTION
        </span>
        <p className="text-base sm:text-lg font-bold text-slate-900 dark:text-white font-sans leading-snug">
          "{investigationQuestion}"
        </p>
      </div>

      {/* Primary Verdict Card */}
      <div className={`p-6 rounded-2xl border bg-white dark:bg-cerberus-card ${verdictMeta.badgeClass} shadow-sm dark:shadow-panel space-y-4`}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-cerberus-bg/90 border border-current">
              {verdictMeta.icon}
            </div>
            <div>
              <span className="text-[10px] font-mono tracking-widest uppercase opacity-80 block">
                PRIMARY DETERMINATION STATUS
              </span>
              <h2 className="text-xl sm:text-2xl font-black font-mono tracking-wide">
                {verdictMeta.headline}
              </h2>
            </div>
          </div>

          <div className="text-right font-mono">
            <span className="text-[10px] uppercase text-slate-500 dark:text-cerberus-muted block">
              Confidence Index
            </span>
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white">
              {(normalizedConfidence * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="pt-4 border-t border-slate-200 dark:border-cerberus-border/60">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 dark:text-cerberus-muted block mb-1.5 font-bold">
            Cross-Modal Synthesis & Answer:
          </span>
          <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
            {summaryAnswer}
          </p>
        </div>
      </div>

      {/* Reasoning Tree */}
      {reasoningExplanation.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-cerberus-border bg-white dark:bg-cerberus-card p-6 shadow-sm dark:shadow-panel space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-200 dark:border-cerberus-border pb-3">
            <Scale className="w-4 h-4 text-blue-600 dark:text-cerberus-blue" />
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-900 dark:text-white">
              Step-by-Step Forensic Reasoning Explanation
            </h3>
          </div>

          <div className="space-y-3.5 relative before:absolute before:left-3.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200 dark:before:bg-cerberus-border">
            {reasoningExplanation.map((step) => (
              <div key={step.step} className="relative flex items-start gap-4 pl-1">
                <div className="w-7 h-7 rounded-full bg-slate-100 dark:bg-cerberus-bg-secondary border border-blue-400 dark:border-cerberus-cyan/50 flex items-center justify-center text-xs font-mono font-bold text-blue-600 dark:text-cerberus-cyan shrink-0 z-10 shadow-sm">
                  {step.step}
                </div>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border w-full">
                  <h4 className="text-xs font-bold font-mono text-slate-900 dark:text-white">
                    {step.title}
                  </h4>
                  <p className="text-xs text-slate-700 dark:text-slate-300 font-sans mt-1 leading-relaxed">
                    {step.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contradicting vs Supporting Evidence with Expandable Citations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Contradictions */}
        <div className="rounded-2xl border border-cerberus-red/40 bg-cerberus-card p-6 shadow-panel space-y-3">
          <div className="flex items-center gap-2 border-b border-cerberus-border pb-3">
            <XCircle className="w-4 h-4 text-cerberus-red" />
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-cerberus-red">
              Contradicting Claims ({contradictingEvidence.length})
            </h3>
          </div>

          <div className="space-y-3">
            {contradictingEvidence.length === 0 ? (
              <p className="text-xs font-mono text-cerberus-muted py-2">No contradicting claims detected for this inquiry.</p>
            ) : contradictingEvidence.map((con, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-cerberus-red/10 border border-cerberus-red/30 text-xs font-mono space-y-2">
                <div className="flex items-center justify-between text-[10px] text-cerberus-red font-bold">
                  <span>{con.source}</span>
                  <span className="px-1.5 py-0.5 rounded bg-cerberus-red/20">{con.criticality}</span>
                </div>
                <p className="text-white font-sans font-medium text-xs">"{con.claim}"</p>
                <div className="text-[11px] text-cerberus-muted font-mono">
                  <strong className="text-cerberus-red">Refutes:</strong> {con.contradicts}
                </div>

                {/* Expandable Citation Details */}
                {con.citationRef && (
                  <div className="pt-2 border-t border-cerberus-border/60">
                    <button
                      onClick={() => setExpandedCitation(expandedCitation === `con-${idx}` ? null : `con-${idx}`)}
                      className="text-[10px] font-mono text-cerberus-cyan hover:underline flex items-center gap-1"
                    >
                      <span>Citation Coordinate: {con.citationRef}</span>
                      {expandedCitation === `con-${idx}` ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                    {expandedCitation === `con-${idx}` && (
                      <div className="mt-1.5 p-2 rounded bg-cerberus-bg text-[10px] text-slate-300 font-sans">
                        Verified spatial bounding and clause extraction from origin file: {con.source}.
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Supporting Evidence */}
        <div className="rounded-2xl border border-cerberus-green/40 bg-cerberus-card p-6 shadow-panel space-y-3">
          <div className="flex items-center gap-2 border-b border-cerberus-border pb-3">
            <CheckCircle className="w-4 h-4 text-cerberus-green" />
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-cerberus-green">
              Supporting Evidence ({supportingEvidence.length})
            </h3>
          </div>

          <div className="space-y-3">
            {supportingEvidence.length === 0 ? (
              <p className="text-xs font-mono text-cerberus-muted py-2">No direct supporting claims extracted for this inquiry.</p>
            ) : supportingEvidence.map((sup, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-cerberus-green/10 border border-cerberus-green/30 text-xs font-mono space-y-2">
                <div className="flex items-center justify-between text-[10px] text-cerberus-green font-bold">
                  <span>{sup.source}</span>
                  <span>{(sup.reliability * 100).toFixed(0)}% RELIABILITY</span>
                </div>
                <p className="text-white font-sans font-medium text-xs">"{sup.finding}"</p>
                <div className="text-[10px] text-cerberus-muted uppercase">
                  Modality: {sup.modality}
                </div>

                {/* Citation */}
                {sup.citationRef && (
                  <div className="pt-2 border-t border-cerberus-border/60 text-[10px] text-cerberus-cyan font-mono">
                    Provenance Coordinate: <strong className="text-white">{sup.citationRef}</strong>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Traceable Source Citations */}
      {citations.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-cerberus-border bg-white dark:bg-cerberus-card p-6 shadow-sm dark:shadow-panel space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-200 dark:border-cerberus-border pb-3">
            <FileText className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-900 dark:text-white">
              Traceable Source Citations ({citations.length})
            </h3>
          </div>
          <div className="space-y-2">
            {citations.map((cit, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border text-xs font-mono text-slate-700 dark:text-slate-300">
                {cit.formatted_citation || `${cit.citation_id || `[${idx + 1}]`} ${cit.filename || cit.source_id} (${cit.source_type || 'document'})`}
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};

export default ReportViewer;
