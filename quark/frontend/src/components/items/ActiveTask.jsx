import React from 'react';
import { ProgressBar } from '../ui/ProgressBar';

// Composant de tâche active
const ActiveTask = ({ task }) => (
  <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-500 transition-all duration-200  hover:bg-marine-600/50">
    <div className="flex items-center justify-between mb-2">
      <div>
        <div className="text-white font-medium">{task.id}</div>
        <div className="text-slate-400 text-sm">{task.type} - {task.node}</div>
      </div>
      <div className="flex items-center gap-2">
        <div className="text-slate-400 text-sm">{task.user}</div>
      </div>
      <div className="text-right">
        <div className="text-cyan-400 font-medium">{parseFloat(task.progress).toFixed(2)}%</div>
        <div className="text-slate-400 text-sm">{task.time}</div>
      </div>
    </div>
    <ProgressBar 
      value={task.progress} 
      className="bg-gradient-to-r from-cyan-400 to-blue-500"
    />
  </div>
);

export default ActiveTask;