import React from 'react';
import { 
  Network, 
  HelpCircle, 
  Sparkles, 
  Info,
  ShieldAlert
} from 'lucide-react';
import { KnowledgeGraph } from '../components/KnowledgeGraph';
import { useInvestigation } from '../context/InvestigationContext';

export const KnowledgeGraphPage = () => {
  const { knowledgeGraph, isDemoMode, setIsDemoMode } = useInvestigation();

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-600 dark:text-cerberus-cyan">
              TOPOLOGICAL INTELLIGENCE GRAPH
            </span>
            <span className="px-1.5 py-0.2 rounded bg-cyan-50 dark:bg-cerberus-blue/15 text-cyan-700 dark:text-cerberus-cyan border border-cyan-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
              MEMBER 3 GRAPH ENGINE
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
            Connected Knowledge Graph
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
            Multi-relational knowledge representation linking entity nodes, document sources, atomic claims, and contradiction edges.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1.5 rounded-xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border text-cyan-700 dark:text-cerberus-cyan font-bold shadow-sm">
            {knowledgeGraph?.nodes?.length || 0} Nodes • {knowledgeGraph?.links?.length || 0} Edges
          </span>
        </div>
      </div>

      {/* Interactive Knowledge Graph */}
      <KnowledgeGraph graphData={knowledgeGraph} />

      {/* Integration Contract Note for Member 3 */}
      <div className="p-4 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border flex items-start gap-3 text-xs font-mono shadow-sm">
        <Info className="w-5 h-5 text-cyan-600 dark:text-cerberus-cyan shrink-0 mt-0.5" />
        <div>
          <span className="text-slate-900 dark:text-white font-bold uppercase">Member 3 Backend Integration Contract:</span>
          <p className="text-slate-600 dark:text-cerberus-muted font-sans mt-0.5">
            This topological visualizer renders live data from <code className="text-cyan-700 dark:text-cerberus-cyan">GET /graph</code>. 
            When live backend graph endpoints stream updated nodes and directional links, this canvas dynamically mounts without rewriting the interface.
          </p>
        </div>
      </div>

    </div>
  );
};

export default KnowledgeGraphPage;
