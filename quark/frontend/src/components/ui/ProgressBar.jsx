import React from 'react';

// Barre de progression
const ProgressBar = ({ value, className = "bg-blue-500", height = "h-2" }) => (
  <div className={`w-full bg-slate-700 rounded-full ${height} overflow-hidden`}>
    <div 
      className={`${height} rounded-full transition-all duration-500 ${className}`}
      style={{ width: `${value}%` }}
    />
  </div>
);

export{ProgressBar}