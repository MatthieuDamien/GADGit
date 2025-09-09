import React from 'react';

// Badge de priorité
const PriorityBadge = ({ priority }) => {
  const getColorClass = () => {
    switch(priority) {
      case 'Urgente': 
        return 'bg-red-500 dark:bg-red-500/80 text-white';
      case 'Haute': 
        return 'bg-orange-500 dark:bg-orange-500/80 text-white';
      case 'Normale': 
        return 'bg-primary-light dark:bg-primary-dark text-white dark:text-black';
      case 'Basse': 
        return 'bg-neutral/50 dark:bg-neutral/30 text-neutral dark:text-neutral';
      default: 
        return 'bg-neutral/50 dark:bg-neutral/30 text-neutral dark:text-neutral';
    }
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getColorClass()}`}>
      {priority}
    </span>
  );
};

export default PriorityBadge;