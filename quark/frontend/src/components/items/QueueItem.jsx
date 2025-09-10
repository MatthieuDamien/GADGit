import React from 'react';
import PriorityBadge from '../ui/PriorityBadge';

// Composant d'élément de file d'attente
const QueueItem = ({ task, index, onClick }) => (
  <div className="flex items-center justify-between p-3 
                  rounded-lg 
                  border border-neutral/10 dark:border-neutral/20
                  hover:border-marine-border800 dark:hover:border-primary-dark 
                  hover:bg-gray-200 dark:hover:bg-gray-800/70
                  transition-all duration-300 cursor-pointer"
       onClick={() => onClick && onClick(task)}>
    <div className="flex items-center gap-3">
      <span className="text-neutral text-sm w-6">#{index + 1}</span>
      <div>
        <div className="text-primary-light dark:text-white font-medium">{task.id}</div>
        <div className="text-neutral text-sm">{task.type}</div>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <PriorityBadge priority={task.priority} />
      <span className="text-neutral text-sm">{task.waitTime}</span>
    </div>
  </div>
);

export default QueueItem;