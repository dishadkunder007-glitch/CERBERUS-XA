import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { 
  ShieldAlert, 
  ArrowRight, 
  Network, 
  GitFork, 
  BrainCircuit, 
  FileText, 
  Image as ImageIcon, 
  Table as TableIcon, 
  Lock, 
  Search, 
  Cpu, 
  Layers, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  ChevronDown, 
  ShieldCheck, 
  FileSearch, 
  Crosshair, 
  Zap, 
  Fingerprint 
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';
import { HeroCarousel } from '../components/HeroCarousel';
import { AnimatedCounter } from '../components/AnimatedCounter';

export const LandingPage = () => {
  const { setActiveTab, setIsDemoMode } = useInvestigation();
  const shouldReduceMotion = useReducedMotion();

  const handleScrollToFeatures = () => {
    const el = document.getElementById('features-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const featureIndicators = [
    { 
      code: "MODALITY-01",
      title: "Multimodal Evidence", 
      desc: "Heterogeneous ingestion of PDF filings, optical imagery, and tabular spreadsheets without cross-modal bias.", 
      metricTarget: 3,
      metricSuffix: " Ingestion Engines",
      icon: Layers, 
      color: "text-blue-600 dark:text-cerberus-cyan",
      borderColor: "border-blue-400 dark:border-cerberus-cyan/40",
      glowColor: "shadow-glow-cyan",
      bgLight: "bg-blue-50 dark:bg-cerberus-cyan/10"
    },
    { 
      code: "CONFLICT-02",
      title: "Conflict Detection", 
      desc: "Autonomous cross-examination uncovering temporal, valuation, and physical discrepancies across sources.", 
      metricTarget: 0,
      metricText: "Zero-Tolerance Clash",
      icon: GitFork, 
      color: "text-rose-600 dark:text-cerberus-red",
      borderColor: "border-rose-400 dark:border-cerberus-red/40",
      glowColor: "shadow-glow-red",
      bgLight: "bg-rose-50 dark:bg-cerberus-red/10"
    },
    { 
      code: "TRUST-03",
      title: "Source Reliability", 
      desc: "Cryptographic provenance tracking and consistency scoring without fabricating artificial trust metrics.", 
      metricTarget: 100,
      metricSuffix: "% Provenance Lineage",
      icon: ShieldCheck, 
      color: "text-amber-600 dark:text-cerberus-amber",
      borderColor: "border-amber-400 dark:border-cerberus-amber/40",
      glowColor: "shadow-glow-amber",
      bgLight: "bg-amber-50 dark:bg-cerberus-amber/10"
    },
    { 
      code: "REASON-04",
      title: "Traceable Verdicts", 
      desc: "Every conclusion links directly to exact source files, clause page numbers, spreadsheet rows, and OCR bounds.", 
      metricTarget: 4,
      metricSuffix: "-Tier Verified",
      icon: BrainCircuit, 
      color: "text-emerald-600 dark:text-cerberus-green",
      borderColor: "border-emerald-400 dark:border-cerberus-green/40",
      glowColor: "shadow-glass",
      bgLight: "bg-emerald-50 dark:bg-cerberus-green/10"
    }
  ];

  const featuresList = [
    {
      code: "PIPELINE-A",
      title: "Multimodal Ingestion",
      desc: "Direct parsing of official PDF declarations, satellite berth imagery, commercial invoices, and ERP database dumps.",
      icon: Layers,
      color: "text-blue-600 dark:text-cerberus-cyan",
      tag: "STAGE 1 INGEST"
    },
    {
      code: "PIPELINE-B",
      title: "Knowledge Graph Construction",
      desc: "Autonomously builds connected topological graphs linking entities, dates, dollar valuations, and relation edges.",
      icon: Network,
      color: "text-cyan-600 dark:text-cerberus-cyan",
      tag: "TOPOLOGY GRAPH"
    },
    {
      code: "PIPELINE-C",
      title: "Cross-Source Entity Resolution",
      desc: "Unifies alias variations, serial identifiers, vessel callsigns, and company tax registrations across files.",
      icon: Crosshair,
      color: "text-amber-600 dark:text-cerberus-gold",
      tag: "DISAMBIGUATION"
    },
    {
      code: "PIPELINE-D",
      title: "Contradiction Detection Lab",
      desc: "Zero-tolerance detection for conflicting claims. Never assumes a statement is true simply because it appears more often.",
      icon: GitFork,
      color: "text-rose-600 dark:text-cerberus-red",
      tag: "CROSS-EXAMINATION"
    },
    {
      code: "PIPELINE-E",
      title: "Source Reliability Analysis",
      desc: "Audits source origin, completeness, internal consistency, and independent corroboration with clear explanations.",
      icon: ShieldCheck,
      color: "text-emerald-600 dark:text-cerberus-green",
      tag: "TRUST PROVENANCE"
    },
    {
      code: "PIPELINE-F",
      title: "Adversarial Content Scanner",
      desc: "Detects suspicious metadata timestamps, resampled OCR typography, and embedded adversarial prompt injections.",
      icon: AlertTriangle,
      color: "text-amber-600 dark:text-cerberus-amber",
      tag: "RED FLAG SCANNER"
    },
    {
      code: "PIPELINE-G",
      title: "Conflict-Aware Neural Reasoning",
      desc: "Produces 3 primary decision states: SUPPORTED, CONFLICTED, or INSUFFICIENT evidence, plus MANIPULATION flags.",
      icon: BrainCircuit,
      color: "text-blue-600 dark:text-cerberus-cyan",
      tag: "VERIFICATION TREE"
    },
    {
      code: "PIPELINE-H",
      title: "Traceable Answer Studio",
      desc: "Generates forensic investigation answers with expandable citations linked to exact document pages and spreadsheet rows.",
      icon: FileSearch,
      color: "text-indigo-600 dark:text-cerberus-cyan",
      tag: "TRACEABLE DOSSIER"
    }
  ];

  const supportedFormats = [
    { format: 'PDF', label: 'PDF Documents', desc: 'Customs C88 filings, contracts, sworn statements with clause & page coordinates', badge: 'SPATIAL OCR' },
    { format: 'JPG / JPEG', label: 'Scanned Records', desc: 'Commercial supplier invoices, VAT stamped records, historical physical filings', badge: 'TYPOGRAPHY' },
    { format: 'PNG', label: 'Optical Imagery', desc: 'High-res dock telemetry, satellite berth captures, EXIF timestamp verification', badge: 'BOUNDING BOX' },
    { format: 'XLSX / XLS', label: 'Spreadsheet Ledgers', desc: 'Multi-sheet enterprise ERP dumps, container manifests, billable item matrices', badge: 'MULTI-SHEET' },
    { format: 'CSV', label: 'Structured Datasets', desc: 'Municipal harbor pilot logs, gatehouse logs, automated sensor telemetry streams', badge: 'ROW LINEAGE' },
  ];

  const workflowSteps = [
    { step: '01', title: 'Upload Evidence', role: 'Heterogeneous Ingest' },
    { step: '02', title: 'Extract Information', role: 'OCR & Tabular Parser' },
    { step: '03', title: 'Identify Entities', role: 'Cross-Modal Matching' },
    { step: '04', title: 'Build Knowledge Graph', role: 'Topological Edges' },
    { step: '05', title: 'Detect Conflicts', role: 'Contradiction Lab' },
    { step: '06', title: 'Evaluate Reliability', role: 'Trust & Authenticity' },
    { step: '07', title: 'Generate Traceable Verdict', role: 'Neural Verification' },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : 0.08,
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 25 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.5, ease: [0.25, 0.1, 0.25, 1.0] }
    }
  };

  return (
    <div className="space-y-16 pb-20 -mt-6">
      
      {/* 
        ====================================================================
        1. HERO BACKGROUND CAROUSEL (Inspired by GM University Presentation)
        - Full-screen cinematic slides with Ken Burns zoom effect
        - Unobstructed three-headed robot visual identity
        - Staggered headline, tagline, and CTA animations
        - Previous/Next navigation arrows & bottom pill indicators
        - Autoplay with progress indicator & pause-on-hover
        - Keyboard arrow key navigation
        ====================================================================
      */}
      <HeroCarousel 
        onInitialize={() => setActiveTab('dashboard')}
        onExplore={handleScrollToFeatures}
      />

      {/* 
        ====================================================================
        2 & 3. CONTRASTING PLATFORM ARCHITECTURE ZONE
        - Staggered scroll animations & animated counters
        - High contrast in both light & dark themes
        ====================================================================
      */}
      <div className="bg-slate-100/90 dark:bg-[#070D1A] py-16 px-4 sm:px-6 lg:px-8 rounded-3xl border border-slate-300/80 dark:border-cerberus-border/80 shadow-inner max-w-7xl mx-auto space-y-16 transition-colors">
        
        {/* Section 2: 4 Feature Indicators with Animated Counters */}
        <motion.section
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-60px" }}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {featureIndicators.map((ind, idx) => {
              const Icon = ind.icon;
              return (
                <motion.div 
                  key={idx}
                  variants={itemVariants}
                  whileHover={shouldReduceMotion ? {} : { y: -4, transition: { duration: 0.2 } }}
                  className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-border hover:border-blue-500 dark:hover:border-cerberus-cyan/50 shadow-md hover:shadow-xl transition-all duration-300 flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 dark:text-cerberus-muted">
                        {ind.code}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-100 dark:bg-cerberus-bg-secondary text-slate-800 dark:text-cerberus-cyan border border-slate-200 dark:border-cerberus-border">
                        {ind.metricTarget !== undefined && ind.metricTarget > 0 ? (
                          <AnimatedCounter to={ind.metricTarget} suffix={ind.metricSuffix || ''} />
                        ) : (
                          ind.metricText || "Zero-Tolerance Clash"
                        )}
                      </span>
                    </div>

                    <div className="flex items-start gap-3.5 mb-2">
                      <div className={`p-2.5 rounded-xl border ${ind.borderColor} ${ind.bgLight} shrink-0 group-hover:scale-105 transition-transform`}>
                        <Icon className={`w-5 h-5 ${ind.color}`} />
                      </div>
                      <div>
                        <h3 className="font-display font-bold text-sm sm:text-base text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-cerberus-cyan transition-colors">
                          {ind.title}
                        </h3>
                      </div>
                    </div>

                    <p className="text-xs text-slate-700 dark:text-cerberus-muted font-sans leading-relaxed mt-2 font-medium">
                      {ind.desc}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.section>

        {/* Section 3: Autonomous Multimodal Intelligence (Full High-Contrast Typography & Staggered Reveal) */}
        <motion.section 
          id="features-section"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-blue-100 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-300 dark:border-cerberus-cyan/30 text-xs font-mono font-bold mb-3 uppercase tracking-wider">
              <Zap className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-cyan" />
              CORE CAPABILITY ARCHITECTURE
            </div>
            
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 dark:text-white font-display tracking-tight">
              Autonomous Multimodal Intelligence
            </h2>
            
            <p className="text-sm sm:text-base text-slate-700 dark:text-slate-300 max-w-2xl mx-auto mt-2.5 font-sans font-medium">
              Engineered to overcome modality bias, detect forged claims, and reconcile conflicting records across complex investigations.
            </p>
          </div>

          <motion.div 
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-60px" }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {featuresList.map((feat, idx) => {
              const Icon = feat.icon;
              return (
                <motion.div
                  key={idx}
                  variants={itemVariants}
                  whileHover={shouldReduceMotion ? {} : { y: -4, transition: { duration: 0.2 } }}
                  className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-border hover:border-blue-500 dark:hover:border-cerberus-border-light shadow-md hover:shadow-xl transition-all duration-300 flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-11 h-11 rounded-xl bg-slate-100 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border flex items-center justify-center group-hover:scale-105 transition-transform">
                        <Icon className={`w-5 h-5 ${feat.color}`} />
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-cerberus-bg-secondary text-slate-700 dark:text-cerberus-muted border border-slate-200 dark:border-cerberus-border font-bold">
                        {feat.tag}
                      </span>
                    </div>

                    <h3 className="font-display font-bold text-sm sm:text-base text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-cerberus-cyan transition-colors mb-2">
                      {feat.title}
                    </h3>

                    <p className="text-xs text-slate-700 dark:text-cerberus-muted font-sans leading-relaxed font-medium">
                      {feat.desc}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-200 dark:border-cerberus-border/60 flex items-center justify-between text-[10px] font-mono text-slate-500 dark:text-cerberus-dark-muted font-semibold">
                    <span>{feat.code}</span>
                    <span className="text-blue-600 dark:text-cerberus-cyan font-bold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                      Inspect &rarr;
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </motion.section>

      </div>

      {/* 
        ====================================================================
        SECTION 4: Supported Forensic Evidence Formats (Spacious & Polished)
        ====================================================================
      */}
      <motion.section 
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.6 }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
      >
        <div className="p-8 sm:p-12 rounded-3xl bg-white dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-border shadow-xl">
          <div className="text-center mb-10">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan block mb-1">
              INPUT SPECIFICATION MATRIX
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display mt-1">
              Supported Forensic File Formats
            </h2>
            <p className="text-xs sm:text-sm text-slate-700 dark:text-cerberus-muted max-w-xl mx-auto mt-2 font-sans font-medium">
              PDF, JPG, PNG, XLSX, XLS, and CSV files are parsed with spatial coordinates, sheet tabs, and row IDs.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {supportedFormats.map((fmt, idx) => (
              <motion.div 
                key={idx}
                whileHover={shouldReduceMotion ? {} : { scale: 1.02 }}
                className="p-5 rounded-2xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border flex flex-col justify-between hover:border-blue-500 dark:hover:border-cerberus-cyan/50 transition-colors shadow-sm"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-display font-bold text-sm text-slate-900 dark:text-white">
                      {fmt.label}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white dark:bg-cerberus-card text-blue-700 dark:text-cerberus-cyan border border-slate-200 dark:border-cerberus-border font-bold">
                      {fmt.format}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-cerberus-muted font-sans leading-relaxed">
                    {fmt.desc}
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-slate-200 dark:border-cerberus-border/70 text-[10px] font-mono text-slate-600 dark:text-cerberus-cyan flex items-center justify-between">
                  <span>Parser: Normalized</span>
                  <span className="font-bold">{fmt.badge}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* 
        ====================================================================
        SECTION 5: Traceable 7-Stage Investigation Process Flow
        ====================================================================
      */}
      <motion.section 
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.6 }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
      >
        <div className="text-center mb-12">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan block mb-1">
            TRACEABLE INVESTIGATION PIPELINE
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display mt-1">
            How The Evidence Analysis Process Works
          </h2>
          <p className="text-xs sm:text-sm text-slate-700 dark:text-cerberus-muted max-w-xl mx-auto mt-2 font-sans font-medium">
            From raw multimodal upload to cross-modal contradiction detection and traceable verdict generation.
          </p>
        </div>

        {/* 7-Stage Flow with Subtle Stagger */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3.5">
          {workflowSteps.map((ws, idx) => (
            <motion.div 
              key={idx}
              whileHover={shouldReduceMotion ? {} : { y: -4, transition: { duration: 0.2 } }}
              className="p-5 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-300 dark:border-cerberus-border text-center flex flex-col justify-between relative group hover:border-blue-500 dark:hover:border-cerberus-cyan/50 shadow-sm hover:shadow-md transition-all"
            >
              <div>
                <span className="text-sm font-mono font-black text-blue-600 dark:text-cerberus-cyan block mb-1.5">
                  {ws.step}
                </span>
                <h4 className="font-display font-bold text-xs text-slate-900 dark:text-white mb-1">
                  {ws.title}
                </h4>
              </div>
              <span className="text-[10px] font-mono text-slate-600 dark:text-cerberus-muted block mt-3 pt-2 border-t border-slate-100 dark:border-cerberus-border/60">
                {ws.role}
              </span>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA Banner with subtle glow */}
        <motion.div 
          whileHover={shouldReduceMotion ? {} : { scale: 1.01 }}
          className="mt-14 p-8 sm:p-10 rounded-3xl bg-gradient-to-r from-blue-700 via-indigo-700 to-blue-800 dark:from-cerberus-card dark:via-cerberus-bg-secondary dark:to-cerberus-card border border-blue-400/30 dark:border-cerberus-cyan/30 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-2xl text-white"
        >
          <div>
            <h3 className="font-display font-bold text-xl sm:text-2xl text-white">
              Ready to Inspect Cross-Modal Contradictions?
            </h3>
            <p className="text-xs sm:text-sm text-blue-100 dark:text-cerberus-muted mt-1.5 font-sans">
              Launch the Command Center to ingest evidence or explore pre-loaded Operation Boreas benchmark data.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => {
                setIsDemoMode(true);
                setActiveTab('dashboard');
              }}
              className="px-6 py-3.5 rounded-xl bg-white hover:bg-slate-100 text-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 dark:text-white font-mono text-xs sm:text-sm font-bold shadow-lg transition-all"
            >
              ENTER COMMAND CENTER &rarr;
            </button>
          </div>
        </motion.div>
      </motion.section>

    </div>
  );
};

export default LandingPage;
