import React from 'react';

const StatusBadge = ({ status }) => {
  const getStatusClass = () => {
    // Utilisation de toLowerCase pour être plus robuste
    const lowerStatus = status ? status.toLowerCase() : 'unknown';

    // CORRIGÉ : Logique plus spécifique pour éviter les conflits (ex: 'c' pour completed et cancelled)
    // On vérifie les erreurs en premier.
    switch (true) {
      // Statuts d'erreur
      case lowerStatus.startsWith('fail'):
      case lowerStatus.startsWith('cancel'):
      case lowerStatus.startsWith('timeout'):
      case lowerStatus.startsWith('node_fail'):
      case lowerStatus.includes('err'):
        return 'bg-red-4 text-red-11';
      // Statuts en cours
      case lowerStatus.startsWith('runn'):
      case lowerStatus === 'r':
        return 'bg-blue-4 text-blue-11 dark:bg-lime-4 dark:text-lime-11';
      // Statuts terminés avec succès
      case lowerStatus.startsWith('complet'): // Gère 'COMPLETED' et 'COMPLETING'
        return 'bg-green-4 text-green-11';
      // Statuts en attente
      case lowerStatus.startsWith('pend'):
      case lowerStatus === 'pd':
        return 'bg-yellow-4 text-yellow-11 dark:bg-blue-12 dark:text-blue-1';
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