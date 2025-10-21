import React from 'react';

const StatusBadge = ({ status }) => {
  const getStatusClass = () => {
    // Utilisation de toLowerCase pour être plus robuste
    switch (status.toLowerCase()) {
      case 'running':
        return 'bg-blue-4 text-blue-11 dark:bg-lime-4 dark:text-lime-11';
      case 'completed':
        return 'bg-green-4 text-green-11';
      case 'error':
        return 'bg-red-4 text-red-11';
      case 'pending':
        return 'bg-yellow-4 text-yellow-11';
      default:
        return 'bg-gray-4 text-gray-11';
    }
  };

  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded-full capitalize ${getStatusClass()}`}>
      {status}
    </span>
  );
};

export default StatusBadge;