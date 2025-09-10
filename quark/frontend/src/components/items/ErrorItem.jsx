import React from 'react';
import { XCircle, AlertCircle } from 'lucide-react';

// Composant d'erreur
const ErrorItem = ({ error, onClick }) => {
  const getSeverityColor = () => {
    switch(error.severity) {
      case 'error': return 'text-red-500 dark:text-red-400';
      case 'warning': return 'text-orange-500 dark:text-orange-400';
      default: return 'text-blue-500 dark:text-blue-400';
    }
  };

  const IconComponent = error.severity === 'error' ? XCircle : AlertCircle;

  return (
    <button className="flex items-center justify-between p-3 w-full
                        rounded-lg 
                       border border-neutral/10 dark:border-neutral/20 
                       hover:border-orange-500/75 dark:hover:border-orange-400/75 
                       hover:bg-gray-200 dark:hover:bg-gray-800/70
                       transition-all duration-300 cursor-pointer group"
            onClick={() => onClick && onClick(error)}>
      <div className="flex items-center gap-3">
        <IconComponent className={`w-5 h-5 ${getSeverityColor()}`} />
        <div className="text-left">
          <div className="text-primary-light dark:text-white font-medium">
            {error.id} - {error.type}
          </div>
          <div className="text-neutral text-sm">{error.message}</div>
        </div>
      </div>
      <span className="text-neutral text-sm whitespace-nowrap">{error.time}</span>
    </button>
  );
};

export default ErrorItem;