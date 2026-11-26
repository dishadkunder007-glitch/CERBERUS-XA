import React, { useState, useMemo } from 'react';
import {
  Database,
  Search,
  Filter,
  UploadCloud,
  Layers,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Table as TableIcon,
  Image as ImageIcon,
  CheckCircle2,
  X,
  Trash2
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';
import { formatBytes } from '../utils/formatters';
import { EmptyState } from '../components/EmptyState';

export const EvidencePage = () => {
  const {
    evidenceFiles,
    extractedClaims,
    conflicts,
    setActiveTab,
    isDemoMode,
    handleDeleteEvidence,
    handleClearSession
  } = useInvestigation();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedModality, setSelectedModality] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [sortBy, setSortBy] = useState('newest');
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  // Filter & Sort
  const filteredFiles = useMemo(() => {
    return evidenceFiles.filter(file => {
      const matchSearch = searchTerm === '' ||
        file.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        file.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        file.relatedEntities?.some(e => e.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchModality = selectedModality === 'ALL' || file.modality === selectedModality;
      const matchStatus = selectedStatus === 'ALL' || file.status === selectedStatus;

      return matchSearch && matchModality && matchStatus;
    }).sort((a, b) => {
      if (sortBy === 'name') return a.filename.localeCompare(b.filename);
      if (sortBy === 'size') return b.size - a.size;
      return new Date(b.uploadTime) - new Date(a.uploadTime);
    });
  }, [evidenceFiles, searchTerm, selectedModality, selectedStatus, sortBy]);

  const getFormatIcon = (modality) => {
    switch (modality) {
      case 'DOCUMENT': return <FileText className="w-4 h-4 text-cerberus-blue" />;
      case 'STRUCTURED_DATA': return <TableIcon className="w-4 h-4 text-cerberus-cyan" />;
      case 'IMAGE_OCR': return <ImageIcon className="w-4 h-4 text-cerberus-gold" />;
      default: return <Database className="w-4 h-4 text-cerberus-muted" />;
    }
  };

  return (
    <div className="space-y-6 pb-12">

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan">
              EVIDENCE VAULT REPOSITORY
            </span>
            <span className="px-1.5 py-0.2 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
              TAMPER AUDIT REGISTRY
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
            Central Evidence Vault
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
            Every ingested source carries an immutable Evidence ID, cryptographic hash, provenance origin, and extraction coordinates.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {!isDemoMode && evidenceFiles.length > 0 && (
            <button
              onClick={handleClearSession}
              className="px-3.5 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-cerberus-red border border-rose-500/30 text-xs font-mono font-bold transition-all flex items-center gap-1.5"
              title="Clear all uploaded files from active vault"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Vault</span>
            </button>
          )}

          <button
            onClick={() => setActiveTab('upload')}
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 text-white text-xs font-mono font-bold shadow-glow-blue transition-all flex items-center gap-2"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Ingest Source</span>
          </button>
        </div>
      </div>

      {/* Toolbar: Search, Modality Filter, Status Filter, Sorting */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">

        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 dark:text-cerberus-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Evidence ID, filename, or related entities..."
            className="w-full pl-9 pr-4 py-2 bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border rounded-xl text-xs text-slate-900 dark:text-cerberus-text placeholder-slate-400 dark:placeholder-cerberus-dark-muted focus:outline-none focus:border-blue-500 dark:focus:border-cerberus-cyan font-sans"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <select
            value={selectedModality}
            onChange={(e) => setSelectedModality(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border rounded-xl text-xs text-slate-700 dark:text-cerberus-muted focus:outline-none focus:border-blue-500 dark:focus:border-cerberus-cyan font-mono"
          >
            <option value="ALL">All Modalities</option>
            <option value="DOCUMENT">Documents (PDF)</option>
            <option value="STRUCTURED_DATA">Spreadsheets / CSV</option>
            <option value="IMAGE_OCR">Imagery & OCR</option>
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border rounded-xl text-xs text-slate-700 dark:text-cerberus-muted focus:outline-none focus:border-blue-500 dark:focus:border-cerberus-cyan font-mono"
          >
            <option value="ALL">All Statuses</option>
            <option value="PROCESSED">Processed</option>
            <option value="VERIFIED">Verified</option>
            <option value="UNVERIFIED">Unverified</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border rounded-xl text-xs text-slate-700 dark:text-cerberus-muted focus:outline-none focus:border-blue-500 dark:focus:border-cerberus-cyan font-mono"
          >
            <option value="newest">Sort: Newest</option>
            <option value="name">Sort: Name</option>
            <option value="size">Sort: Size</option>
          </select>
        </div>

      </div>

      {/* Evidence Table */}
      {filteredFiles.length === 0 ? (
        <EmptyState
          title="No Matching Evidence Sources"
          message="No records matched your search filters. Try adjusting keywords or upload new files."
          actionText="Upload Evidence"
          onAction={() => setActiveTab('upload')}
        />
      ) : (
        <div className="rounded-2xl border border-slate-200 dark:border-cerberus-border bg-white dark:bg-cerberus-card/80 overflow-hidden shadow-sm dark:shadow-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-200 dark:border-cerberus-border bg-slate-50 dark:bg-cerberus-bg-secondary text-slate-600 dark:text-cerberus-muted text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4">Evidence ID</th>
                  <th className="py-3 px-4">Filename & Source</th>
                  <th className="py-3 px-4">Modality</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4">Extraction Claims</th>
                  <th className="py-3 px-4">Reliability</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-cerberus-border/70 font-sans">
                {filteredFiles.map((file) => (
                  <tr
                    key={file.id}
                    onClick={() => setSelectedEvidence(file)}
                    className="hover:bg-slate-50 dark:hover:bg-cerberus-bg-secondary/60 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-blue-600 dark:text-cerberus-cyan">
                      {file.id}
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {getFormatIcon(file.modality)}
                        <span className="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[220px]">
                          {file.filename}
                        </span>
                      </div>
                      {file.relatedEntities && file.relatedEntities.length > 0 && (
                        <div className="text-[10px] text-slate-500 dark:text-cerberus-muted mt-0.5 truncate max-w-[220px]">
                          Entities: {file.relatedEntities.join(', ')}
                        </div>
                      )}
                    </td>

                    <td className="py-3 px-4 font-mono text-slate-600 dark:text-cerberus-muted text-[11px]">
                      {file.modality}
                    </td>

                    <td className="py-3 px-4 font-mono text-slate-700 dark:text-slate-300">
                      {formatBytes(file.size)}
                    </td>

                    <td className="py-3 px-4 font-mono text-cerberus-cyan font-bold">
                      {file.extractedClaimsCount || 0} Claims
                    </td>

                    <td className="py-3 px-4 font-mono">
                      {file.reliabilityScore != null ? (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${file.reliabilityScore >= 0.8 ? 'text-cerberus-green bg-cerberus-green/10' :
                            file.reliabilityScore >= 0.5 ? 'text-cerberus-amber bg-cerberus-amber/10' :
                              'text-cerberus-red bg-cerberus-red/10'
                          }`}>
                          {(file.reliabilityScore * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-cerberus-dark-muted">Unassessed</span>
                      )}
                    </td>

                    <td className="py-3 px-4 font-mono">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cerberus-green/10 text-cerberus-green border border-cerberus-green/30">
                        {file.status}
                      </span>
                    </td>

                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedEvidence(file);
                          }}
                          className="p-1.5 rounded text-cerberus-muted hover:text-cerberus-cyan hover:bg-cerberus-card transition-colors"
                          title="View Provenance Dossier"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </button>
                        {!isDemoMode && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteEvidence(file.id);
                            }}
                            className="p-1.5 rounded text-cerberus-muted hover:text-rose-500 dark:hover:text-cerberus-red hover:bg-rose-500/10 transition-colors"
                            title="Delete File from Vault"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Evidence Details Modal / Drawer */}
      {selectedEvidence && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">

            <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 font-bold">
                  {selectedEvidence.id}
                </span>
                <h3 className="font-mono font-bold text-base text-slate-900 dark:text-white">
                  {selectedEvidence.filename}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="text-slate-400 hover:text-slate-900 dark:text-cerberus-muted dark:hover:text-white p-1 rounded hover:bg-slate-100 dark:hover:bg-cerberus-bg-secondary transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Hash & Provenance */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">CRYPTOGRAPHIC HASH</span>
                <span className="text-blue-600 dark:text-cerberus-cyan truncate block mt-0.5">{selectedEvidence.hash || 'sha256:4d8f1e920b7a8c3d'}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border">
                <span className="text-[10px] text-slate-500 dark:text-cerberus-muted block uppercase">MODALITY SPEC</span>
                <span className="text-slate-900 dark:text-white block mt-0.5">{selectedEvidence.modality} ({selectedEvidence.format})</span>
              </div>
            </div>

            {/* Provenance Box */}
            {selectedEvidence.provenance && (
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-cerberus-bg/90 border border-slate-200 dark:border-cerberus-border text-xs">
                <span className="text-[10px] font-mono text-blue-700 dark:text-cerberus-cyan uppercase font-bold block mb-1">
                  Provenance Source & Submitter
                </span>
                <div className="space-y-1 font-mono text-slate-700 dark:text-slate-300">
                  <p>Source Gateway: <strong className="text-slate-900 dark:text-white">{selectedEvidence.provenance.source}</strong></p>
                  <p>Declared By: <strong className="text-slate-900 dark:text-white">{selectedEvidence.provenance.declaredBy}</strong></p>
                  <p>Target Entity: <strong className="text-blue-600 dark:text-cerberus-cyan">{selectedEvidence.provenance.targetEntity}</strong></p>
                </div>
              </div>
            )}

            {/* Extracted claims count and conflicts */}
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border flex items-center justify-between text-xs font-mono">
              <span className="text-slate-600 dark:text-cerberus-muted">Claims Extracted: <strong className="text-slate-900 dark:text-white">{selectedEvidence.extractedClaimsCount || 0}</strong></span>
              <span className="text-rose-600 dark:text-cerberus-red font-bold">Related Conflicts: {selectedEvidence.conflictsCount || 0}</span>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedEvidence(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-cerberus-card dark:hover:bg-cerberus-border text-slate-800 dark:text-slate-200 text-xs font-mono font-bold transition-colors"
              >
                Close Vault Inspector
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};

export default EvidencePage;
