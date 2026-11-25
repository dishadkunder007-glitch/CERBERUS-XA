import React, { useState } from 'react';
import { 
  Users, 
  GitMerge, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  ArrowRight,
  ExternalLink,
  Search,
  UserCheck
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const EntityResolutionPage = () => {
  const { entities, entityResolutions } = useInvestigation();
  const [resolutions, setResolutions] = useState(entityResolutions);
  const [filterStatus, setFilterStatus] = useState('ALL');

  const handleManualVerify = (id) => {
    setResolutions(prev => prev.map(res => {
      if (res.id === id) {
        return {
          ...res,
          status: 'MERGED',
          manualVerificationBy: 'Forensic Analyst (Verified)'
        };
      }
      return res;
    }));
  };

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-amber-600 dark:text-cerberus-gold">
              CROSS-MODAL ENTITY MATCHING
            </span>
            <span className="px-1.5 py-0.2 rounded bg-amber-50 dark:bg-cerberus-blue/15 text-amber-700 dark:text-cerberus-cyan border border-amber-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
              MEMBER 3 ENTITY RESOLVER
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
            Entity Resolution & Disambiguation
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
            Unifies alias variations, serial identifiers, company names, and vessel registrations across heterogeneous documents. Uncertain matches require human verification before merging.
          </p>
        </div>
      </div>

      {/* Resolved Canonical Entities Grid */}
      <div className="space-y-3">
        <h3 className="font-mono font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-cerberus-text flex items-center gap-2">
          <Users className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
          Canonical Entities ({entities.length})
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {entities.map((ent) => (
            <div
              key={ent.id}
              className="p-5 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-3"
            >
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 font-bold">
                    {ent.id}
                  </span>
                  <h4 className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                    {ent.canonicalName}
                  </h4>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 dark:bg-cerberus-green/10 text-emerald-700 dark:text-cerberus-green border border-emerald-200 dark:border-cerberus-green/30 font-bold">
                  {ent.status}
                </span>
              </div>

              <div className="text-xs font-mono space-y-1">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted uppercase block">Resolved Aliases:</span>
                <div className="flex flex-wrap gap-1.5">
                  {ent.resolvedAliases.map((alias, aIdx) => (
                    <span key={aIdx} className="px-2 py-0.5 rounded bg-slate-100 dark:bg-cerberus-bg-secondary text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-cerberus-border text-[11px]">
                      {alias}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-cerberus-border text-[11px] font-mono text-slate-500 dark:text-cerberus-muted">
                <span>Mentions: <strong className="text-blue-600 dark:text-cerberus-cyan">{ent.sourceMentionsCount} Sources</strong></span>
                <span className="text-emerald-600 dark:text-cerberus-green font-bold">Match Confidence: {(ent.confidence * 100).toFixed(1)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Suggested Entity Merges & Verification Queue */}
      <div className="space-y-3 pt-4">
        <h3 className="font-mono font-bold text-xs uppercase tracking-wider text-amber-700 dark:text-cerberus-gold flex items-center gap-2">
          <GitMerge className="w-4 h-4 text-amber-600 dark:text-cerberus-gold" />
          Cross-Source Candidate Matches & Verification Queue
        </h3>

        <div className="space-y-3">
          {resolutions.map((res) => (
            <div
              key={res.id}
              className="p-5 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs font-mono"
            >
              <div className="space-y-1.5 max-w-xl">
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="font-bold text-amber-700 dark:text-cerberus-gold">{res.id}</span>
                  <span className="text-slate-500 dark:text-cerberus-muted">Similarity Score:</span>
                  <span className="font-bold text-emerald-600 dark:text-cerberus-green">{(res.similarityScore * 100).toFixed(0)}% Match</span>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center gap-2 font-semibold text-slate-900 dark:text-white text-xs">
                  <span className="p-1 rounded bg-slate-100 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">{res.candidateNameA}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-cyan shrink-0 hidden sm:inline" />
                  <span className="p-1 rounded bg-slate-100 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">{res.candidateNameB}</span>
                </div>

                <div className="text-[11px] text-slate-600 dark:text-cerberus-muted font-sans">
                  Matching Attributes: <strong className="text-slate-800 dark:text-slate-300 font-mono">{res.matchingAttributes.join(' • ')}</strong>
                </div>

                {res.manualVerificationBy && (
                  <div className="text-[10px] text-emerald-600 dark:text-cerberus-green flex items-center gap-1">
                    <UserCheck className="w-3.5 h-3.5" />
                    Verified by: {res.manualVerificationBy}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {res.status === 'MERGED' ? (
                  <span className="px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-cerberus-green/10 text-emerald-700 dark:text-cerberus-green border border-emerald-200 dark:border-cerberus-green/30 font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    MERGED & RESOLVED
                  </span>
                ) : (
                  <button
                    onClick={() => handleManualVerify(res.id)}
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 text-white font-bold shadow-glow-blue transition-all flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Verify & Merge
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};

export default EntityResolutionPage;
