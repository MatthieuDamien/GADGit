import React from 'react';

// Badge de priorité
const PriorityBadge = ({ priority }) => {
  const getColorClass = () => {
    switch(priority) {
      case 'Urgente': 
        return 'bg-red-4 text-red-11';
      case 'Haute': 
        return 'bg-orange-4 text-orange-11';
      case 'Normale': 
        return 'bg-blue-4 text-blue-11 dark:bg-lime-4 dark:text-lime-11';
      case 'Basse': 
        return 'bg-gray-4 text-gray-11';
      default: 
        return 'bg-gray-4 text-gray-11';
    }
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getColorClass()}`}>
      {priority}
    </span>
  );
};

export default PriorityBadge;