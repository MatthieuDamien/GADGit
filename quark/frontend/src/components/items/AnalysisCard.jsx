import React from 'react';
import { ProgressBar } from '../ui/ProgressBar';
import StatusBadge from '../ui/StatusBadge';

const AnalysisCard = ({ analysis }) => {
  const { analysis_id, status, infos, last_update } = analysis;

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calcul du pourcentage pour la barre de progression
  const progressPercent = infos.jobs_total > 0
    ? (infos.jobs_completed / infos.jobs_total) * 100
    : 0;

  return (
    <div className="p-4 rounded-lg shadow-md bg-gray-2 dark:bg-gray-3 border border-transparent hover:border-blue-7 dark:hover:border-lime-7 transition-all duration-200">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <h3 className="font-bold text-md text-gray-12 dark:text-white truncate">{analysis_id}</h3>
        </div>
        <StatusBadge status={status} />
      </div>
      <div className="text-sm text-gray-11 dark:text-gray-10 space-y-1">
        <p><strong>Utilisateur:</strong> {infos.user_name || 'inconnu'}</p>
        <p><strong>Jobs:</strong> {infos.jobs_completed} / {infos.jobs_total} terminés</p>
        <div className="flex items-center">
          <strong className="mr-2">Progression:</strong>
          <div className="flex-grow">
            <ProgressBar allocatedValue={progressPercent} idleValue={100 - progressPercent} height="h-2.5" />
          </div>
          <span className="ml-2 w-12 text-right">{Math.round(progressPercent)} %</span>
        </div>
        <p className="text-xs pt-2">Dernière MàJ: {formatDate(last_update)}</p>
      </div>
    </div>
  );
};

export default AnalysisCard;