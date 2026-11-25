import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { InvestigationProvider, useInvestigation } from './context/InvestigationContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { RightPanel } from './components/RightPanel';
import { DemoModeBanner } from './components/DemoModeBanner';

// Pages & 6 Reorganized Hubs
import { LandingPage } from './pages/LandingPage';
import { Dashboard } from './pages/Dashboard';
import { EvidenceCenterPage } from './pages/EvidenceCenterPage';
import { KnowledgeGraphHubPage } from './pages/KnowledgeGraphHubPage';
import { ConflictTrustPage } from './pages/ConflictTrustPage';
import { AIInvestigationPage } from './pages/AIInvestigationPage';
import { ReportsAuditPage } from './pages/ReportsAuditPage';

import { ShieldAlert } from 'lucide-react';

const AppContent = () => {
  const { activeTab, backendStatus } = useInvestigation();

  const renderActivePage = () => {
    switch (activeTab) {
      case 'landing':
        return <LandingPage />;

      // 1. Overview
      case 'overview':
      case 'dashboard':
        return <Dashboard />;

      // 2. Evidence Center (Combines uploads, vault, modality explorer, previews)
      case 'evidence-center':
      case 'evidence':
      case 'upload':
      case 'modality':
      case 'vault':
        return <EvidenceCenterPage />;

      // 3. Knowledge Graph (Combines interactive graph, entity resolution, relationships)
      case 'knowledge-graph':
      case 'graph':
      case 'entity-resolution':
      case 'entities':
        return <KnowledgeGraphHubPage />;

      // 4. Conflict & Trust Analysis (Combines contradiction lab, reliability, adversarial scanner)
      case 'conflict-trust':
      case 'conflicts':
      case 'reliability':
      case 'adversarial':
        return <ConflictTrustPage />;

      // 5. AI Investigation (Combines question inquiry, AI reasoning, traceable answers)
      case 'ai-investigation':
      case 'reasoning':
      case 'report':
      case 'answer-studio':
        return <AIInvestigationPage />;

      // 6. Reports & Audit (Combines investigation cases, audit trail, evaluation metrics, settings)
      case 'reports-audit':
      case 'investigations':
      case 'audit':
      case 'settings':
      case 'cases':
        return <ReportsAuditPage />;

      default:
        return <Dashboard />;
    }
  };

  // If on Landing Page, render full cinematic landing layout
  if (activeTab === 'landing') {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#050A16] text-slate-900 dark:text-[#F1F5F9] flex flex-col font-sans selection:bg-blue-600 selection:text-white transition-colors duration-300">
        <Navbar />
        <DemoModeBanner />
        <main className="flex-1 w-full pt-6">
          <AnimatePresence mode="wait">
            <motion.div
              key="landing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <LandingPage />
            </motion.div>
          </AnimatePresence>
        </main>
        <footer className="border-t border-slate-200 dark:border-cerberus-border bg-white dark:bg-[#0A1325] py-6 text-xs font-mono text-slate-500 dark:text-cerberus-muted mt-auto transition-colors">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
              <span className="font-bold text-slate-900 dark:text-white">CERBERUS-XA</span>
              <span>•</span>
              <span>"Where Every Modality Can Contradict the Others."</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-cerberus-muted">
              Member 1: Frontend & UI Platform • FastAPI: {backendStatus.apiUrl}
            </div>
          </div>
        </footer>
      </div>
    );
  }

  // 3-Zone Workspace Layout for Command Center
  return (
    <div className="h-screen bg-slate-50 dark:bg-[#050A16] text-slate-900 dark:text-[#F1F5F9] flex flex-col font-sans selection:bg-blue-600 selection:text-white overflow-hidden transition-colors duration-300">
      {/* Top Navbar */}
      <Navbar />

      {/* Demo Mode Notification Banner */}
      <DemoModeBanner />

      {/* 3-Zone Intelligence Workspace */}
      <div className="flex-1 flex overflow-hidden">

        {/* Zone A: Left Sidebar (6 Primary Sections) */}
        <Sidebar />

        {/* Zone B: Center Workspace with Smooth Framer Motion Page Transition */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-slate-50 dark:bg-[#050A16] radar-grid transition-colors duration-300">
          <div className="max-w-7xl mx-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.22, ease: "easeOut" }}
              >
                {renderActivePage()}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>

        {/* Zone C: Right Intelligence Status Panel */}
        <RightPanel />

      </div>

      {/* Minimal Status Footer */}
      <footer className="border-t border-slate-200 dark:border-cerberus-border bg-white dark:bg-[#0A1325] px-4 py-2 text-[11px] font-mono text-slate-500 dark:text-cerberus-muted flex items-center justify-between shrink-0 z-30 transition-colors">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-600 dark:bg-cerberus-cyan animate-pulse" />
          <span className="text-slate-900 dark:text-white font-bold">CERBERUS-XA COMMAND CENTER</span>
          <span className="text-slate-300 dark:text-cerberus-border">|</span>
          <span className="hidden sm:inline">Offline Multimodal Verification Engine</span>
        </div>
        <div className="flex items-center gap-4">
          <span className={backendStatus.online ? 'text-emerald-600 dark:text-cerberus-green' : 'text-rose-600 dark:text-cerberus-red'}>
            {backendStatus.online ? 'FastAPI Connected' : 'FastAPI Offline'}
          </span>
          <span className="text-slate-300 dark:text-cerberus-border">|</span>
          <span>Member 1: Frontend & UI Development</span>
        </div>
      </footer>
    </div>
  );
};

export function App() {
  return (
    <InvestigationProvider>
      <AppContent />
    </InvestigationProvider>
  );
}

export default App;
