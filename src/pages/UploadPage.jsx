import React from 'react';
import { 
  UploadCloud, 
  FileText, 
  Image as ImageIcon, 
  Table as TableIcon, 
  Database,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { FileUpload } from '../components/FileUpload';
import { useInvestigation } from '../context/InvestigationContext';

export const UploadPage = () => {
  const { backendStatus, isDemoMode } = useInvestigation();

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-cerberus-cyan">
            DATA INGESTION CONSOLE
          </span>
          <span className="px-1.5 py-0.2 rounded bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan border border-blue-200 dark:border-cerberus-cyan/30 text-[10px] font-mono">
            MEMBER 2 PIPELINE
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
          Multimodal Evidence Ingestion Center
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-cerberus-muted mt-1 max-w-2xl font-sans">
          Upload PDF files, scanned documents, optical imagery, and tabular spreadsheets. Files are verified, extracted, and structured into atomic claims with spatial coordinates.
        </p>
      </div>

      {/* Main Upload Dropzone */}
      <FileUpload />

      {/* Modality Ingestion Architecture */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
        <div className="p-4 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
          <div className="flex items-center gap-2 text-blue-600 dark:text-cerberus-blue font-bold mb-1">
            <FileText className="w-4 h-4 text-blue-600 dark:text-cerberus-cyan" />
            <span className="text-slate-900 dark:text-white">PDF Documents</span>
          </div>
          <p className="text-slate-600 dark:text-cerberus-muted text-[11px] font-sans leading-relaxed">
            Layout-aware extraction preserving clause boxes, page numbers, and digital signatures.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
          <div className="flex items-center gap-2 text-amber-600 dark:text-cerberus-amber font-bold mb-1">
            <ImageIcon className="w-4 h-4 text-amber-600 dark:text-cerberus-gold" />
            <span className="text-slate-900 dark:text-white">Optical Imagery & OCR</span>
          </div>
          <p className="text-slate-600 dark:text-cerberus-muted text-[11px] font-sans leading-relaxed">
            OCR bounding box detection, EXIF timestamp verification, and visual tamper analysis.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-cerberus-card border border-slate-200 dark:border-cerberus-border shadow-sm">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-cerberus-green font-bold mb-1">
            <TableIcon className="w-4 h-4 text-emerald-600 dark:text-cerberus-green" />
            <span className="text-slate-900 dark:text-white">Spreadsheets & CSV</span>
          </div>
          <p className="text-slate-600 dark:text-cerberus-muted text-[11px] font-sans leading-relaxed">
            Relational table parsing retaining sheet names, column indices, and row-level coordinates.
          </p>
        </div>
      </div>

    </div>
  );
};

export default UploadPage;
