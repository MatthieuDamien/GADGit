import React, { useEffect, useState, useMemo } from 'react';
import Header from '../components/dashboard/Header';
import { useRealtimeDataContext } from '../contexts/RealtimeDataContext';
import { useParams } from 'react-router-dom';
import { ProgressBar } from '../components/ui/ProgressBar';
import StatusBadge from '../components/ui/StatusBadge';

const AnalysisPage = () => {
  const { id } = useParams();
  const { analysisSummaries, uniqueJobMetrics, loading: contextLoading, error: contextError } = useRealtimeDataContext();
  const [analysis, setAnalysis] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('darkMode');
      if (saved !== null) {
        return saved === 'true';
      }
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', isDarkMode.toString());
  }, [isDarkMode]);

  const handleToggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleRefresh = () => {
    console.log('🔄 Refresh manuel demandé');
    window.location.reload();
  };

  useEffect(() => {
    setLoading(contextLoading);
    if (contextError) {
      setError(contextError);
    }
  }, [contextLoading, contextError]);

  useEffect(() => {
    if (analysisSummaries.length > 0) {
      const foundAnalysis = analysisSummaries.find(summary => summary.analysis_id === id);
      if (foundAnalysis) {
        setAnalysis(foundAnalysis);
      } else {
        setError(`Analyse avec l'ID "${id}" non trouvée.`);
        setAnalysis(null);
      }
    }
  }, [analysisSummaries, id]);

  // CORRIGÉ: La liste des jobs est maintenant directement disponible dans l'objet 'analysis'.
  // Plus besoin de filtrer depuis 'uniqueJobMetrics'.
  const filteredJobs = useMemo(() => {
    if (!analysis || !analysis.infos || !analysis.infos.jobs_list) {
      return [];
    }

    const statusOrder = {
      // Running states
      'RUNNING': 1, 'R': 1, 'COMPLETING': 1, 'CG': 1,
      // Error states
      'FAILED': 2, 'F': 2, 'TIMEOUT': 2, 'TO': 2, 'CANCELLED': 2, 'CANCELLED+': 2, 'CA': 2, 'NODE_FAIL': 2, 'NF': 2, 'OUT_OF_MEMORY': 2,
      // Pending states
      'PENDING': 3, 'PD': 3,
      // Completed states
      'COMPLETED': 4,
    };

    const getStatusValue = (state) => {
      const upperState = state.toUpperCase();
      return statusOrder[upperState] || 99; // Default for unknown states
    };

    return [...analysis.infos.jobs_list].sort((a, b) => {
      const statusA = getStatusValue(a.STATE);
      const statusB = getStatusValue(b.STATE);
      if (statusA !== statusB) {
        return statusA - statusB;
      }
      // If statuses are the same, sort by Job ID descending
      return parseInt(b.JOBID, 10) - parseInt(a.JOBID, 10);
    });
  }, [analysis]);

  // Mettre à jour l'état de chargement une fois que les données sont prêtes
  useEffect(() => {
    if (!contextLoading && (analysis || error)) {
      setLoading(false);
    }
  }, [contextLoading, analysis, error]);

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

  const formatDuration = (totalSeconds) => {
    if (totalSeconds === null || totalSeconds === undefined || totalSeconds < 0) {
      return 'N/A';
    }
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);

    const pad = (num) => num.toString().padStart(2, '0');

    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  };

  if (loading) {
    return <div className="text-center p-10">Chargement des détails de l'analyse...</div>;
  }

  if (error) {
    return <div className="text-center p-10 text-red-500">Erreur: {error}</div>;
  }

  if (!analysis) {
    return <div className="text-center p-10">Aucune analyse trouvée pour cet ID.</div>;
  }

  const progressPercent = analysis.infos.jobs_total > 0
    ? (analysis.infos.jobs_completed / analysis.infos.jobs_total) * 100
    : 0;

  return (
    <div className="min-h-screen bg-gray-1 dark:bg-gray-1 text-gray-12 dark:text-gray-12">
      <Header
        lastUpdate={new Date()} // Toujours à jour grâce au WebSocket
        onRefresh={handleRefresh}
        isDarkMode={isDarkMode}
        onToggleDarkMode={handleToggleDarkMode}
      />
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4 p-6">Détails de l'analyse: {analysis.analysis_id}</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-gray-2 dark:bg-gray-3 p-4 rounded-lg shadow-md">
            <h2 className="text-xl font-bold mb-2">Informations générales</h2>
            <p><strong>Statut:</strong> <StatusBadge status={analysis.status} /></p>
            <p><strong>Utilisateur:</strong> {analysis.infos.user_name || 'inconnu'}</p>
            <p><strong>Priorité:</strong> {analysis.infos.priority}</p>
            <p><strong>Soumis le:</strong> {formatDate(analysis.infos.submitted_at)}</p> 
            <p><strong>Dernière mise à jour:</strong> {formatDate(analysis.last_update)}</p>
            <p><strong>Temps Total:</strong> {formatDuration(analysis.infos.execution_time_seconds)}</p>
          </div>
          <div className="bg-gray-2 dark:bg-gray-3 p-4 rounded-lg shadow-md">
            <h2 className="text-xl font-bold mb-2">Progression</h2>
            <p><strong>Jobs totaux:</strong> {analysis.infos.jobs_total}</p>
            <p><strong>Jobs terminés:</strong> {analysis.infos.jobs_completed}</p>
            <p><strong>Jobs en cours:</strong> {analysis.infos.jobs_running}</p>
            <p><strong>Jobs en attente:</strong> {analysis.infos.jobs_pending}</p>
            <p><strong>Jobs en erreur:</strong> {analysis.infos.jobs_error}</p>
            <div className="flex items-center mt-2">
              <strong className="mr-2">Progression:</strong>
              <div className="flex-grow">
                <ProgressBar allocatedValue={progressPercent} idleValue={100 - progressPercent} height="h-2.5" />
              </div>
              <span className="ml-2 w-12 text-right">{Math.round(progressPercent)} %</span>
            </div>
          </div>
        </div>
      </div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">Liste des jobs</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-gray-2 dark:bg-gray-3">
            <thead>
              <tr>
                <th className="py-2 px-4 border-b border-gray-4 dark:border-gray-5 bg-gray-3 dark:bg-gray-4 text-left text-xs font-semibold uppercase tracking-wider">Job ID</th>
                <th className="py-2 px-4 border-b border-gray-4 dark:border-gray-5 bg-gray-3 dark:bg-gray-4 text-left text-xs font-semibold uppercase tracking-wider">Nom</th>
                <th className="py-2 px-4 border-b border-gray-4 dark:border-gray-5 bg-gray-3 dark:bg-gray-4 text-left text-xs font-semibold uppercase tracking-wider">Statut</th>
                <th className="py-2 px-4 border-b border-gray-4 dark:border-gray-5 bg-gray-3 dark:bg-gray-4 text-left text-xs font-semibold uppercase tracking-wider">Utilisateur</th>
                <th className="py-2 px-4 border-b border-gray-4 dark:border-gray-5 bg-gray-3 dark:bg-gray-4 text-left text-xs font-semibold uppercase tracking-wider">Durée</th>
                <th className="py-2 px-4 border-b border-gray-4 dark:border-gray-5 bg-gray-3 dark:bg-gray-4 text-left text-xs font-semibold uppercase tracking-wider">Nœuds</th>
              </tr>
            </thead>
            <tbody>
              {filteredJobs.map((job, index) => (
                <tr
                  key={job.JOBID}
                  className={index % 2 === 0 ? 'bg-gray-2 dark:bg-gray-3' : 'bg-gray-3 dark:bg-gray-4'}
                >
                  <td className="py-2 px-4 border-b border-gray-4 dark:border-gray-5">{job.JOBID}</td>
                  <td className="py-2 px-4 border-b border-gray-4 dark:border-gray-5">{job.JOBNAME}</td>
                  <td className="py-2 px-4 border-b border-gray-4 dark:border-gray-5">
                    <StatusBadge status={job.STATE} />
                  </td>
                  <td className="py-2 px-4 border-b border-gray-4 dark:border-gray-5">{job.USER}</td>
                  <td className="py-2 px-4 border-b border-gray-4 dark:border-gray-5">{job.ELAPSED}</td>
                  <td className="py-2 px-4 border-b border-gray-4 dark:border-gray-5">{job.NODELIST}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage;
