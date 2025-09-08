import React from 'react';

// Composant Card générique
const Card = ({ children, className = "" }) => (
  <div className={`bg-marine-500/50 backdrop-blur-sm rounded-xl border border-slate-700 ${className}`}>
    {children}
  </div>
);

// En-tête de Card
const CardHeader = ({ title, icon: Icon, iconColor = "text-slate-400", count, children }) => (
  <div className="p-4 border-b border-slate-700">
    <div className="flex items-center justify-between">
      <h2 className="text-lg font-semibold text-white flex items-center gap-2">
        {Icon && <Icon className={`w-5 h-5 ${iconColor}`} />}
        {title}
      </h2>
      {count !== undefined && (
        <span className="text-sm text-slate-400">{count}</span>
      )}
      {children}
    </div>
  </div>
);

// Corps de Card
const CardContent = ({ children, className = "" }) => (
  <div className={`p-4 ${className}`}>
    {children}
  </div>
);

export { Card, CardHeader, CardContent };