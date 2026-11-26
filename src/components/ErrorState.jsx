import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const ErrorState = ({ 
  title = "Integration or Query Failure", 
  message = "An error occurred while communicating with the backend service.", 
  onRetry 
}) => {
  return (
    <div className="p-6 rounded-2xl bg-cerberus-red/10 border border-cerberus-red/30 my-6 text-left">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-cerberus-red shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-sm font-bold text-cerberus-red font-mono">
            {title}
          </h3>
          <p className="text-xs text-rose-200/80 font-sans mt-1 leading-relaxed">
            {message}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 px-3.5 py-1.5 rounded-lg bg-cerberus-red/20 hover:bg-cerberus-red/30 text-cerberus-red border border-cerberus-red/40 text-xs font-mono flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Retry Request
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorState;
