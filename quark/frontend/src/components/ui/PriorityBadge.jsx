import React from 'react';

// Badge de priorité
const PriorityBadge = ({ priority }) => {
  const getColorClass = () => {
    switch(priority) {
      case 'Urgente': return 'bg-red-500';
      case 'Haute': return 'bg-orange-500';
      case 'Normale': return 'bg-blue-500';
      case 'Basse': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs text-white font-medium ${getColorClass()}`}>
      {priority}
    </span>
  );
};

export default PriorityBadge;