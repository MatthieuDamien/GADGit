import React from 'react';

// Barre de progression
const ProgressBar = ({ value, className = "bg-primary-light dark:bg-primary-dark", height = "h-2" }) => (
  <div className={`w-full bg-neutral/20 dark:bg-neutral/10 rounded-full ${height} overflow-hidden`}>
    <div 
      className={`${height} rounded-full transition-all duration-500 ${className}`}
      style={{ width: `${value}%` }}
    />
  </div>
);

export { ProgressBar };