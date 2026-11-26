import React, { useState } from 'react';
import { 
  GitFork, 
  AlertOctagon, 
  Network, 
  BarChart3, 
  ShieldAlert, 
  Filter,
  ArrowRight
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  Cell 
} from 'recharts';
import { useInvestigation } from '../context/InvestigationContext';
import { ConflictCard } from '../components/ConflictCard';
import { KnowledgeGraph } from '../components/KnowledgeGraph';
import { EmptyState } from '../components/EmptyState';

export const ConflictPage = () => {
  const { conflicts, knowledgeGraph, setActiveTab } = useInvestigation();
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');

  const filteredConflicts = conflicts.filter(c => {
    return selectedSeverity === 'ALL' || c.severity === selectedSeverity;
  });

  const conflictStats = [
    { name: 'Financial Valuation', count: 1, severity: 'Critical', color: '#FF536B' },
    { name: 'Temporal Berthing', count: 1, severity: 'Critical', color: '#FF536B' },
    { name: 'Physical Mass Delta', count: 1, severity: 'High', color: '#FFB547' },
  ];

  return (
    <div className="space-y-8 pb-16">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-rose-600 dark:text-cerberus-red">
              CONTRADICTION LAB & CROSS-EXAMINATION
            </span>
            <span className="px-1.5 py-0.2 rounded bg-rose-50 dark:bg-cerberus-red/15 text-rose-600 dark:text-cerberus-red border border-rose-200 dark:border-cerberus-red/30 text-[10px] font-mono">
              MEMBER 3 CONFLICT ENGINE
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
            Conflict Detection Lab
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
            Identifies when independent modalities clash: official declarations vs internal ERP ledgers vs optical sensor telemetry. Does not assume a claim is true merely because it appears in more documents.
          </p>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center gap-2">
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border rounded-xl text-xs text-slate-700 dark:text-cerberus-muted focus:outline-none focus:border-rose-500 dark:focus:border-cerberus-cyan font-mono"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="HIGH">High Only</option>
          </select>
        </div>
      </div>

      {conflicts.length === 0 ? (
        <EmptyState
          title="No Contradictions Detected"
          message="No active conflicts detected in current session. Upload multimodal files or toggle Demo Mode."
        />
      ) : (
        <>
          {/* Conflict Summary Comparison Chart (Recharts) */}
          <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel">
            <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-cerberus-border pb-3">
              <div>
                <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-rose-600 dark:text-cerberus-red" />
                  Conflict Category Breakdown & Discrepancy Scale
                </h3>
                <p className="text-[11px] text-slate-600 dark:text-cerberus-muted mt-0.5 font-sans">
                  Quantified delta across financial, temporal, and physical modalities
                </p>
              </div>
              <span className="text-xs font-mono text-rose-600 dark:text-cerberus-red font-bold">
                {conflicts.length} Active Contradictions
              </span>
            </div>

            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={conflictStats} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1A2C4B" />
                  <XAxis type="number" stroke="#64748B" fontSize={11} fontFamily="monospace" />
                  <YAxis type="category" dataKey="name" stroke="#CBD5E1" fontSize={11} fontFamily="monospace" width={160} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0B1426', borderColor: '#243C66', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                    itemStyle={{ color: '#F1F5F9' }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {conflictStats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Interactive Knowledge Graph Visualization */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-cerberus-text flex items-center gap-2">
                <Network className="w-4 h-4 text-cerberus-cyan" />
                Multimodal Conflict Graph Visualization
              </span>
              <span className="text-[11px] font-mono text-cerberus-muted">
                Red dashed lines indicate contradiction edges
              </span>
            </div>
            <KnowledgeGraph graphData={knowledgeGraph} />
          </section>

          {/* Detailed Side-by-Side Contradiction Cards */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-cerberus-text flex items-center gap-2">
                <AlertOctagon className="w-4 h-4 text-cerberus-red" />
                Detailed Conflict Comparison Dossiers ({filteredConflicts.length})
              </span>
              <button
                onClick={() => setActiveTab('reasoning')}
                className="text-xs font-mono text-cerberus-cyan hover:underline flex items-center gap-1 font-semibold"
              >
                Synthesize Reasoning <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-1 gap-5">
              {filteredConflicts.map((conflict) => (
                <ConflictCard key={conflict.id} conflict={conflict} />
              ))}
            </div>
          </section>
        </>
      )}

    </div>
  );
};

export default ConflictPage;
