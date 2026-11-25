import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  FileText, 
  Table as TableIcon, 
  Image as ImageIcon, 
  AlertTriangle, 
  CheckCircle2, 
  HelpCircle,
  ExternalLink,
  ChevronDown,
  Hash,
  Clock,
  Layers
} from 'lucide-react';
import { getModalityBadgeColor, getStatusBadge } from '../utils/formatters';

export const EvidenceTable = ({ claims = [], onSelectClaim }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedModality, setSelectedModality] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [activeClaimDetail, setActiveClaimDetail] = useState(null);

  // Filtered claims
  const filteredClaims = useMemo(() => {
    return claims.filter((claim) => {
      const matchSearch =
        searchTerm === '' ||
        claim.entity?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        claim.claimText?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        claim.sourceFile?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        claim.extractedValue?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchModality =
        selectedModality === 'ALL' || claim.modality === selectedModality;

      const matchStatus =
        selectedStatus === 'ALL' || claim.status === selectedStatus;

      return matchSearch && matchModality && matchStatus;
    });
  }, [claims, searchTerm, selectedModality, selectedStatus]);

  const getFormatIcon = (modality) => {
    switch (modality) {
      case 'DOCUMENT':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'STRUCTURED_DATA':
        return <TableIcon className="w-4 h-4 text-cyan-400" />;
      case 'IMAGE_OCR':
        return <ImageIcon className="w-4 h-4 text-purple-400" />;
      default:
        return <Layers className="w-4 h-4 text-slate-400" />;
    }
  };

  const renderLocationBadge = (claim) => {
    if (claim.page != null) {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-dark-800 text-slate-300 border border-dark-700 font-mono text-[10px]">
          <span>Page {claim.page}</span>
        </span>
      );
    }
    if (claim.sheet != null || claim.row != null) {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-dark-800 text-slate-300 border border-dark-700 font-mono text-[10px]">
          <span>{claim.sheet ? `${claim.sheet}: ` : ''}Row {claim.row || 'N/A'}</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-dark-800 text-slate-400 border border-dark-700 font-mono text-[10px]">
        <span>OCR Visual</span>
      </span>
    );
  };

  return (
    <div className="space-y-4">
      
      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        
        {/* Search input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search claims by entity, value, snippet, or source filename..."
            className="w-full pl-9 pr-4 py-2 bg-dark-900/80 border border-dark-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-accent-blue font-sans"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-xs font-mono"
            >
              ×
            </button>
          )}
        </div>

        {/* Filter dropdowns */}
        <div className="flex items-center gap-2">
          {/* Modality Filter */}
          <select
            value={selectedModality}
            onChange={(e) => setSelectedModality(e.target.value)}
            className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-accent-blue font-mono"
          >
            <option value="ALL">All Modalities</option>
            <option value="DOCUMENT">PDF Documents</option>
            <option value="STRUCTURED_DATA">Spreadsheets / CSV</option>
            <option value="IMAGE_OCR">Image OCR</option>
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-accent-blue font-mono"
          >
            <option value="ALL">All Statuses</option>
            <option value="CONTRADICTION">Contradictions</option>
            <option value="VERIFIED">Verified / Supported</option>
            <option value="UNVERIFIED">Unverified / Pending</option>
          </select>
        </div>

      </div>

      {/* Evidence Table */}
      <div className="rounded-xl border border-dark-700/80 bg-dark-900/60 overflow-hidden shadow-panel">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-700 bg-dark-850/80 text-[11px] font-mono uppercase tracking-wider text-slate-400">
                <th className="py-3 px-4">Entity / Subject</th>
                <th className="py-3 px-4">Extracted Value</th>
                <th className="py-3 px-4">Source Provenance</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Verification</th>
                <th className="py-3 px-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-800 text-xs font-sans">
              {filteredClaims.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-mono text-xs">
                    No matching claims found.
                  </td>
                </tr>
              ) : (
                filteredClaims.map((claim) => {
                  const statusInfo = getStatusBadge(claim.status);
                  return (
                    <tr
                      key={claim.id}
                      onClick={() => setActiveClaimDetail(claim)}
                      className={`hover:bg-dark-800/60 cursor-pointer transition-colors ${
                        claim.status === 'CONTRADICTION' ? 'bg-rose-950/10' : ''
                      }`}
                    >
                      {/* Entity */}
                      <td className="py-3 px-4 font-semibold text-slate-200">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-slate-500">{claim.id}</span>
                          <span>{claim.entity}</span>
                        </div>
                      </td>

                      {/* Value */}
                      <td className="py-3 px-4 font-mono font-medium text-slate-100">
                        <span className={`px-2 py-0.5 rounded text-[11px] ${
                          claim.status === 'CONTRADICTION'
                            ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                            : 'bg-dark-800 text-slate-200'
                        }`}>
                          {claim.extractedValue}
                        </span>
                      </td>

                      {/* Source */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2 min-w-0 max-w-[200px]">
                          {getFormatIcon(claim.modality)}
                          <span className="truncate text-slate-300 font-mono text-[11px]" title={claim.sourceFile}>
                            {claim.sourceFile}
                          </span>
                        </div>
                      </td>

                      {/* Location (Page/Sheet/Row) */}
                      <td className="py-3 px-4">
                        {renderLocationBadge(claim)}
                      </td>

                      {/* Confidence */}
                      <td className="py-3 px-4 font-mono text-[11px]">
                        {claim.confidence != null ? (
                          <div className="flex items-center gap-2">
                            <div className="w-12 h-1.5 rounded-full bg-dark-700 overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  claim.confidence > 0.9 ? 'bg-emerald-400' : 'bg-amber-400'
                                }`}
                                style={{ width: `${claim.confidence * 100}%` }}
                              />
                            </div>
                            <span className="text-slate-300">{(claim.confidence * 100).toFixed(1)}%</span>
                          </div>
                        ) : (
                          <span className="text-slate-500">N/A</span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono border font-semibold ${statusInfo.classes}`}>
                          {statusInfo.label}
                        </span>
                      </td>

                      {/* Action */}
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveClaimDetail(claim);
                          }}
                          className="p-1 rounded text-slate-400 hover:text-accent-cyan hover:bg-dark-700 transition-colors"
                          title="View complete evidence snippet and provenance"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer info */}
        <div className="p-3 bg-dark-850/60 border-t border-dark-700 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span>Showing {filteredClaims.length} of {claims.length} cross-modal claims</span>
          <span className="hidden sm:inline">Member 2: Ingest & Lineage Registry</span>
        </div>
      </div>

      {/* Claim Detail Modal */}
      {activeClaimDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-dark-900 border border-dark-700 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative space-y-4">
            
            <div className="flex items-center justify-between border-b border-dark-700 pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-500/10 text-accent-blue border border-blue-500/30">
                  {activeClaimDetail.id}
                </span>
                <h3 className="text-base font-bold text-slate-100 font-mono">
                  {activeClaimDetail.entity}
                </h3>
              </div>
              <button
                onClick={() => setActiveClaimDetail(null)}
                className="text-slate-400 hover:text-white p-1 rounded hover:bg-dark-800"
              >
                ✕
              </button>
            </div>

            {/* Extracted Value Callout */}
            <div className="p-3.5 rounded-xl bg-dark-800 border border-dark-700">
              <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                Extracted Value Representation
              </span>
              <p className="text-lg font-mono font-bold text-cyan-300">
                {activeClaimDetail.extractedValue}
              </p>
            </div>

            {/* Full Claim Sentence / Raw Text */}
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                Raw Extracted Context Snippet
              </span>
              <div className="p-3 rounded-lg bg-dark-950 border border-dark-800 text-xs text-slate-300 font-mono leading-relaxed">
                "{activeClaimDetail.claimText || 'No text snippet provided'}"
              </div>
            </div>

            {/* Provenance Metadata Grid */}
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded bg-dark-850 border border-dark-750">
                <span className="text-[10px] text-slate-500 block">SOURCE FILE</span>
                <span className="text-slate-200 truncate block mt-0.5">{activeClaimDetail.sourceFile}</span>
              </div>
              <div className="p-2.5 rounded bg-dark-850 border border-dark-750">
                <span className="text-[10px] text-slate-500 block">MODALITY & LOC</span>
                <span className="text-slate-200 block mt-0.5">
                  {activeClaimDetail.modality} ({activeClaimDetail.page ? `Page ${activeClaimDetail.page}` : activeClaimDetail.row ? `Row ${activeClaimDetail.row}` : 'Visual OCR'})
                </span>
              </div>
              <div className="p-2.5 rounded bg-dark-850 border border-dark-750">
                <span className="text-[10px] text-slate-500 block">CONFIDENCE METRIC</span>
                <span className="text-emerald-400 block mt-0.5">
                  {activeClaimDetail.confidence ? `${(activeClaimDetail.confidence * 100).toFixed(2)}%` : 'Unspecified'}
                </span>
              </div>
              <div className="p-2.5 rounded bg-dark-850 border border-dark-750">
                <span className="text-[10px] text-slate-500 block">VERDICT STATUS</span>
                <span className={`font-semibold block mt-0.5 ${
                  activeClaimDetail.status === 'CONTRADICTION' ? 'text-rose-400' : 'text-emerald-400'
                }`}>
                  {activeClaimDetail.status}
                </span>
              </div>
            </div>

            {/* Close Button */}
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setActiveClaimDetail(null)}
                className="px-4 py-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-slate-300 text-xs font-mono font-semibold"
              >
                Close Inspector
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};

export default EvidenceTable;
