import React from 'react';
import { motion } from 'framer-motion';
import { 
  Activity, 
  Database, 
  Network, 
  GitFork, 
  BrainCircuit, 
  FileCheck2, 
  ChevronLeft, 
  ChevronRight,
  ShieldAlert,
  Sparkles
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const Sidebar = () => {
  const { 
    activeTab, 
    setActiveTab, 
    sidebarCollapsed, 
    setSidebarCollapsed,
    conflicts,
    evidenceFiles
  } = useInvestigation();

  // Exactly 6 Primary Navigation Sections matching requirements
  const navItems = [
    { 
      id: 'overview', 
      label: 'Overview', 
      icon: Activity,
      hint: 'Dashboard statistics, recent activity, system health, alerts and summaries'
    },
    { 
      id: 'evidence-center', 
      label: 'Evidence Center', 
      icon: Database,
      badge: evidenceFiles.length > 0 ? evidenceFiles.length : null,
      badgeColor: 'bg-blue-500/10 text-blue-600 dark:text-cerberus-cyan border-blue-500/30',
      hint: 'File uploads, evidence vault, modality explorer and extracted sources'
    },
    { 
      id: 'knowledge-graph', 
      label: 'Knowledge Graph', 
      icon: Network,
      hint: 'Interactive topological graph, entity resolution and relational edges'
    },
    { 
      id: 'conflict-trust', 
      label: 'Conflict & Trust Analysis', 
      icon: GitFork,
      badge: conflicts.length > 0 ? conflicts.length : null,
      badgeColor: 'bg-rose-500/10 dark:bg-cerberus-red/20 text-rose-600 dark:text-cerberus-red border-rose-500/30 dark:border-cerberus-red/40',
      hint: 'Contradiction discovery, source reliability and adversarial scanning'
    },
    { 
      id: 'ai-investigation', 
      label: 'AI Investigation', 
      icon: BrainCircuit,
      hint: 'Question inquiry, claim investigation and neural reasoning engine'
    },
    { 
      id: 'reports-audit', 
      label: 'Reports & Audit', 
      icon: FileCheck2,
      hint: 'Traceable answers, case dossiers, audit trail and evaluation metrics'
    },
  ];

  const isItemActive = (itemId) => {
    if (activeTab === itemId) return true;
    if (itemId === 'overview' && activeTab === 'dashboard') return true;
    if (itemId === 'evidence-center' && ['evidence', 'upload', 'modality', 'vault'].includes(activeTab)) return true;
    if (itemId === 'knowledge-graph' && ['graph', 'entity-resolution', 'entities'].includes(activeTab)) return true;
    if (itemId === 'conflict-trust' && ['conflicts', 'reliability', 'adversarial'].includes(activeTab)) return true;
    if (itemId === 'ai-investigation' && ['reasoning', 'report', 'answer-studio'].includes(activeTab)) return true;
    if (itemId === 'reports-audit' && ['investigations', 'audit', 'settings', 'cases'].includes(activeTab)) return true;
    return false;
  };

  return (
    <aside
      className={`relative flex flex-col border-r border-slate-200 dark:border-cerberus-border bg-white dark:bg-cerberus-bg-secondary/95 backdrop-blur-md transition-all duration-300 z-30 shrink-0 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Top Sidebar Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-cerberus-border h-16">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="p-1.5 rounded-lg bg-blue-500/10 dark:bg-cerberus-card border border-blue-500/20 dark:border-cerberus-cyan/30 text-blue-600 dark:text-cerberus-cyan shadow-sm shrink-0">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <span className="font-extrabold text-xs tracking-wider font-mono text-slate-900 dark:text-cerberus-text block truncate">
                COMMAND CENTER
              </span>
              <span className="text-[10px] text-blue-600 dark:text-cerberus-cyan font-mono block">
                6 PRIMARY GRIDS
              </span>
            </div>
          </div>
        )}

        {/* Collapse toggle button */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className={`p-1.5 rounded-lg text-slate-500 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-cerberus-text hover:bg-slate-100 dark:hover:bg-cerberus-card transition-colors ${
            sidebarCollapsed ? 'mx-auto' : ''
          }`}
          title={sidebarCollapsed ? 'Expand Navigation Sidebar' : 'Collapse Sidebar'}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Exactly 6 Primary Navigation Items List */}
      <nav className="flex-1 overflow-y-auto p-2.5 space-y-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = isItemActive(item.id);
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-mono transition-all text-left group relative ${
                isActive
                  ? 'bg-blue-600/10 dark:bg-cerberus-blue/20 text-blue-600 dark:text-cerberus-cyan border border-blue-600/30 dark:border-cerberus-cyan/40 shadow-sm font-semibold'
                  : 'text-slate-600 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-cerberus-text hover:bg-slate-100 dark:hover:bg-cerberus-card/80 border border-transparent'
              }`}
              title={sidebarCollapsed ? `${item.label} — ${item.hint}` : undefined}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-colors ${
                  isActive 
                    ? 'text-blue-600 dark:text-cerberus-cyan' 
                    : 'text-slate-500 dark:text-cerberus-muted group-hover:text-slate-900 dark:group-hover:text-cerberus-text'
                }`}
              />
              
              {!sidebarCollapsed && (
                <span className="flex-1 truncate tracking-tight font-medium">{item.label}</span>
              )}

              {/* Counter Badges */}
              {!sidebarCollapsed && item.badge && (
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold border ${item.badgeColor}`}>
                  {item.badge}
                </span>
              )}

              {/* Collapsed dot badge */}
              {sidebarCollapsed && item.badge && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      {!sidebarCollapsed && (
        <div className="p-3 border-t border-slate-200 dark:border-cerberus-border/80 text-[10px] font-mono text-slate-500 dark:text-cerberus-dark-muted flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            CERBERUS-XA
          </span>
          <span className="text-blue-600 dark:text-cerberus-cyan font-bold">6 MODULES</span>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
