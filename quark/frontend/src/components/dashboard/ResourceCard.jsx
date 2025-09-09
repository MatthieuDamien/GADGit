import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { ProgressBar } from '../ui/ProgressBar';

// Composant de statistique de ressource
const ResourceCard = ({ label, icon: Icon, iconColor, value, color }) => {
  const getProgressColor = (val) => {
    if (val > 95) return 'bg-red-600 dark:bg-red-500';
    if (val > 90) return 'bg-red-500 dark:bg-red-400';
    if (val > 75) return 'bg-orange-500 dark:bg-orange-400';
    if (val > 50) return 'bg-yellow-500 dark:bg-yellow-400';
    return 'bg-green-500 dark:bg-green-400';
  };

  return (
    <Card>
      <CardContent>
        <div className="flex items-center justify-between mb-2">
          <span className="text-neutral text-sm">{label}</span>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
        <div className="text-2xl font-bold text-primary-light dark:text-white mb-2">
          {value.toFixed(0)}%
        </div>
        <ProgressBar value={value} className={getProgressColor(value)} />
      </CardContent>
    </Card>
  );
};

export { ResourceCard };