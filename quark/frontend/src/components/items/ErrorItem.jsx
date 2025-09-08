import React from 'react';
import { XCircle, AlertCircle } from 'lucide-react';

// Composant d'erreur
const ErrorItem = ({ error }) => {
  const getSeverityColor = () => {
    switch(error.severity) {
      case 'error': return 'text-red-500';
      case 'warning': return 'text-orange-500';
      default: return 'text-blue-500';
    }
  };

  const IconComponent = error.severity === 'error' ? XCircle : AlertCircle;

  return (
    <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-500 transition-all duration-200  hover:bg-marine-600/50">
      <div className="flex items-center gap-3">
        <IconComponent className={`w-5 h-5 ${getSeverityColor()}`} />
        <div>
          <div className="text-white font-medium">{error.id} - {error.type}</div>
          <div className="text-slate-400 text-sm">{error.message}</div>
        </div>
      </div>
      <span className="text-slate-400 text-sm whitespace-nowrap">{error.time}</span>
    </div>
  );
};

export default ErrorItem;