import React from 'react';
import { Database, Plus } from 'lucide-react';

export const EmptyState = ({ 
  title = "No Records Available", 
  message = "No data points found matching the selected query or filter criteria.", 
  actionText, 
  onAction 
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-cerberus-card/50 border border-dashed border-cerberus-border my-6">
      <div className="w-12 h-12 rounded-2xl bg-cerberus-card border border-cerberus-border flex items-center justify-center text-cerberus-muted mb-4 shadow-glass">
        <Database className="w-6 h-6 text-cerberus-cyan/60" />
      </div>
      <h3 className="text-sm font-bold text-cerberus-text font-mono">
        {title}
      </h3>
      <p className="text-xs text-cerberus-muted max-w-sm mt-1 mb-5 font-sans leading-relaxed">
        {message}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 rounded-xl bg-cerberus-blue hover:bg-blue-600 text-white text-xs font-mono font-bold shadow-glow-blue transition-all flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
