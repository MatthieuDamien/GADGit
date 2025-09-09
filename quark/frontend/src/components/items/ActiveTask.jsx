import React from 'react';
import { ProgressBar } from '../ui/ProgressBar';

// Composant de tâche active
const ActiveTask = ({ task, onClick }) => (
  <div className="p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg 
                  border border-neutral/10 dark:border-neutral/10 
                  hover:border-primary-light dark:hover:border-primary-dark 
                  hover:bg-gray-100 dark:hover:bg-gray-800/70
                  transition-all duration-300 cursor-pointer"
       onClick={() => onClick && onClick(task)}>
    <div className="flex items-center justify-between mb-2">
      <div>
        <div className="text-primary-light dark:text-white font-medium">{task.id}</div>
        <div className="text-neutral text-sm">{task.type} - {task.node}</div>
      </div>
      <div className="flex items-center gap-2">
        <div className="text-neutral text-sm">{task.user}</div>
      </div>
      <div className="text-right">
        <div className="text-primary-light dark:text-primary-dark font-medium">
          {parseFloat(task.progress).toFixed(2)}%
        </div>
        <div className="text-neutral text-sm">{task.time}</div>
      </div>
    </div>
    <ProgressBar 
      value={task.progress} 
      className="bg-gradient-to-r from-primary-light to-marine-700 
                 dark:from-primary-dark dark:to-jaune-500/70"
    />
  </div>
);

export default ActiveTask;