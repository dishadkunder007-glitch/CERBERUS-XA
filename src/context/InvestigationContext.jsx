import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  checkBackendHealth,
  processBatch,
  processFile,
  getExtractedClaims,
  getEvidenceFiles,
  deleteEvidenceFile,
  resetBackendSession,
} from '../services/evidenceService';
import {
  getConflictAnalysis
} from '../services/conflictService';
import {
  getKnowledgeGraphData
} from '../services/graphService';
import {
  submitInvestigationQuery,
  getInvestigationReport,
  getEntityResolutions,
  getReliabilityAnalysis,
  getAdversarialAnalysis,
  getAuditLogs,
  getInvestigationsHistory
} from '../services/investigationService';
import {
  DEMO_CASE_INFO,
  DEMO_INVESTIGATIONS_LIST,
  DEMO_EVIDENCE_FILES,
  DEMO_EXTRACTED_CLAIMS,
  DEMO_CONFLICTS,
  DEMO_ENTITIES,
  DEMO_ENTITY_RESOLUTIONS,
  DEMO_GRAPH_DATA,
  DEMO_RELIABILITY_RECORDS,
  DEMO_ADVERSARIAL_ALERTS,
  DEMO_INVESTIGATION_REPORT,
  DEMO_AUDIT_LOGS,
  DEMO_EVALUATION_METRICS
} from '../data/demoData';

const InvestigationContext = createContext(null);

export const InvestigationProvider = ({ children }) => {
  // Theme state: 'dark' | 'light'
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('cerberus-theme') || 'dark';
  });

  useEffect(() => {
    const root = document.documentElement;
    const body = document.body;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
      if (body) {
        body.classList.add('dark');
        body.classList.remove('light');
      }
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
      if (body) {
        body.classList.add('light');
        body.classList.remove('dark');
      }
    }
    localStorage.setItem('cerberus-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Navigation & View state (6 Primary Sections + Landing)
  const [activeTab, setActiveTabRaw] = useState('landing');
  const [subTabs, setSubTabs] = useState({
    'overview': 'dashboard',
    'evidence-center': 'vault',
    'knowledge-graph': 'graph',
    'conflict-trust': 'conflicts',
    'ai-investigation': 'answer-studio',
    'reports-audit': 'cases'
  });

  const setSubTab = useCallback((mainTab, subTab) => {
    setSubTabs(prev => ({
      ...prev,
      [mainTab]: subTab
    }));
  }, []);

  // Smart Navigation Handler: Maps legacy tab IDs to the 6 primary sections
  const setActiveTab = useCallback((tab, targetSubTab) => {
    switch (tab) {
      case 'landing':
        setActiveTabRaw('landing');
        break;

      case 'overview':
      case 'dashboard':
        setActiveTabRaw('overview');
        if (targetSubTab) setSubTab('overview', targetSubTab);
        break;

      case 'evidence-center':
        setActiveTabRaw('evidence-center');
        if (targetSubTab) setSubTab('evidence-center', targetSubTab);
        break;
      case 'evidence':
      case 'vault':
        setActiveTabRaw('evidence-center');
        setSubTab('evidence-center', 'vault');
        break;
      case 'upload':
      case 'ingest':
        setActiveTabRaw('evidence-center');
        setSubTab('evidence-center', 'upload');
        break;
      case 'modality':
        setActiveTabRaw('evidence-center');
        setSubTab('evidence-center', 'modality');
        break;

      case 'knowledge-graph':
        setActiveTabRaw('knowledge-graph');
        if (targetSubTab) setSubTab('knowledge-graph', targetSubTab);
        break;
      case 'graph':
        setActiveTabRaw('knowledge-graph');
        setSubTab('knowledge-graph', 'graph');
        break;
      case 'entity-resolution':
      case 'entities':
        setActiveTabRaw('knowledge-graph');
        setSubTab('knowledge-graph', 'entities');
        break;

      case 'conflict-trust':
        setActiveTabRaw('conflict-trust');
        if (targetSubTab) setSubTab('conflict-trust', targetSubTab);
        break;
      case 'conflicts':
        setActiveTabRaw('conflict-trust');
        setSubTab('conflict-trust', 'conflicts');
        break;
      case 'reliability':
        setActiveTabRaw('conflict-trust');
        setSubTab('conflict-trust', 'reliability');
        break;
      case 'adversarial':
        setActiveTabRaw('conflict-trust');
        setSubTab('conflict-trust', 'adversarial');
        break;

      case 'ai-investigation':
        setActiveTabRaw('ai-investigation');
        if (targetSubTab) setSubTab('ai-investigation', targetSubTab);
        break;
      case 'report':
      case 'answer-studio':
        setActiveTabRaw('ai-investigation');
        setSubTab('ai-investigation', 'answer-studio');
        break;
      case 'reasoning':
        setActiveTabRaw('ai-investigation');
        setSubTab('ai-investigation', 'reasoning');
        break;

      case 'reports-audit':
        setActiveTabRaw('reports-audit');
        if (targetSubTab) setSubTab('reports-audit', targetSubTab);
        break;
      case 'investigations':
      case 'cases':
        setActiveTabRaw('reports-audit');
        setSubTab('reports-audit', 'cases');
        break;
      case 'audit':
        setActiveTabRaw('reports-audit');
        setSubTab('reports-audit', 'audit');
        break;
      case 'settings':
        setActiveTabRaw('reports-audit');
        setSubTab('reports-audit', 'settings');
        break;

      default:
        setActiveTabRaw(tab);
        if (targetSubTab) {
          setSubTab(tab, targetSubTab);
        }
        break;
    }
  }, [setSubTab]);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);

  // Backend connectivity state
  const [backendStatus, setBackendStatus] = useState({
    checked: false,
    online: false,
    apiUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    details: null,
    error: null,
  });

  // Strict Demo Mode distinction:
  const [isDemoMode, setIsDemoMode] = useState(true);

  // Live Backend State
  const [liveFiles, setLiveFiles] = useState([]);
  const [liveClaims, setLiveClaims] = useState([]);
  const [liveConflicts, setLiveConflicts] = useState([]);
  const [liveGraph, setLiveGraph] = useState({ nodes: [], links: [] });
  const [liveReport, setLiveReport] = useState(null);
  const [liveEntities, setLiveEntities] = useState([]);
  const [liveResolutions, setLiveResolutions] = useState([]);
  const [liveReliability, setLiveReliability] = useState([]);
  const [liveAdversarial, setLiveAdversarial] = useState([]);
  const [liveInvestigations, setLiveInvestigations] = useState([]);
  const [liveAuditLogs, setLiveAuditLogs] = useState([]);

  // Processing & Error states
  const [processingState, setProcessingState] = useState({
    isUploading: false,
    isProcessing: false,
    progress: 0,
    statusText: '',
    error: null,
    successMessage: null,
  });

  // Active investigation query
  const [investigationQuery, setInvestigationQuery] = useState(
    "Did Nordic Freight Forwarding misrepresent shipment valuation, arrival dates, and cargo contents of Vessel MV Polaris to evade EU tariff duties?"
  );

  // Check backend health on mount
  const verifyBackend = useCallback(async () => {
    try {
      const health = await checkBackendHealth();
      const isOnline = Boolean(health.online);
      setBackendStatus({
        checked: true,
        online: isOnline,
        apiUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
        details: health.data || null,
        error: health.error || null,
      });
      return isOnline;
    } catch (err) {
      setBackendStatus({
        checked: true,
        online: false,
        apiUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
        details: null,
        error: err.message || 'Connection refused',
      });
      return false;
    }
  }, []);

  // Fetch live state from backend
  const refreshLiveData = useCallback(async () => {
    try {
      const [evidence, claims, conflicts, graph, resolutions, reliability, adversarial, audit, investigations] = await Promise.allSettled([
        getEvidenceFiles(),
        getExtractedClaims(),
        getConflictAnalysis(),
        getKnowledgeGraphData(),
        getEntityResolutions(),
        getReliabilityAnalysis(),
        getAdversarialAnalysis(),
        getAuditLogs(),
        getInvestigationsHistory()
      ]);

      if (evidence.status === 'fulfilled' && Array.isArray(evidence.value)) {
        setLiveFiles(evidence.value);
      }
      if (claims.status === 'fulfilled' && Array.isArray(claims.value)) {
        setLiveClaims(claims.value);
      }
      if (conflicts.status === 'fulfilled' && Array.isArray(conflicts.value)) {
        setLiveConflicts(conflicts.value);
      }
      if (graph.status === 'fulfilled' && graph.value?.nodes) {
        setLiveGraph(graph.value);
      }
      if (resolutions.status === 'fulfilled' && Array.isArray(resolutions.value) && resolutions.value.length > 0) {
        setLiveResolutions(resolutions.value);
        // Populate live entities from actual entity-resolution results
        const entityMap = new Map();
        resolutions.value.forEach((r) => {
          const canon = r.canonicalName || r.alias || 'Unknown Entity';
          if (!entityMap.has(canon)) {
            entityMap.set(canon, {
              id: r.id,
              name: canon,
              type: 'ORGANIZATION',
              aliases: r.alias && r.alias !== canon ? [r.alias] : [],
              sources: r.sources || [],
              confidence: r.confidence || 1.0,
              status: r.status || 'CANONICAL',
            });
          } else if (r.alias && r.alias !== canon) {
            const existing = entityMap.get(canon);
            if (!existing.aliases.includes(r.alias)) {
              existing.aliases.push(r.alias);
            }
          }
        });
        setLiveEntities(Array.from(entityMap.values()));
      }
      if (reliability.status === 'fulfilled' && Array.isArray(reliability.value) && reliability.value.length > 0) {
        setLiveReliability(reliability.value);
      }
      if (adversarial.status === 'fulfilled' && Array.isArray(adversarial.value) && adversarial.value.length > 0) {
        setLiveAdversarial(adversarial.value);
      }
      if (audit.status === 'fulfilled' && Array.isArray(audit.value) && audit.value.length > 0) {
        setLiveAuditLogs(audit.value);
      }
      if (investigations.status === 'fulfilled' && Array.isArray(investigations.value) && investigations.value.length > 0) {
        setLiveInvestigations(investigations.value);
      }
    } catch (err) {
      console.warn('Live data sync notice:', err);
    }
  }, []);

  useEffect(() => {
    verifyBackend().then(online => {
      if (online) {
        refreshLiveData();
      }
    });
  }, [verifyBackend, refreshLiveData]);

  // Upload and process files via FastAPI
  const handleUploadFiles = async (files) => {
    if (!files || files.length === 0) return;

    setProcessingState({
      isUploading: true,
      isProcessing: true,
      progress: 10,
      statusText: 'Transmitting evidence to FastAPI multimodal ingestion pipeline...',
      error: null,
      successMessage: null,
    });

    try {
      let response;
      if (files.length === 1) {
        response = await processFile(files[0], (pct) => {
          setProcessingState(prev => ({ ...prev, progress: Math.min(pct * 0.7, 70), statusText: `Uploading: ${pct}%` }));
        });
      } else {
        response = await processBatch(files, (pct) => {
          setProcessingState(prev => ({ ...prev, progress: Math.min(pct * 0.7, 70), statusText: `Batch uploading: ${pct}%` }));
        });
      }

      setProcessingState(prev => ({
        ...prev,
        progress: 85,
        statusText: 'Extracting cross-modal claims and constructing graph...'
      }));

      const newFiles = Array.from(files).map((f, idx) => ({
        id: `LIVE-EV-${Date.now()}-${idx}`,
        filename: f.name,
        size: f.size,
        format: f.name.split('.').pop().toUpperCase(),
        uploadTime: new Date().toISOString(),
        status: 'PROCESSED',
        backendResponse: response
      }));

      setLiveFiles(prev => [...newFiles, ...prev]);

      if (response && response.claims) {
        setLiveClaims(prev => [...response.claims, ...prev]);
      } else {
        try {
          const claimsData = await getExtractedClaims();
          if (claimsData && Array.isArray(claimsData)) setLiveClaims(claimsData);
        } catch { /* contract */ }
      }

      if (response && response.conflicts) {
        setLiveConflicts(response.conflicts);
      } else {
        try {
          const conflictsData = await getConflictAnalysis();
          if (conflictsData && Array.isArray(conflictsData)) setLiveConflicts(conflictsData);
        } catch { /* contract */ }
      }

      if (response && response.graph) {
        setLiveGraph(response.graph);
      } else {
        try {
          const graphData = await getKnowledgeGraphData();
          if (graphData && graphData.nodes) setLiveGraph(graphData);
        } catch { /* contract */ }
      }

      // Automatically switch to Live Mode so newly uploaded files are immediately visible
      setIsDemoMode(false);

      // Refresh all live backend data (including GET /evidence)
      await refreshLiveData();

      setProcessingState({
        isUploading: false,
        isProcessing: false,
        progress: 100,
        statusText: 'Completed',
        error: null,
        successMessage: `Successfully ingested and processed ${files.length} evidence file(s).`,
      });

    } catch (err) {
      console.error('Evidence upload error:', err);
      setProcessingState({
        isUploading: false,
        isProcessing: false,
        progress: 0,
        statusText: 'Failed',
        error: err.message || 'Backend upload failed. Ensure FastAPI is running on ' + (backendStatus.apiUrl || 'port 8000') + ' with CORS enabled.',
        successMessage: null,
      });
    }
  };

  // Run AI reasoning query
  const handleRunInvestigation = async (question) => {
    const q = question || investigationQuery;
    setProcessingState(prev => ({
      ...prev,
      isProcessing: true,
      statusText: 'Querying Member 4 neural reasoning engine...',
      error: null
    }));

    try {
      // Automatically switch to Live Mode so the user sees the real backend verdict
      setIsDemoMode(false);
      const response = await submitInvestigationQuery({ question: q });
      setLiveReport(response);

      // Append completed live investigation to session history without deleting previous entries
      if (response && (response.reportId || response.verdict || response.finalVerdict)) {
        const rawVerdict = response.verdict || response.finalVerdict || 'INSUFFICIENT_EVIDENCE';
        const statusStr = rawVerdict === 'ANSWERED' || rawVerdict === 'Supported by evidence'
          ? 'SUPPORTED'
          : (rawVerdict === 'CONFLICTED' || rawVerdict === 'Conflicting evidence'
            ? 'CONFLICT_DETECTED'
            : 'INSUFFICIENT_EVIDENCE');

        const newEntry = {
          id: response.reportId || `DOSSIER-${Date.now()}`,
          title: response.investigationQuestion || response.question || q,
          category: 'Live Cross-Modal Inquiry',
          status: statusStr,
          leadEntity: liveEntities[0]?.name || 'Uploaded Corpus',
          evidenceCount: liveFiles.length,
          claimsCount: liveClaims.length,
          verdict: response.finalVerdict || rawVerdict,
          confidence: response.verdictConfidence ?? 0,
          timestamp: response.timestamp || new Date().toISOString(),
          lastUpdated: response.timestamp || new Date().toISOString(),
          dossier: response
        };

        setLiveInvestigations(prev => {
          const filtered = prev.filter(item => item.id !== newEntry.id);
          return [newEntry, ...filtered];
        });
      }

      setProcessingState(prev => ({
        ...prev,
        isProcessing: false,
        statusText: 'Analysis complete',
        successMessage: 'Investigation reasoning report synthesized.'
      }));
      setActiveTab('ai-investigation', 'answer-studio');
    } catch (err) {
      console.error('Investigation error:', err);
      setProcessingState(prev => ({
        ...prev,
        isProcessing: false,
        error: err.message || 'Investigation query failed. Member 4 reasoning service unreachable.',
        statusText: 'Query failed'
      }));
    }
  };

  // Select a specific investigation dossier from history
  const selectInvestigationReport = useCallback((dossier) => {
    if (dossier) {
      setLiveReport(dossier);
    }
  }, []);

  // Delete a specific evidence file from the vault
  const handleDeleteEvidence = async (evidenceId) => {
    if (!isDemoMode && backendStatus.online) {
      try {
        await deleteEvidenceFile(evidenceId);
        await refreshLiveData();
      } catch (err) {
        console.error('Delete evidence error:', err);
        setProcessingState(prev => ({
          ...prev,
          error: err.message || 'Failed to delete evidence file.'
        }));
      }
    } else {
      setLiveFiles(prev => prev.filter(f => f.id !== evidenceId));
    }
  };

  // Clear live session data
  const handleClearSession = async () => {
    if (backendStatus.online) {
      try {
        await resetBackendSession();
      } catch (err) {
        console.warn('Backend reset warning:', err);
      }
    }
    setLiveFiles([]);
    setLiveClaims([]);
    setLiveConflicts([]);
    setLiveGraph({ nodes: [], links: [] });
    setLiveReport(null);
    setLiveEntities([]);
    setLiveResolutions([]);
    setLiveReliability([]);
    setLiveAdversarial([]);
    setLiveInvestigations([]);
    setLiveAuditLogs([]);
    setProcessingState({
      isUploading: false,
      isProcessing: false,
      progress: 0,
      statusText: '',
      error: null,
      successMessage: null
    });
  };

  const evidenceFiles = isDemoMode ? DEMO_EVIDENCE_FILES : liveFiles;
  const extractedClaims = isDemoMode ? DEMO_EXTRACTED_CLAIMS : liveClaims;
  const conflicts = isDemoMode ? DEMO_CONFLICTS : liveConflicts;
  const knowledgeGraph = isDemoMode ? DEMO_GRAPH_DATA : liveGraph;
  const investigationReport = isDemoMode ? DEMO_INVESTIGATION_REPORT : liveReport;
  const entities = isDemoMode ? DEMO_ENTITIES : liveEntities;
  const entityResolutions = isDemoMode ? DEMO_ENTITY_RESOLUTIONS : liveResolutions;
  const reliabilityRecords = isDemoMode ? DEMO_RELIABILITY_RECORDS : liveReliability;
  const adversarialAlerts = isDemoMode ? DEMO_ADVERSARIAL_ALERTS : liveAdversarial;
  const investigationsList = isDemoMode ? DEMO_INVESTIGATIONS_LIST : liveInvestigations;
  const auditLogs = isDemoMode ? DEMO_AUDIT_LOGS : liveAuditLogs;
  const evaluationMetrics = isDemoMode ? DEMO_EVALUATION_METRICS : null;

  const caseInfo = isDemoMode ? DEMO_CASE_INFO : {
    caseId: liveFiles.length > 0 ? "LIVE-SESSION-" + liveFiles[0]?.id : "NO-ACTIVE-CASE",
    title: liveFiles.length > 0 ? "Live Multimodal Evidence Session" : "No Active Case",
    classification: "OPERATIONAL // UNCLASSIFIED",
    leadAnalyst: "Forensic Analyst",
    createdDate: new Date().toISOString(),
    status: liveFiles.length > 0 ? "EVIDENCE_INGESTED" : "AWAITING_EVIDENCE",
    summary: liveFiles.length > 0 ? "Session loaded with real backend evidence files." : "Upload evidence files to begin analysis."
  };

  return (
    <InvestigationContext.Provider
      value={{
        theme,
        setTheme,
        toggleTheme,
        activeTab,
        setActiveTab,
        subTabs,
        setSubTab,
        sidebarCollapsed,
        setSidebarCollapsed,
        rightPanelOpen,
        setRightPanelOpen,
        backendStatus,
        verifyBackend,
        isDemoMode,
        setIsDemoMode,
        caseInfo,
        evidenceFiles,
        extractedClaims,
        conflicts,
        knowledgeGraph,
        investigationReport,
        entities,
        entityResolutions,
        reliabilityRecords,
        adversarialAlerts,
        investigationsList,
        auditLogs,
        evaluationMetrics,
        processingState,
        setProcessingState,
        investigationQuery,
        setInvestigationQuery,
        handleUploadFiles,
        handleRunInvestigation,
        handleDeleteEvidence,
        handleClearSession,
        selectInvestigationReport,
        refreshLiveData,
        liveFilesCount: liveFiles.length
      }}
    >
      {children}
    </InvestigationContext.Provider>
  );
};

export const useInvestigation = () => {
  const context = useContext(InvestigationContext);
  if (!context) {
    throw new Error('useInvestigation must be used within an InvestigationProvider');
  }
  return context;
};
