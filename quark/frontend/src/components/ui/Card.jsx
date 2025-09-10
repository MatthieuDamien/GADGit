import React from 'react';

// Composant Card générique
const Card = ({ children, className = "" }) => (
  <div className={`bg-gray-200 dark:bg-gris-500 backdrop-blur-sm rounded-xl 
                   border border-neutral/20 dark:border-neutral/10 
                   shadow-sm hover:shadow-md transition-shadow duration-200 rt-variant-surface ${className}`}>
    {children}
  </div>
);

// En-tête de Card
const CardHeader = ({ title, icon: Icon, iconColor = "text-neutral", count, children }) => (
  <div className="p-4 border-b border-neutral/10 dark:border-neutral/70">
    <div className="flex items-center justify-between">
      <h2 className="text-lg font-semibold text-primary-light dark:text-white flex items-center gap-2">
        {Icon && <Icon className={`w-5 h-5 ${iconColor}`} />}
        {title}
      </h2>
      {count !== undefined && (
        <span className="text-sm text-neutral">{count}</span>
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