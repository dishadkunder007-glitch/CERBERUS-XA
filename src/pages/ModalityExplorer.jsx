import React, { useState } from 'react';
import { 
  Layers, 
  FileText, 
  Image as ImageIcon, 
  Table as TableIcon, 
  Scan, 
  Database,
  ArrowRightLeft,
  Search,
  ExternalLink,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';

export const ModalityExplorer = () => {
  const [activeModality, setActiveModality] = useState('DOCUMENTS'); // 'DOCUMENTS', 'IMAGES', 'SPREADSHEETS', 'SCANNED', 'STRUCTURED', 'CROSS_MODAL'

  const modalityTabs = [
    { id: 'DOCUMENTS', label: 'Documents (PDF)', icon: FileText },
    { id: 'IMAGES', label: 'Optical Imagery', icon: ImageIcon },
    { id: 'SPREADSHEETS', label: 'Spreadsheets (XLSX)', icon: TableIcon },
    { id: 'SCANNED', label: 'Scanned Records', icon: Scan },
    { id: 'STRUCTURED', label: 'Structured Datasets', icon: Database },
    { id: 'CROSS_MODAL', label: 'Cross-Modal Comparison', icon: ArrowRightLeft },
  ];

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan">
            HETEROGENEOUS MODALITY INSPECTOR
          </span>
          <span className="px-1.5 py-0.2 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
            MEMBER 2 EXTRACTION
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
          Modality Explorer & Cross-Modal Workspace
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
          Inspect extracted features per modality: document clauses, OCR image bounding boxes, spreadsheet cells, and cross-modal comparison matrices.
        </p>
      </div>

      {/* Modality Selector Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 dark:border-cerberus-border pb-3">
        {modalityTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeModality === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveModality(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono transition-all ${
                isActive
                  ? 'bg-blue-500/10 dark:bg-cerberus-blue/20 text-blue-600 dark:text-cerberus-cyan border border-blue-500/30 dark:border-cerberus-cyan/40 shadow-sm font-bold'
                  : 'text-slate-600 dark:text-cerberus-muted hover:text-slate-900 dark:hover:text-white bg-white dark:bg-cerberus-card/80 border border-slate-200 dark:border-cerberus-border'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Documents (PDF) */}
      {activeModality === 'DOCUMENTS' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3">
            <div>
              <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                eu_customs_declaration_form_c88.pdf
              </h3>
              <p className="text-xs text-slate-500 dark:text-cerberus-muted font-mono">
                Page Provenance: Pages 1 - 6 • Extracted 14 Claims
              </p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-50 dark:bg-cerberus-blue/20 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-blue-500/40 font-bold">
              PDF CLAUSES
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border space-y-2">
              <span className="text-[10px] text-blue-600 dark:text-cerberus-cyan uppercase font-bold block">
                [Page 2, Box 22] Valuation Clause
              </span>
              <p className="text-slate-800 dark:text-slate-200 font-sans">
                "Declared FOB Customs Valuation of imported high-precision micro-controllers under Taric Code 8542.31 is certified at $1,420,000 USD."
              </p>
              <div className="text-[10px] text-rose-600 dark:text-cerberus-red font-bold">
                * Clashes with internal ERP spreadsheet by +350.7%
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border space-y-2">
              <span className="text-[10px] text-blue-600 dark:text-cerberus-cyan uppercase font-bold block">
                [Page 4, Box 18] Schedule Arrival
              </span>
              <p className="text-slate-800 dark:text-slate-200 font-sans">
                "Section 18: Vessel MV Polaris scheduled berthing arrival at Terminal 3 marked as July 19, 2026 14:00 UTC."
              </p>
              <div className="text-[10px] text-rose-600 dark:text-cerberus-red font-bold">
                * Direct contradiction with optical berth telemetry (July 14)
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Optical Imagery */}
      {activeModality === 'IMAGES' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3">
            <div>
              <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                dock_berth_highres_telemetry.png
              </h3>
              <p className="text-xs text-slate-500 dark:text-cerberus-muted font-mono">
                Port Autonomous Optical Sensor Array • Berth 4-A
              </p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-50 dark:bg-cerberus-gold/20 text-amber-700 dark:text-cerberus-gold border border-amber-200 dark:border-cerberus-gold/40 font-bold">
              OPTICAL OCR
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border space-y-2">
              <span className="text-[10px] text-amber-600 dark:text-cerberus-gold uppercase font-bold block">
                Detected Bounding Boxes & OCR String Matches
              </span>
              <ul className="space-y-1.5 text-slate-800 dark:text-slate-200 font-mono">
                <li>• Box [420, 180, 580, 240]: <strong className="text-blue-600 dark:text-cerberus-cyan">"IMO 9128472"</strong> (Confidence 99.4%)</li>
                <li>• Box [890, 40, 1100, 80]: <strong className="text-emerald-600 dark:text-cerberus-green">"BERTH 4-A"</strong> (Confidence 98.9%)</li>
                <li>• Box [1200, 30, 1500, 70]: <strong className="text-blue-600 dark:text-cerberus-cyan">"2026-07-14 04:12 UTC"</strong> (Confidence 99.8%)</li>
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border space-y-2">
              <span className="text-[10px] text-emerald-600 dark:text-cerberus-green uppercase font-bold block">
                EXIF & Physical Verification
              </span>
              <p className="text-slate-700 dark:text-slate-300 font-sans leading-relaxed">
                Sensor calibration signed with SHA-256 hardware token. Visual vessel draft height confirms laden cargo at 1,180 metric tons.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Spreadsheets (XLSX) */}
      {activeModality === 'SPREADSHEETS' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3">
            <div>
              <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                internal_freight_manifest_q3.xlsx
              </h3>
              <p className="text-xs text-slate-500 dark:text-cerberus-muted font-mono">
                Sheets: Manifest_Overview, Container_Manifest, Audit_Trail • 28 Claims
              </p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-50 dark:bg-cerberus-cyan/20 text-cyan-700 dark:text-cerberus-cyan border border-cyan-200 dark:border-cerberus-cyan/40 font-bold">
              TABULAR RELATIONAL
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-200 dark:border-cerberus-border text-slate-600 dark:text-cerberus-muted text-[10px] uppercase">
                  <th className="py-2.5 px-3">Row #</th>
                  <th className="py-2.5 px-3">Container ID</th>
                  <th className="py-2.5 px-3">Commodity</th>
                  <th className="py-2.5 px-3">Net Mass</th>
                  <th className="py-2.5 px-3">Ledger Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-cerberus-border/60">
                <tr className="hover:bg-slate-50 dark:hover:bg-cerberus-bg-secondary/40">
                  <td className="py-2 px-3 text-blue-600 dark:text-cerberus-cyan font-bold">142</td>
                  <td className="py-2 px-3">CONT-EU-9011</td>
                  <td className="py-2 px-3 text-slate-700 dark:text-slate-300">High-Precision Microcontrollers</td>
                  <td className="py-2 px-3">48,000 kg</td>
                  <td className="py-2 px-3 text-emerald-600 dark:text-cerberus-green font-bold">$4,980,000 USD (Consignment Sum)</td>
                </tr>
                <tr className="hover:bg-slate-50 dark:hover:bg-cerberus-bg-secondary/40">
                  <td className="py-2 px-3 text-blue-600 dark:text-cerberus-cyan font-bold">178</td>
                  <td className="py-2 px-3">CONT-EU-9016</td>
                  <td className="py-2 px-3 text-slate-700 dark:text-slate-300">High-Density Compute Modules</td>
                  <td className="py-2 px-3 font-bold text-amber-600 dark:text-cerberus-amber">1,180,000 kg (Total Sum)</td>
                  <td className="py-2 px-3 text-slate-700 dark:text-slate-300">$1,280,000 USD</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Scanned Records */}
      {activeModality === 'SCANNED' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3">
            <div>
              <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                supplier_commercial_invoice_904.jpg
              </h3>
              <p className="text-xs text-slate-500 dark:text-cerberus-muted font-mono">
                Offshore Supplier Commercial Invoice OCR • Page 1
              </p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-50 dark:bg-cerberus-gold/20 text-amber-700 dark:text-cerberus-gold border border-amber-200 dark:border-cerberus-gold/40 font-bold">
              SCANNED PAPER OCR
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border space-y-2 text-xs font-mono">
            <span className="text-[10px] text-amber-600 dark:text-cerberus-gold uppercase font-bold block">
              Extracted OCR Entity & Billed Valuation
            </span>
            <p className="text-slate-800 dark:text-slate-200 font-sans">
              "Commercial Invoice itemized total for consignment batch 7091 billed to holding company: €4,550,000 EUR (~$4.95M USD)."
            </p>
            <div className="text-[10px] text-emerald-600 dark:text-cerberus-green font-bold">
              * Corroborates internal ERP spreadsheet ($4.98M) vs false customs claim ($1.42M)
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Structured Datasets */}
      {activeModality === 'STRUCTURED' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-cerberus-border pb-3">
            <div>
              <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                port_authority_customs_logbook.csv
              </h3>
              <p className="text-xs text-slate-500 dark:text-cerberus-muted font-mono">
                Municipal Harbor Master Dispatch Feed • 19 Relational Claims
              </p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-50 dark:bg-cerberus-cyan/20 text-cyan-700 dark:text-cerberus-cyan border border-cyan-200 dark:border-cerberus-cyan/40 font-bold">
              CSV LOGBOOK
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border text-xs font-mono space-y-2">
            <span className="text-[10px] text-blue-600 dark:text-cerberus-cyan uppercase font-bold block">
              Automated Pilot Assisted Mooring Log
            </span>
            <p className="text-slate-700 dark:text-slate-300 font-sans">
              Row 88: Vessel MV Polaris tug assist complete and tied to Berth 4-A on July 14, 2026 at 03:55 UTC. Pilot Operator: Capt. H. Lindqvist.
            </p>
          </div>
        </div>
      )}

      {/* Tab 6: Cross-Modal Comparison Workspace */}
      {activeModality === 'CROSS_MODAL' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm dark:shadow-panel space-y-4">
          <div className="border-b border-slate-200 dark:border-cerberus-border pb-3">
            <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
              <ArrowRightLeft className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
              Cross-Modal Synthesis & Multi-Modality Juxtaposition
            </h3>
            <p className="text-xs text-slate-500 dark:text-cerberus-muted font-mono mt-0.5">
              Direct side-by-side comparison of conflicting modalities for Entity: Consignment 7091 & MV Polaris
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            {/* Source 1: Document */}
            <div className="p-4 rounded-xl bg-rose-50 dark:bg-cerberus-red/10 border border-rose-200 dark:border-cerberus-red/40 space-y-2">
              <span className="text-[10px] text-rose-600 dark:text-cerberus-red font-bold uppercase block">
                MODALITY: PDF DOCUMENT
              </span>
              <p className="font-bold text-slate-900 dark:text-white text-sm">$1,420,000 USD</p>
              <p className="text-[11px] text-slate-600 dark:text-slate-300 font-sans">Customs C88 Form filing</p>
              <div className="text-[10px] text-rose-600 dark:text-cerberus-red font-bold">STATUS: CONFLICT</div>
            </div>

            {/* Source 2: Spreadsheet */}
            <div className="p-4 rounded-xl bg-cyan-50 dark:bg-cerberus-cyan/10 border border-cyan-200 dark:border-cerberus-cyan/40 space-y-2">
              <span className="text-[10px] text-cyan-700 dark:text-cerberus-cyan font-bold uppercase block">
                MODALITY: SPREADSHEET
              </span>
              <p className="font-bold text-slate-900 dark:text-white text-sm">$4,980,000 USD</p>
              <p className="text-[11px] text-slate-600 dark:text-slate-300 font-sans">Internal ERP database ledger</p>
              <div className="text-[10px] text-cyan-700 dark:text-cerberus-cyan font-bold">STATUS: CORROBORATED</div>
            </div>

            {/* Source 3: Optical Image */}
            <div className="p-4 rounded-xl bg-emerald-50 dark:bg-cerberus-green/10 border border-emerald-200 dark:border-cerberus-green/40 space-y-2">
              <span className="text-[10px] text-emerald-700 dark:text-cerberus-green font-bold uppercase block">
                MODALITY: SCANNED IMAGE
              </span>
              <p className="font-bold text-slate-900 dark:text-white text-sm">€4,550,000 EUR (~$4.95M)</p>
              <p className="text-[11px] text-slate-600 dark:text-slate-300 font-sans">Commercial Supplier Invoice OCR</p>
              <div className="text-[10px] text-emerald-700 dark:text-cerberus-green font-bold">STATUS: CORROBORATED</div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default ModalityExplorer;
