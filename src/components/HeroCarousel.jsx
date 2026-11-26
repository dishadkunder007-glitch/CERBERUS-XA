import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { 
  ArrowRight, 
  ChevronLeft, 
  ChevronRight, 
  ChevronDown, 
  Terminal, 
  Layers, 
  Network, 
  GitFork, 
  ShieldCheck, 
  BrainCircuit, 
  Zap, 
  Pause, 
  Play 
} from 'lucide-react';
import cerberusRobotImg from '../assets/cerberus-three-heads.png';

const SLIDE_DURATION = 7000; // 7 seconds per slide

export const HeroCarousel = ({ onInitialize, onExplore }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [direction, setDirection] = useState(1);
  const [isPaused, setIsPaused] = useState(false);
  const [progress, setProgress] = useState(0);
  const shouldReduceMotion = useReducedMotion();
  const carouselRef = useRef(null);

  const slides = [
    {
      id: 'sentinel',
      badge: 'MULTIMODAL INTELLIGENCE GUARDIAN | CERBERUS-XA',
      badgeIcon: Zap,
      titlePrefix: 'CERBERUS',
      titleAccent: '-XA',
      tagline: '"Where Every Modality Can Contradict the Others."',
      description: 'Connecting evidence, challenging contradictions and discovering what can actually be trusted.',
      philosophy: '"Every Source Has a Voice. Every Claim Faces Verification."',
      accentGradient: 'from-cyan-400 via-blue-400 to-indigo-400',
      taglineColor: 'text-cyan-200 dark:text-cyan-300',
      telemetry: ['3 Ingestion Engines', 'Zero-Bias Parser', 'SHA-256 Provenance Hashing', 'Offline Capable'],
      overlayEffect: 'radial-cyan'
    },
    {
      id: 'topology',
      badge: 'TOPOLOGICAL EVIDENCE GRAPH | STAGE 02',
      badgeIcon: Network,
      titlePrefix: 'EVIDENCE',
      titleAccent: ' GRAPH',
      tagline: '"Unifying Disparate Data Streams into Connected Truth."',
      description: 'Autonomously maps cross-source entity coordinates, resolving conflicting dates, valuations, and identities across documents, spreadsheets, and optical telemetry.',
      philosophy: '"Heterogeneous Modalities Unified Across Topological Edges."',
      accentGradient: 'from-blue-400 via-cyan-300 to-emerald-400',
      taglineColor: 'text-blue-200 dark:text-cyan-200',
      telemetry: ['Entity Resolution', 'Cross-Modal Matching', 'Topological Edges', 'Multi-Relational Graph'],
      overlayEffect: 'radial-blue'
    },
    {
      id: 'conflict',
      badge: 'CONTRADICTION LAB & REASONING | STAGE 03',
      badgeIcon: GitFork,
      titlePrefix: 'CONFLICT',
      titleAccent: ' ENGINE',
      tagline: '"Zero Tolerance for Fabricated Claims. Every Verdict Traceable."',
      description: 'Cross-examines claims across independent sources without majority bias. Delivers auditable verdicts with direct page, row, and bounding box citations.',
      philosophy: '"Majority Consensus Never Guarantees Veracity."',
      accentGradient: 'from-amber-400 via-rose-400 to-cyan-400',
      taglineColor: 'text-amber-200 dark:text-amber-300',
      telemetry: ['4-Tier Verified Verdicts', 'Page & Row Citations', 'Temporal Discrepancy Check', 'Zero Bias'],
      overlayEffect: 'radial-amber'
    }
  ];

  const totalSlides = slides.length;

  const goToSlide = useCallback((index, newDirection = 1) => {
    setDirection(newDirection);
    setCurrentSlide(index);
    setProgress(0);
  }, []);

  const handleNext = useCallback(() => {
    setDirection(1);
    setCurrentSlide((prev) => (prev + 1) % totalSlides);
    setProgress(0);
  }, [totalSlides]);

  const handlePrev = useCallback(() => {
    setDirection(-1);
    setCurrentSlide((prev) => (prev - 1 + totalSlides) % totalSlides);
    setProgress(0);
  }, [totalSlides]);

  // Autoplay timer with progress bar
  useEffect(() => {
    if (isPaused) return;

    const intervalTime = 50; // Update progress bar every 50ms
    const step = (intervalTime / SLIDE_DURATION) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          handleNext();
          return 0;
        }
        return prev + step;
      });
    }, intervalTime);

    return () => clearInterval(timer);
  }, [isPaused, handleNext]);

  // Keyboard Navigation: Arrow Left / Right
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft') {
        handlePrev();
      } else if (e.key === 'ArrowRight') {
        handleNext();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlePrev, handleNext]);

  const activeSlideData = slides[currentSlide];
  const BadgeIcon = activeSlideData.badgeIcon;

  // Animation variants
  const slideVariants = {
    enter: (dir) => ({
      opacity: 0,
      x: shouldReduceMotion ? 0 : dir > 0 ? 50 : -50,
      scale: 1
    }),
    center: {
      opacity: 1,
      x: 0,
      scale: shouldReduceMotion ? 1 : 1.04,
      transition: {
        opacity: { duration: 0.7, ease: 'easeOut' },
        x: { duration: 0.7, ease: 'easeOut' },
        scale: { duration: 7, ease: 'linear' }
      }
    },
    exit: (dir) => ({
      opacity: 0,
      x: shouldReduceMotion ? 0 : dir > 0 ? -50 : 50,
      transition: {
        opacity: { duration: 0.5 },
        x: { duration: 0.5 }
      }
    })
  };

  const textContainerVariants = {
    initial: {},
    animate: {
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : 0.12,
        delayChildren: shouldReduceMotion ? 0 : 0.15
      }
    }
  };

  const textItemVariants = {
    initial: { opacity: 0, y: shouldReduceMotion ? 0 : 20 },
    animate: { 
      opacity: 1, 
      y: 0, 
      transition: { duration: 0.55, ease: [0.25, 0.1, 0.25, 1.0] } 
    }
  };

  return (
    <section 
      ref={carouselRef}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      className="relative min-h-[84vh] lg:min-h-[90vh] flex flex-col justify-between overflow-hidden border-b border-slate-300 dark:border-cerberus-border/70 py-10 lg:py-14 select-none"
      aria-label="CERBERUS-XA Intelligence Carousel"
    >
      {/* 
        ====================================================================
        SLIDE BACKGROUND & KEN BURNS ZOOM ANIMATION
        ====================================================================
      */}
      <AnimatePresence initial={false} custom={direction} mode="wait">
        <motion.div
          key={currentSlide}
          custom={direction}
          variants={slideVariants}
          initial="enter"
          animate="center"
          exit="exit"
          className="absolute inset-0 bg-cover bg-no-repeat pointer-events-none"
          style={{
            backgroundImage: `url(${cerberusRobotImg})`,
            backgroundPosition: 'center 22%',
          }}
        />
      </AnimatePresence>

      {/* Atmospheric Scrim Overlays - Darkened top & bottom for 100% text legibility, center completely clear */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/85 via-slate-950/20 to-slate-950/90 pointer-events-none z-0" />
      <div className="absolute inset-0 bg-radial-vignette opacity-45 pointer-events-none z-0" />

      {/* Subtle dynamic overlay glow depending on active slide */}
      {activeSlideData.overlayEffect === 'radial-cyan' && (
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none transition-opacity duration-1000" />
      )}
      {activeSlideData.overlayEffect === 'radial-blue' && (
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-blue-500/15 rounded-full blur-3xl pointer-events-none transition-opacity duration-1000" />
      )}
      {activeSlideData.overlayEffect === 'radial-amber' && (
        <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-amber-500/15 rounded-full blur-3xl pointer-events-none transition-opacity duration-1000" />
      )}

      {/* 
        ====================================================================
        THIN AUTOPLAY PROGRESS BAR (Reference: GMU & Premium University sites)
        ====================================================================
      */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-slate-800/60 z-30 overflow-hidden">
        <motion.div 
          className="h-full bg-gradient-to-r from-blue-500 via-cyan-400 to-indigo-400"
          style={{ width: `${progress}%` }}
          transition={{ ease: 'linear' }}
        />
      </div>

      {/* 
        ====================================================================
        TOP ZONE: STAGGERED HEADLINE, BADGE & TAGLINE
        ====================================================================
      */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full pt-4 text-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentSlide}
            variants={textContainerVariants}
            initial="initial"
            animate="animate"
            className="flex flex-col items-center"
          >
            {/* 1. Protocol Pill Badge */}
            <motion.div variants={textItemVariants} className="mb-4">
              <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-slate-950/85 backdrop-blur-md border border-cyan-400/40 text-xs font-mono text-cyan-300 shadow-lg">
                <BadgeIcon className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                <span className="tracking-widest uppercase font-bold">{activeSlideData.badge}</span>
              </div>
            </motion.div>

            {/* 2. Main Heading */}
            <motion.h1 
              variants={textItemVariants}
              className="text-4xl sm:text-6xl lg:text-7xl font-black font-display tracking-tight text-white drop-shadow-[0_4px_24px_rgba(0,0,0,0.95)]"
            >
              {activeSlideData.titlePrefix}
              <span className={`text-transparent bg-clip-text bg-gradient-to-r ${activeSlideData.accentGradient}`}>
                {activeSlideData.titleAccent}
              </span>
            </motion.h1>

            {/* 3. High-Contrast Tagline */}
            <motion.p 
              variants={textItemVariants}
              className={`mt-2.5 text-lg sm:text-2xl md:text-3xl font-bold font-sans italic ${activeSlideData.taglineColor} drop-shadow-[0_2px_12px_rgba(0,0,0,0.95)] max-w-3xl mx-auto leading-snug`}
            >
              {activeSlideData.tagline}
            </motion.p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* 
        ====================================================================
        MIDDLE ZONE: 100% UNOBSTRUCTED VIEW OF ALL THREE ROBOT HEADS!
        ====================================================================
      */}
      <div className="relative z-10 flex-1 min-h-[160px] sm:min-h-[200px]" />

      {/* 
        ====================================================================
        BOTTOM ZONE: FLOATING FROSTED COMMAND DOCK WITH ACTIONS
        ====================================================================
      */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full pb-2">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentSlide}
            variants={textContainerVariants}
            initial="initial"
            animate="animate"
            className="p-5 sm:p-7 rounded-3xl bg-slate-950/80 backdrop-blur-xl border border-slate-700/70 dark:border-cerberus-cyan/40 shadow-2xl flex flex-col lg:flex-row items-center justify-between gap-6"
          >
            {/* Description & Philosophy */}
            <motion.div variants={textItemVariants} className="space-y-2 text-center lg:text-left max-w-2xl">
              <p className="text-xs sm:text-sm text-slate-200 font-sans leading-relaxed">
                {activeSlideData.description}
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900/80 border border-slate-700 text-xs font-mono text-cyan-300 font-semibold">
                <Terminal className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span>{activeSlideData.philosophy}</span>
              </div>
            </motion.div>

            {/* Action Buttons */}
            <motion.div variants={textItemVariants} className="flex flex-wrap items-center justify-center gap-3.5 shrink-0">
              <button
                onClick={onInitialize}
                className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-mono text-xs sm:text-sm font-bold tracking-wider shadow-glow-cyan transition-all flex items-center gap-2.5 group"
              >
                <span>INITIALIZE INVESTIGATION</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              <button
                onClick={onExplore}
                className="px-5 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-600 hover:border-cyan-400 font-mono text-xs sm:text-sm font-semibold transition-all flex items-center gap-2"
              >
                <span>EXPLORE SYSTEM</span>
                <ChevronDown className="w-4 h-4 text-cyan-400 animate-bounce" />
              </button>
            </motion.div>
          </motion.div>
        </AnimatePresence>

        {/* Real-time Telemetry Indicators */}
        <div className="mt-3 flex flex-wrap items-center justify-center gap-4 text-[11px] font-mono text-slate-300 dark:text-cerberus-muted drop-shadow">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            {activeSlideData.telemetry[0]}
          </span>
          <span>•</span>
          <span>{activeSlideData.telemetry[1]}</span>
          <span>•</span>
          <span>{activeSlideData.telemetry[2]}</span>
          <span>•</span>
          <span>{activeSlideData.telemetry[3]}</span>
        </div>
      </div>

      {/* 
        ====================================================================
        NAVIGATION ARROWS: PREVIOUS & NEXT (GMU Presentation Style)
        ====================================================================
      */}
      <button
        onClick={handlePrev}
        aria-label="Previous Slide"
        className="absolute left-3 sm:left-6 top-1/2 -translate-y-1/2 z-20 w-11 h-11 sm:w-13 sm:h-13 rounded-full bg-slate-950/70 hover:bg-slate-900 text-white border border-slate-700/80 hover:border-cyan-400 backdrop-blur-md flex items-center justify-center shadow-xl hover:shadow-glow-cyan hover:scale-105 active:scale-95 transition-all group"
      >
        <ChevronLeft className="w-6 h-6 text-slate-300 group-hover:text-cyan-300 transition-colors" />
      </button>

      <button
        onClick={handleNext}
        aria-label="Next Slide"
        className="absolute right-3 sm:right-6 top-1/2 -translate-y-1/2 z-20 w-11 h-11 sm:w-13 sm:h-13 rounded-full bg-slate-950/70 hover:bg-slate-900 text-white border border-slate-700/80 hover:border-cyan-400 backdrop-blur-md flex items-center justify-center shadow-xl hover:shadow-glow-cyan hover:scale-105 active:scale-95 transition-all group"
      >
        <ChevronRight className="w-6 h-6 text-slate-300 group-hover:text-cyan-300 transition-colors" />
      </button>

      {/* 
        ====================================================================
        BOTTOM SLIDE INDICATORS & PLAY/PAUSE TOGGLE
        ====================================================================
      */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-slate-950/75 backdrop-blur-md border border-slate-800 text-xs">
        {slides.map((s, idx) => (
          <button
            key={s.id}
            onClick={() => goToSlide(idx, idx > currentSlide ? 1 : -1)}
            aria-label={`Go to slide ${idx + 1}`}
            className="group py-1"
          >
            <div 
              className={`h-1.5 rounded-full transition-all duration-300 ${
                currentSlide === idx 
                  ? 'w-7 bg-cyan-400 shadow-glow-cyan' 
                  : 'w-2 bg-slate-600 hover:bg-slate-400'
              }`}
            />
          </button>
        ))}

        <div className="h-3 w-px bg-slate-700 mx-1" />

        {/* Play/Pause Button */}
        <button
          onClick={() => setIsPaused(!isPaused)}
          className="text-slate-400 hover:text-cyan-300 transition-colors p-0.5"
          aria-label={isPaused ? "Play Carousel" : "Pause Carousel"}
          title={isPaused ? "Resume Autoplay" : "Pause Autoplay"}
        >
          {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
        </button>
      </div>

    </section>
  );
};

export default HeroCarousel;
