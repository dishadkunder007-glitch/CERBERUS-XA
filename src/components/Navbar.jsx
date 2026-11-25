import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, 
  Activity, 
  Briefcase, 
  Database, 
  GitFork, 
  Radio, 
  Settings, 
  UploadCloud, 
  SlidersHorizontal, 
  RefreshCw,
  PanelRight,
  Sun,
  Moon,
  Network,
  BrainCircuit,
  FileCheck2
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const Navbar = () => {
  const { 
    theme,
    toggleTheme,
    activeTab, 
    setActiveTab, 
    backendStatus, 
    verifyBackend, 
    isDemoMode, 
    setIsDemoMode,
    rightPanelOpen,
    setRightPanelOpen
  } = useInvestigation();

  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'evidence-center', label: 'Evidence Center', icon: Database },
    { id: 'knowledge-graph', label: 'Knowledge Graph', icon: Network },
    { id: 'conflict-trust', label: 'Conflict & Trust', icon: GitFork },
    { id: 'ai-investigation', label: 'AI Investigation', icon: BrainCircuit },
    { id: 'reports-audit', label: 'Reports & Audit', icon: FileCheck2 },
  ];

  const isLinkActive = (id) => {
    if (activeTab === id) return true;
    if (id === 'overview' && activeTab === 'dashboard') return true;
    if (id === 'evidence-center' && ['evidence', 'upload', 'modality', 'vault'].includes(activeTab)) return true;
    if (id === 'knowledge-graph' && ['graph', 'entity-resolution', 'entities'].includes(activeTab)) return true;
    if (id === 'conflict-trust' && ['conflicts', 'reliability', 'adversarial'].includes(activeTab)) return true;
    if (id === 'ai-investigation' && ['reasoning', 'report', 'answer-studio'].includes(activeTab)) return true;
    if (id === 'reports-audit' && ['investigations', 'audit', 'settings', 'cases'].includes(activeTab)) return true;
    return false;
  };

  return (
    <header className={`sticky top-0 z-50 border-b transition-all duration-300 ${
      isScrolled 
        ? 'border-slate-300/80 dark:border-cerberus-border bg-white/95 dark:bg-cerberus-bg/95 backdrop-blur-2xl shadow-md'
        : 'border-slate-200/80 dark:border-cerberus-border/70 bg-white/80 dark:bg-cerberus-bg/80 backdrop-blur-xl'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          
          {/* Logo & Platform Title (Never wraps, shrink-0) */}
          <div className="flex items-center gap-3 shrink-0">
            <button 
              onClick={() => setActiveTab('landing')}
              className="flex items-center gap-2.5 text-left group transition-all"
            >
              <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-slate-100 dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-border group-hover:border-cerberus-cyan/50 transition-colors shadow-glow-cyan shrink-0">
                <ShieldAlert className="w-5 h-5 text-cerberus-blue dark:text-cerberus-cyan" />
                <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cerberus-cyan opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cerberus-cyan"></span>
                </span>
              </div>
              <div className="whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold tracking-wider text-base sm:text-lg bg-gradient-to-r from-blue-600 via-cyan-500 to-indigo-600 dark:from-blue-400 dark:via-cyan-300 dark:to-indigo-300 bg-clip-text text-transparent font-mono whitespace-nowrap">
                    CERBERUS-XA
                  </span>
                  <span className="px-1.5 py-0.5 text-[10px] font-mono tracking-widest uppercase bg-blue-500/10 text-blue-600 dark:text-cerberus-cyan border border-blue-500/20 dark:border-cerberus-cyan/30 rounded whitespace-nowrap">
                    INTELLIGENCE
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 dark:text-cerberus-muted tracking-tight hidden sm:block font-sans whitespace-nowrap">
                  Multimodal Evidence Graph & Conflict Reasoning
                </p>
              </div>
            </button>
          </div>

          {/* Center Navigation Links with Smooth Sliding Indicator */}
          <nav className="hidden lg:flex items-center space-x-1 shrink-0">
            {navLinks.map((item) => {
              const Icon = item.icon;
              const isActive = isLinkActive(item.id);
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-blue-600 dark:text-cerberus-cyan font-bold'
                      : 'text-slate-600 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-cerberus-text'
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeNavPill"
                      className="absolute inset-0 rounded-lg bg-blue-500/10 dark:bg-cerberus-blue/20 border border-blue-500/30 dark:border-cerberus-cyan/40 shadow-sm"
                      transition={{ type: "spring", stiffness: 350, damping: 30 }}
                    />
                  )}
                  <Icon className={`w-3.5 h-3.5 relative z-10 ${isActive ? 'text-blue-600 dark:text-cerberus-cyan' : 'text-slate-400 dark:text-cerberus-muted'}`} />
                  <span className="relative z-10">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Status Controls */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
            
            {/* Segmented Dual-Pill Theme Switcher (Dark & Light) */}
            <div className="flex items-center bg-slate-100 dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-border rounded-xl p-1 gap-1 shadow-sm">
              <button
                type="button"
                onClick={() => theme !== 'dark' && toggleTheme()}
                className={`relative flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all whitespace-nowrap ${
                  theme === 'dark'
                    ? 'text-cerberus-cyan'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
                title="Switch to Obsidian Cyber Dark Mode"
              >
                {theme === 'dark' && (
                  <motion.div
                    layoutId="navbarThemePill"
                    className="absolute inset-0 rounded-lg bg-cerberus-blue/25 border border-cerberus-cyan/50 shadow-glow-cyan"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <Moon className={`w-3.5 h-3.5 relative z-10 ${theme === 'dark' ? 'text-cerberus-cyan' : 'text-slate-400'}`} />
                <span className="relative z-10 text-[11px]">DARK</span>
              </button>

              <button
                type="button"
                onClick={() => theme !== 'light' && toggleTheme()}
                className={`relative flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all whitespace-nowrap ${
                  theme === 'light'
                    ? 'text-blue-700'
                    : 'text-cerberus-muted hover:text-white'
                }`}
                title="Switch to Clean High-Contrast Light Mode"
              >
                {theme === 'light' && (
                  <motion.div
                    layoutId="navbarThemePill"
                    className="absolute inset-0 rounded-lg bg-white border border-blue-400/50 shadow-sm"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <Sun className={`w-3.5 h-3.5 relative z-10 ${theme === 'light' ? 'text-amber-500' : 'text-cerberus-muted'}`} />
                <span className="relative z-10 text-[11px]">LIGHT</span>
              </button>
            </div>

            {/* Demo Mode Toggle */}
            <div className="flex items-center bg-slate-100 dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-border rounded-lg p-0.5">
              <button
                onClick={() => setIsDemoMode(!isDemoMode)}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-mono transition-colors whitespace-nowrap ${
                  isDemoMode 
                    ? 'bg-amber-500/20 text-amber-700 dark:text-cerberus-amber border border-amber-500/40 font-semibold' 
                    : 'text-slate-500 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-cerberus-text'
                }`}
                title="Toggle between Jury Demo Benchmark and Live Clean Backend"
              >
                <SlidersHorizontal className="w-3 h-3" />
                <span className="hidden sm:inline">DEMO:</span> {isDemoMode ? 'ON' : 'OFF'}
              </button>
            </div>

            {/* Backend Health Ping */}
            <button
              onClick={() => verifyBackend()}
              title={`FastAPI Backend: ${backendStatus.apiUrl} (${backendStatus.online ? 'Online' : 'Offline'}). Click to re-check.`}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono border transition-all whitespace-nowrap ${
                backendStatus.online
                  ? 'bg-emerald-500/10 text-emerald-700 dark:text-cerberus-green border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-700 dark:text-cerberus-red border-rose-500/30'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${backendStatus.online ? 'bg-emerald-500 dark:bg-cerberus-green animate-pulse' : 'bg-rose-500 dark:bg-cerberus-red'}`} />
              <span className="hidden md:inline">API</span>
              <span>{backendStatus.online ? 'CONNECTED' : 'OFFLINE'}</span>
              <RefreshCw className="w-3 h-3 opacity-60 hover:opacity-100 ml-0.5" />
            </button>

            {/* Primary Action Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveTab('upload')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 text-white text-xs font-mono font-bold shadow-glow-blue transition-all whitespace-nowrap"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Ingest</span>
            </motion.button>

            {/* Right Panel Toggle (Only in workspace view) */}
            {activeTab !== 'landing' && (
              <button
                onClick={() => setRightPanelOpen(!rightPanelOpen)}
                className={`p-1.5 rounded-lg border transition-colors ${
                  rightPanelOpen
                    ? 'bg-blue-500/15 border-blue-500/30 text-blue-600 dark:text-cerberus-cyan'
                    : 'bg-slate-100 dark:bg-cerberus-card border-slate-300 dark:border-cerberus-border text-slate-500 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-white'
                }`}
                title={rightPanelOpen ? 'Hide Intelligence Panel' : 'Show Intelligence Panel'}
              >
                <PanelRight className="w-4 h-4" />
              </button>
            )}

          </div>

        </div>
      </div>
    </header>
  );
};

export default Navbar;
