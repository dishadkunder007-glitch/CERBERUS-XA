// Formatting and utility functions for CERBERUS-XA Intelligence Dashboard

export const formatBytes = (bytes, decimals = 2) => {
  if (!+bytes) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

export const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  } catch {
    return String(timestamp);
  }
};

export const getFileExtension = (filename = '') => {
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop().toUpperCase() : 'UNKNOWN';
};

export const getModalityType = (filename = '') => {
  const ext = getFileExtension(filename).toLowerCase();
  if (['pdf'].includes(ext)) return 'DOCUMENT';
  if (['jpg', 'jpeg', 'png'].includes(ext)) return 'IMAGE_OCR';
  if (['xlsx', 'xls', 'csv'].includes(ext)) return 'STRUCTURED_DATA';
  return 'MULTIMODAL_OTHER';
};

export const getModalityBadgeColor = (type) => {
  switch (type) {
    case 'DOCUMENT':
      return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
    case 'IMAGE_OCR':
      return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
    case 'STRUCTURED_DATA':
      return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
    default:
      return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
  }
};

export const getVerdictColor = (verdict = '') => {
  const v = verdict.toLowerCase();
  if (v.includes('supported')) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  if (v.includes('conflict')) return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
  if (v.includes('insufficient')) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
  if (v.includes('manipulated')) return 'text-purple-400 bg-purple-500/10 border-purple-500/30';
  return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
};

export const getStatusBadge = (status = '') => {
  const s = status.toLowerCase();
  if (s === 'verified' || s === 'supported' || s === 'extracted' || s === 'processed') {
    return {
      label: 'VERIFIED',
      classes: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
    };
  }
  if (s === 'conflict' || s === 'contradiction' || s === 'disputed') {
    return {
      label: 'CONTRADICTION',
      classes: 'text-rose-400 bg-rose-500/10 border-rose-500/30'
    };
  }
  if (s === 'unverified' || s === 'pending' || s === 'processing') {
    return {
      label: 'UNVERIFIED',
      classes: 'text-amber-400 bg-amber-500/10 border-amber-500/30'
    };
  }
  return {
    label: status.toUpperCase() || 'UNKNOWN',
    classes: 'text-slate-400 bg-slate-500/10 border-slate-500/30'
  };
};
