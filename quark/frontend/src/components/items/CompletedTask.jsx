import React from 'react';
import { CheckCircle } from 'lucide-react';

// Composant de tâche terminée
const CompletedTask = ({ task, onClick }) => (
  <div 
    className="p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg 
               border border-neutral/10 dark:border-neutral/10 
               hover:border-green-500 dark:hover:border-green-400 
               hover:bg-gray-100 dark:hover:bg-gray-800/70
               transition-all duration-300 cursor-pointer group"
    onClick={() => onClick && onClick(task)}
  >
    {/* Temps en haut */}
    <div className="flex items-center gap-2 mb-2">
      <span className="text-neutral text-xs">{task.time}</span>
      <div className="flex-1 h-px bg-neutral/20"></div>
    </div>
    
    {/* Contenu principal */}
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <CheckCircle className="w-4 h-4 text-green-500 dark:text-green-400" />
        <div>
          <div className="text-primary-light dark:text-white font-medium text-sm">{task.id}</div>
          <div className="text-neutral text-xs">{task.type}</div>
        </div>
      </div>
      <div className="flex flex-col items-end text-xs">
        <span className="text-neutral">{task.node}</span>
        <span className="text-green-500 dark:text-green-400">{task.timeToBeDone}</span>
      </div>
    </div>
  </div>
);

export default CompletedTask;