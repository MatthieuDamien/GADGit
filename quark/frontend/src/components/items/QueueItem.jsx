import React from 'react';
import PriorityBadge from '../ui/PriorityBadge';

// Composant d'élément de file d'attente
const QueueItem = ({ task, index }) => (
  <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-500 transition-all duration-200  hover:bg-marine-600/50">
    <div className="flex items-center gap-3">
      <span className="text-slate-400 text-sm w-6">#{index + 1}</span>
      <div>
        <div className="text-white font-medium">{task.id}</div>
        <div className="text-slate-400 text-sm">{task.type}</div>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <PriorityBadge priority={task.priority} />
      <span className="text-slate-400 text-sm">{task.waitTime}</span>
    </div>
  </div>
);

export default QueueItem;