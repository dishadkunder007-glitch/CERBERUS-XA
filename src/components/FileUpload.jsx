import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  File, 
  FileText, 
  Image as ImageIcon, 
  Table, 
  X, 
  CheckCircle2, 
  AlertCircle, 
  ShieldAlert, 
  ArrowRight,
  Database,
  Loader2
} from 'lucide-react';
import { useInvestigation } from '../context/InvestigationContext';
import { formatBytes, getFileExtension } from '../utils/formatters';

const SUPPORTED_FORMATS = ['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls', 'csv'];

export const FileUpload = () => {
  const { 
    handleUploadFiles, 
    processingState, 
    backendStatus, 
    setIsDemoMode,
    setActiveTab 
  } = useInvestigation();
  
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const fileInputRef = useRef(null);

  // Validate file format
  const isValidFormat = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    return SUPPORTED_FORMATS.includes(ext);
  };

  const handleFiles = (files) => {
    setValidationError(null);
    const valid = [];
    const invalid = [];

    Array.from(files).forEach((file) => {
      if (isValidFormat(file.name)) {
        if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
          valid.push(file);
        }
      } else {
        invalid.push(file.name);
      }
    });

    if (invalid.length > 0) {
      setValidationError(`Unsupported format: ${invalid.join(', ')}. Supported: PDF, JPG, PNG, XLSX, XLS, CSV.`);
    }

    if (valid.length > 0) {
      setSelectedFiles((prev) => [...prev, ...valid]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
    setValidationError(null);
  };

  const handleSubmit = async () => {
    if (selectedFiles.length === 0) return;
    await handleUploadFiles(selectedFiles);
  };

  const getFormatIcon = (filename) => {
    const ext = getFileExtension(filename).toLowerCase();
    if (ext === 'pdf') return <FileText className="w-5 h-5 text-cerberus-blue" />;
    if (['jpg', 'jpeg', 'png'].includes(ext)) return <ImageIcon className="w-5 h-5 text-cerberus-gold" />;
    if (['xlsx', 'xls', 'csv'].includes(ext)) return <Table className="w-5 h-5 text-cerberus-cyan" />;
    return <File className="w-5 h-5 text-cerberus-muted" />;
  };

  return (
    <div className="space-y-6">
      
      {/* Backend Alert Notice */}
      {!backendStatus.online && (
        <div className="p-4 rounded-2xl bg-cerberus-red/10 border border-cerberus-red/30 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-cerberus-red shrink-0 mt-0.5" />
          <div className="text-xs text-rose-200 font-sans">
            <span className="font-bold font-mono text-cerberus-red">FASTAPI BACKEND DISCONNECTED:</span> Cannot reach{' '}
            <code className="px-1.5 py-0.5 rounded bg-cerberus-bg font-mono text-rose-300">
              {backendStatus.apiUrl}
            </code>
            . Live evidence ingestion requires your team's FastAPI server. You can run it with{' '}
            <code className="text-white font-mono">uvicorn main:app --reload</code> or explore the{' '}
            <button
              onClick={() => {
                setIsDemoMode(true);
                setActiveTab('dashboard');
              }}
              className="text-cerberus-cyan underline font-semibold ml-1 hover:text-white"
            >
              Demo Benchmark Dataset
            </button>
            .
          </div>
        </div>
      )}

      {/* Drag & Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center transition-all duration-200 ${
          dragActive
            ? 'border-blue-500 dark:border-cerberus-cyan bg-blue-50/50 dark:bg-cerberus-card scale-[0.99] shadow-glow-cyan'
            : 'border-slate-300 dark:border-cerberus-border hover:border-blue-500 dark:hover:border-cerberus-cyan/50 bg-white dark:bg-cerberus-card/70 hover:bg-slate-50 dark:hover:bg-cerberus-card shadow-sm dark:shadow-panel'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls,.csv"
          onChange={handleInputChange}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center pointer-events-none">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-cerberus-bg-secondary border border-blue-200 dark:border-cerberus-border flex items-center justify-center text-blue-600 dark:text-cerberus-cyan mb-4 shadow-sm dark:shadow-glow-cyan">
            <UploadCloud className="w-8 h-8" />
          </div>
          
          <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white font-mono">
            Drag & Drop Multimodal Evidence Files
          </h3>
          <p className="text-xs text-slate-600 dark:text-cerberus-muted max-w-md mt-1 font-sans">
            Ingest heterogeneous PDF documents, high-res telemetry imagery, or tabular XLSX/CSV ledgers.
          </p>

          <div className="mt-4 flex flex-wrap items-center justify-center gap-1.5">
            {['PDF Document', 'PNG / JPG Imagery', 'XLSX / CSV Spreadsheets'].map((tag) => (
              <span
                key={tag}
                className="px-2.5 py-1 text-[11px] font-mono rounded-lg bg-slate-100 dark:bg-cerberus-bg-secondary text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-cerberus-border"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-6">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={processingState.isUploading}
            className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 dark:bg-cerberus-blue dark:hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-bold font-mono tracking-wider transition-all shadow-glow-blue inline-flex items-center gap-2"
          >
            <UploadCloud className="w-4 h-4" />
            BROWSE SYSTEM FILES
          </button>
        </div>
      </div>

      {/* Validation Error Message */}
      {validationError && (
        <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-cerberus-amber/10 border border-amber-300 dark:border-cerberus-amber/30 text-xs text-amber-700 dark:text-cerberus-amber flex items-center gap-2 font-mono">
          <AlertCircle className="w-4 h-4 shrink-0 text-amber-600 dark:text-cerberus-amber" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Selected Files Staging Queue */}
      {selectedFiles.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-cerberus-border bg-white dark:bg-cerberus-card p-6 shadow-sm dark:shadow-panel">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-cerberus-border mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-cerberus-text">
                Selected Staging Payloads
              </span>
              <span className="px-2 py-0.5 rounded-full bg-blue-50 dark:bg-cerberus-blue/15 text-blue-700 dark:text-cerberus-cyan text-xs font-mono font-bold border border-blue-200 dark:border-cerberus-cyan/30">
                {selectedFiles.length}
              </span>
            </div>
            <button
              onClick={clearAllFiles}
              disabled={processingState.isUploading}
              className="text-xs font-mono text-slate-500 hover:text-rose-600 dark:text-cerberus-muted dark:hover:text-cerberus-red transition-colors"
            >
              Clear selection
            </button>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-cerberus-border/70 max-h-72 overflow-y-auto pr-1">
            {selectedFiles.map((file, idx) => (
              <div key={`${file.name}-${idx}`} className="py-2.5 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="p-2 rounded-xl bg-slate-100 dark:bg-cerberus-bg-secondary border border-slate-200 dark:border-cerberus-border shrink-0">
                    {getFormatIcon(file.name)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-900 dark:text-white truncate font-sans">
                      {file.name}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-500 dark:text-cerberus-muted font-mono mt-0.5">
                      <span>{formatBytes(file.size)}</span>
                      <span>•</span>
                      <span className="uppercase text-blue-600 dark:text-cerberus-cyan font-semibold">{getFileExtension(file.name)}</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => removeFile(idx)}
                  disabled={processingState.isUploading}
                  className="p-1 rounded text-slate-400 hover:text-rose-600 dark:text-cerberus-muted dark:hover:text-cerberus-red hover:bg-slate-100 dark:hover:bg-cerberus-bg-secondary transition-colors"
                  title="Remove file"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Processing Progress Bar */}
          {processingState.isUploading && (
            <div className="mt-4 pt-4 border-t border-cerberus-border">
              <div className="flex items-center justify-between text-xs font-mono text-slate-300 mb-1.5">
                <span className="flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 text-cerberus-cyan animate-spin" />
                  {processingState.statusText || 'Transmitting to FastAPI ingestion endpoint...'}
                </span>
                <span className="text-cerberus-cyan font-bold">{processingState.progress}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-cerberus-bg overflow-hidden border border-cerberus-border">
                <div
                  className="h-full bg-gradient-to-r from-cerberus-blue to-cerberus-cyan transition-all duration-300 rounded-full"
                  style={{ width: `${processingState.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Processing Error Notice */}
          {processingState.error && (
            <div className="mt-4 p-3.5 rounded-xl bg-cerberus-red/10 border border-cerberus-red/30 text-xs text-rose-300 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-cerberus-red shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold font-mono text-cerberus-red">Backend Ingestion Failure:</p>
                <p className="mt-0.5 font-sans">{processingState.error}</p>
              </div>
            </div>
          )}

          {/* Process Evidence Action Button */}
          <div className="mt-5 flex items-center justify-end gap-3">
            <button
              onClick={handleSubmit}
              disabled={processingState.isUploading || selectedFiles.length === 0}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-cerberus-blue hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-bold font-mono tracking-wider transition-all shadow-glow-blue flex items-center justify-center gap-2"
            >
              <ShieldAlert className="w-4 h-4 text-cerberus-cyan" />
              {processingState.isUploading ? 'INGESTING & EXTRACTING...' : `PROCESS ${selectedFiles.length} EVIDENCE FILE(S)`}
            </button>
          </div>
        </div>
      )}

      {/* Success Notification Banner */}
      {processingState.successMessage && (
        <div className="p-4 rounded-2xl bg-cerberus-green/10 border border-cerberus-green/30 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 text-xs text-cerberus-green font-mono">
            <CheckCircle2 className="w-5 h-5 text-cerberus-green shrink-0" />
            <span>{processingState.successMessage}</span>
          </div>
          <button
            onClick={() => setActiveTab('evidence')}
            className="px-3.5 py-1.5 rounded-lg bg-cerberus-green/20 hover:bg-cerberus-green/30 text-cerberus-green border border-cerberus-green/40 text-xs font-mono font-bold flex items-center gap-1 transition-colors"
          >
            Open Evidence Vault <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      )}

    </div>
  );
};

export default FileUpload;
