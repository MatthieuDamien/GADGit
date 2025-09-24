// Composant React d'exemple utilisant les données
// src/components/dashboard/SlurmDashboard.jsx
import React from 'react';
import { useSlurmData } from '../hooks/UseSlurmData';

const SlurmDashboard = () => {
  const { 
    data, 
    loading, 
    error, 
    refreshData, 
    activeTasks, 
    completedTasks,
    lastUpdate
  } = useSlurmData(true, 5000); // Auto-refresh toutes les 5s

  const handleRefresh = async () => {
    await refreshData();
  };

  if (loading) {
    return <div className="p-4">Chargement des données SLURM...</div>;
  }

  // Afficher l'ancienne data et mettre un pop-up autre part sur la page
  if (error) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 rounded">
        <h3 className="text-red-800">Erreur</h3>
        <p className="text-red-600">{error}</p>
        <button 
          onClick={handleRefresh}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard SLURM</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600 dark:text-slate-200">
            Dernière MAJ: {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : 'Jamais'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tâches actives (squeue) */}
        <div className="bg-white rounded-lg shadow p-4 dark:bg-gris-300">
          <h2 className="text-lg font-semibold mb-4">
            Tâches actives ({activeTasks.length})
          </h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {activeTasks.map((task, index) => (
              <div key={task.JOBID || index} className="p-2 bg-gray-50 rounded dark:bg-gris-400">
                <div className="flex justify-between">
                  <span className="font-medium">{task.JOBID}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    task.STATE === 'RUNNING' || task.STATE === 'R'? 'bg-blue-100 text-blue-800 dark:bg-blue-200 dark:text-blue-900' :
                    task.STATE === 'PENDING' || task.STATE === 'PD' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                  }`}>
                    {task.STATE}
                  </span>
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {task.JOBNAME} | {task.PARTITION}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tâches terminées (sacct) */}
        <div className="bg-white rounded-lg shadow p-4 dark:bg-gris-300">
          <h2 className="text-lg font-semibold mb-4">
            Tâches terminées ({completedTasks.length})
          </h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {completedTasks.map((task, index) => (
              <div key={task.JOBID || index} className="p-2 bg-gray-50 rounded dark:bg-gris-400">
                <div className="flex justify-between">
                  <span className="font-medium">{task.JOBID}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    task.STATE === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                    task.STATE === 'FAILED' ? 'bg-red-100 text-red-800' :
                    task.STATE === 'RUNNING' ? 'bg-blue-100 text-blue-800':
                    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                  }`}>
                    {task.STATE}
                  </span>
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {task.JOBNAME} | Durée: {task.ELAPSED}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Debug info */}
      <div className="mt-6 p-4 bg-gray-100 rounded dark:bg-gris-400">
        <details>
          <summary className="cursor-pointer font-medium">Données brutes (debug)</summary>
          <pre className="mt-2 text-xs overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  );
};

export default SlurmDashboard;