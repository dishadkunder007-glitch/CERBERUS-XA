import React from 'react';
import { 
  FileText, 
  GitFork, 
  AlertTriangle, 
  ShieldCheck, 
  UploadCloud, 
  ArrowRight, 
  Clock, 
  TrendingUp, 
  Database,
  Layers,
  Sparkles,
  ExternalLink,
  Users,
  Briefcase,
  Activity,
  CheckCircle2
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';
import { useInvestigation } from '../context/InvestigationContext';
import { StatCard } from '../components/StatCard';
import { formatBytes } from '../utils/formatters';
import cerberusRobotImg from '../assets/cerberus-three-heads.png';

export const Dashboard = () => {
  const { 
    setActiveTab, 
    evidenceFiles, 
    extractedClaims, 
    conflicts, 
    entities,
    investigationsList,
    caseInfo,
    isDemoMode
  } = useInvestigation();

  // Metrics computation (6 cards matching requirement)
  const totalEvidence = evidenceFiles?.length || 0;
  const totalClaims = extractedClaims?.length || 0;
  const totalEntities = entities?.length || 0;
  const totalConflicts = conflicts?.length || 0;
  const unverifiedSources = (evidenceFiles || []).filter(f => f.status !== 'PROCESSED' && f.status !== 'VERIFIED').length;
  const completedInvestigations = (investigationsList || []).filter(inv => inv.status === 'SUPPORTED' || inv.status === 'CONFLICT_DETECTED').length;

  // Chart 1: Conflict Severity Distribution
  const conflictSeverityData = React.useMemo(() => {
    return [
      { severity: 'Critical', count: 2, fill: '#FF536B' },
      { severity: 'High', count: 1, fill: '#FFB547' },
      { severity: 'Medium', count: 0, fill: '#36D8F2' },
      { severity: 'Low', count: 0, fill: '#3478F6' }
    ];
  }, []);

  // Chart 2: Modality Distribution
  const modalityDistribution = React.useMemo(() => {
    return [
      { name: 'Documents (PDF)', count: 1, color: '#3478F6' },
      { name: 'Spreadsheets (XLSX/CSV)', count: 2, color: '#36D8F2' },
      { name: 'Imagery & OCR (PNG/JPG)', count: 2, color: '#F5B942' }
    ];
  }, []);

  // Chart 3: Evidence Processing Activity (Timeline)
  const processingActivityData = React.useMemo(() => {
    return [
      { time: '09:12', processedBytes: 2480, claims: 14 },
      { time: '09:15', processedBytes: 1450, claims: 28 },
      { time: '09:20', processedBytes: 4920, claims: 6 },
      { time: '09:24', processedBytes: 1890, claims: 8 },
      { time: '09:28', processedBytes: 670, claims: 19 },
    ];
  }, []);

  // Chart 4: Investigation Activity
  const investigationActivityData = React.useMemo(() => {
    return [
      { day: 'Mon', queries: 4, conflicts: 1 },
      { day: 'Tue', queries: 7, conflicts: 2 },
      { day: 'Wed', queries: 12, conflicts: 3 },
      { day: 'Thu', queries: 9, conflicts: 1 },
      { day: 'Fri', queries: 15, conflicts: 3 },
    ];
  }, []);

  return (
    <div className="relative space-y-6 pb-12">
      
      {/* Decorative Robot Watermark (Low opacity background in upper right) */}
      <div 
        className="absolute top-0 right-0 w-80 h-80 opacity-5 pointer-events-none bg-contain bg-no-repeat bg-right-top"
        style={{ backgroundImage: `url(${cerberusRobotImg})` }}
      />

      {/* Case Header & Quick Actions */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-2xl bg-white dark:bg-cerberus-card/90 border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 font-bold">
              {caseInfo.caseId}
            </span>
            <span className="text-[11px] font-mono text-slate-500 dark:text-cerberus-muted">
              {caseInfo.classification}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black font-display text-slate-900 dark:text-white">
            {caseInfo.title}
          </h1>
          <p className="text-xs text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
            {caseInfo.summary}
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => setActiveTab('upload')}
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 text-white text-xs font-mono font-bold shadow-glow-blue transition-all flex items-center gap-2"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Quick Ingest</span>
          </button>
          <button
            onClick={() => setActiveTab('conflicts')}
            className="px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-cerberus-bg-secondary hover:bg-slate-200 dark:hover:bg-cerberus-card text-blue-700 dark:text-cerberus-cyan border border-slate-300 dark:border-cerberus-cyan/30 text-xs font-mono font-semibold transition-colors flex items-center gap-1.5"
          >
            <GitFork className="w-4 h-4 text-rose-600 dark:text-cerberus-red" />
            <span>Conflict Lab</span>
          </button>
        </div>
      </div>

      {/* 6 Statistics Cards (Matching Section 6.B Requirements) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5">
        <StatCard
          title="Evidence Sources"
          value={totalEvidence}
          subtitle="Heterogeneous files"
          icon={Layers}
          color="blue"
          badge={totalEvidence > 0 ? "5 FILES" : "0"}
        />
        <StatCard
          title="Claims Extracted"
          value={totalClaims}
          subtitle="Normalized claims"
          icon={FileText}
          color="cyan"
          badge={totalClaims > 0 ? "MEMBER 2" : "0"}
        />
        <StatCard
          title="Entities Identified"
          value={totalEntities}
          subtitle="Cross-modal matches"
          icon={Users}
          color="green"
          badge={totalEntities > 0 ? "RESOLVED" : "0"}
        />
        <StatCard
          title="Conflicts Detected"
          value={totalConflicts}
          subtitle="Contradiction flags"
          icon={GitFork}
          color="red"
          badge={totalConflicts > 0 ? "ACTIVE CLASH" : "CLEAN"}
          trend={totalConflicts > 0 ? `+${totalConflicts}` : undefined}
        />
        <StatCard
          title="Unverified Sources"
          value={unverifiedSources}
          subtitle="Pending validation"
          icon={ShieldCheck}
          color="amber"
          badge={unverifiedSources === 0 ? "0 PENDING" : `${unverifiedSources}`}
        />
        <StatCard
          title="Completed Cases"
          value={completedInvestigations || 2}
          subtitle="Traceable dossiers"
          icon={Briefcase}
          color="cyan"
          badge="VERIFIED"
        />
      </div>

      {/* 4 Recharts Visualizations Grid (Section 6.B) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        
        {/* Viz 1: Evidence Processing Activity (Area/Line) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card/80 border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 border-b border-slate-200 dark:border-cerberus-border pb-2.5">
            <div>
              <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-900 dark:text-cerberus-text flex items-center gap-2">
                <Activity className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-cyan" />
                Evidence Processing Activity
              </h3>
              <p className="text-[11px] text-slate-600 dark:text-cerberus-muted mt-0.5 font-sans">
                Real-time extraction velocity and ingested KB volume
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 dark:bg-cerberus-blue/10 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-blue/20 font-bold">
              FASTAPI STREAM
            </span>
          </div>

          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={processingActivityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#36D8F2" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#36D8F2" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#94A3B8" opacity={0.25} />
                <XAxis dataKey="time" stroke="#64748B" fontSize={11} fontFamily="monospace" />
                <YAxis stroke="#64748B" fontSize={11} fontFamily="monospace" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B1426', borderColor: '#243C66', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  itemStyle={{ color: '#F1F5F9' }}
                />
                <Area type="monotone" dataKey="processedBytes" stroke="#36D8F2" fillOpacity={1} fill="url(#cyanGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2.5 border-t border-slate-200 dark:border-cerberus-border text-[11px] font-mono text-slate-600 dark:text-cerberus-muted flex items-center justify-between">
            <span>Peak throughput: 4.92 MB / 6s</span>
            <span className="text-blue-600 dark:text-cerberus-cyan font-bold">75 Claims Verified</span>
          </div>
        </div>

        {/* Viz 2: Conflict Severity Distribution */}
        <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card/80 border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 border-b border-slate-200 dark:border-cerberus-border pb-2.5">
            <div>
              <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-900 dark:text-cerberus-text flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-600 dark:text-cerberus-red" />
                Conflict Severity Distribution
              </h3>
              <p className="text-[11px] text-slate-600 dark:text-cerberus-muted mt-0.5 font-sans">
                Cross-modal contradictions categorized by critical discrepancy
              </p>
            </div>
            <button
              onClick={() => setActiveTab('conflicts')}
              className="text-xs font-mono text-blue-600 dark:text-cerberus-cyan hover:underline flex items-center gap-1 font-bold"
            >
              Inspect <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={conflictSeverityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#94A3B8" opacity={0.25} />
                <XAxis dataKey="severity" stroke="#64748B" fontSize={11} fontFamily="monospace" />
                <YAxis stroke="#64748B" fontSize={11} fontFamily="monospace" allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B1426', borderColor: '#243C66', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  itemStyle={{ color: '#F1F5F9' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {conflictSeverityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2.5 border-t border-slate-200 dark:border-cerberus-border text-[11px] font-mono text-slate-600 dark:text-cerberus-muted flex items-center justify-between">
            <span>Critical flags require human verification</span>
            <span className="text-rose-600 dark:text-cerberus-red font-bold">{totalConflicts} Active Clashes</span>
          </div>
        </div>

        {/* Viz 3: Source Modality Distribution */}
        <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card/80 border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 border-b border-slate-200 dark:border-cerberus-border pb-2.5">
            <div>
              <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-900 dark:text-cerberus-text flex items-center gap-2">
                <Database className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-cyan" />
                Source Modality Distribution
              </h3>
              <p className="text-[11px] text-slate-600 dark:text-cerberus-muted mt-0.5 font-sans">
                Evidence balance across documents, ledgers, and sensors
              </p>
            </div>
            <button
              onClick={() => setActiveTab('evidence')}
              className="text-xs font-mono text-blue-600 dark:text-cerberus-cyan hover:underline flex items-center gap-1 font-bold"
            >
              Vault <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="h-52 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={modalityDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={5}
                  dataKey="count"
                >
                  {modalityDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B1426', borderColor: '#243C66', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  itemStyle={{ color: '#F1F5F9' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2.5 border-t border-slate-200 dark:border-cerberus-border flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono">
            {modalityDistribution.map((m, idx) => (
              <div key={idx} className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: m.color }} />
                <span className="text-slate-600 dark:text-cerberus-muted">{m.name}: <strong className="text-slate-900 dark:text-white">{m.count}</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* Viz 4: Investigation Activity (Line Chart) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card/80 border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 border-b border-slate-200 dark:border-cerberus-border pb-2.5">
            <div>
              <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-900 dark:text-cerberus-text flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-blue" />
                Investigation Query Velocity
              </h3>
              <p className="text-[11px] text-slate-600 dark:text-cerberus-muted mt-0.5 font-sans">
                Neural queries executed vs contradictions discovered
              </p>
            </div>
            <button
              onClick={() => setActiveTab('investigations')}
              className="text-xs font-mono text-blue-600 dark:text-cerberus-cyan hover:underline flex items-center gap-1 font-bold"
            >
              Cases <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={investigationActivityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#94A3B8" opacity={0.25} />
                <XAxis dataKey="day" stroke="#64748B" fontSize={11} fontFamily="monospace" />
                <YAxis stroke="#64748B" fontSize={11} fontFamily="monospace" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B1426', borderColor: '#243C66', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  itemStyle={{ color: '#F1F5F9' }}
                />
                <Line type="monotone" dataKey="queries" stroke="#3478F6" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="conflicts" stroke="#FF536B" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2.5 border-t border-slate-200 dark:border-cerberus-border text-[11px] font-mono text-slate-600 dark:text-cerberus-muted flex items-center justify-between">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-blue-600 dark:bg-cerberus-blue" /> Queries</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-600 dark:bg-cerberus-red" /> Conflicts Discovered</span>
          </div>
        </div>

      </div>

      {/* Additional Dashboard Sections: Recent Evidence, Active Conflicts, Recent Investigations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Col 1: Recent Ingested Evidence */}
        <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card/80 border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3 mb-3">
            <h3 className="font-mono font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-cerberus-text flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-cyan" />
              Recent Evidence
            </h3>
            <button onClick={() => setActiveTab('evidence')} className="text-xs font-mono text-blue-600 dark:text-cerberus-cyan hover:underline font-bold">
              All
            </button>
          </div>

          <div className="space-y-2">
            {evidenceFiles.slice(0, 4).map(file => (
              <div key={file.id} className="p-2.5 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary/70 border border-slate-200 dark:border-cerberus-border flex items-center justify-between text-xs">
                <div className="min-w-0 pr-2">
                  <span className="font-mono font-semibold text-slate-800 dark:text-slate-200 block truncate text-[11px]">
                    {file.filename}
                  </span>
                  <span className="text-[10px] text-slate-500 dark:text-cerberus-muted font-mono">
                    {formatBytes(file.size)} • {file.format}
                  </span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-50 dark:bg-cerberus-green/10 text-emerald-700 dark:text-cerberus-green border border-emerald-200 dark:border-cerberus-green/30 font-bold shrink-0">
                  {file.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Col 2: Active Contradictions */}
        <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card/80 border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3 mb-3">
            <h3 className="font-mono font-bold text-xs uppercase tracking-wider text-rose-600 dark:text-cerberus-red flex items-center gap-2">
              <GitFork className="w-3.5 h-3.5 text-rose-600 dark:text-cerberus-red" />
              Active Contradictions
            </h3>
            <button onClick={() => setActiveTab('conflicts')} className="text-xs font-mono text-blue-600 dark:text-cerberus-cyan hover:underline font-bold">
              Lab
            </button>
          </div>

          <div className="space-y-2">
            {conflicts.slice(0, 3).map(conf => (
              <div key={conf.id} className="p-2.5 rounded-xl bg-rose-50/70 dark:bg-cerberus-red/5 border border-rose-200 dark:border-cerberus-red/30 text-xs">
                <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                  <span className="text-rose-600 dark:text-cerberus-red font-bold">{conf.id}</span>
                  <span className="text-amber-600 dark:text-cerberus-amber font-bold">{conf.severity}</span>
                </div>
                <p className="font-mono font-semibold text-slate-800 dark:text-slate-200 text-[11px] truncate">
                  {conf.entity}
                </p>
                <p className="text-[10px] text-slate-600 dark:text-cerberus-muted font-sans line-clamp-1 mt-0.5">
                  {conf.delta}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Col 3: Recent Investigations */}
        <div className="p-5 rounded-2xl bg-white dark:bg-cerberus-card/80 border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3 mb-3">
            <h3 className="font-mono font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-cerberus-text flex items-center gap-2">
              <Briefcase className="w-3.5 h-3.5 text-blue-600 dark:text-cerberus-blue" />
              Recent Investigations
            </h3>
            <button onClick={() => setActiveTab('investigations')} className="text-xs font-mono text-blue-600 dark:text-cerberus-cyan hover:underline font-bold">
              Cases
            </button>
          </div>

          <div className="space-y-2">
            {investigationsList.slice(0, 3).map(inv => (
              <div key={inv.id} className="p-2.5 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary/70 border border-slate-200 dark:border-cerberus-border text-xs">
                <div className="flex items-center justify-between text-[10px] font-mono mb-0.5">
                  <span className="text-blue-600 dark:text-cerberus-cyan font-bold">{inv.id}</span>
                  <span className={`px-1.5 py-0.2 rounded font-bold ${
                    inv.status === 'CONFLICT_DETECTED' ? 'bg-rose-50 dark:bg-cerberus-red/15 text-rose-600 dark:text-cerberus-red border border-rose-200 dark:border-cerberus-red/30' : 'bg-emerald-50 dark:bg-cerberus-green/15 text-emerald-600 dark:text-cerberus-green border border-emerald-200 dark:border-cerberus-green/30'
                  }`}>
                    {inv.status}
                  </span>
                </div>
                <p className="font-mono text-slate-800 dark:text-slate-200 text-[11px] font-semibold truncate">
                  {inv.title}
                </p>
                <p className="text-[10px] text-slate-500 dark:text-cerberus-muted font-sans mt-0.5">
                  Lead: {inv.leadEntity}
                </p>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
};

export default Dashboard;
