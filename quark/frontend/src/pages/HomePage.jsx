import React, { useState, useEffect, useMemo } from 'react';
import Header from '../components/dashboard/Header';
import TaskDialog from '../components/dialogs/TaskDialog';
import ClusterMetrics from '../components/hooks/ClusterMetrics';
import UniqueJobs from '../components/dashboard/UniqueJobs';
import AnalysisSectionParent from '../components/dashboard/AnalysisSectionParent';
import { useRealtimeDataContext } from '../contexts/RealtimeDataContext';
import { Smile } from 'lucide-react';

const HomePage = () => {
  // Context des données en temps réel
  const { analysisSummaries, loading, error } = useRealtimeDataContext();
  // État pour le dark mode
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
  // Effet pour appliquer/retirer la classe dark sur le document
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', isDarkMode.toString());
  }, [isDarkMode]);
  // useMemo pour trier les analyses
  const sortedAnalyses = useMemo(() => {
    console.log('🔄 App.jsx - Recalcul du tri des analyses');
    if (!Array.isArray(analysisSummaries)) {
      console.warn('⚠️ analysisSummaries n\'est pas un array');
      return [];
    }

    console.log(`📊 Tri de ${analysisSummaries.length} analyses`);
    return [...analysisSummaries].sort((a, b) =>
      new Date(b.last_update) - new Date(a.last_update)
    );
  }, [analysisSummaries]);
  // Fonction pour toggle le dark mode
  const handleToggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };
  // Fonction de rafraîchissement manuel -- à supprimer plus tard
  const handleRefresh = () => {
    console.log('🔄 Refresh manuel demandé');
    window.location.reload();
  };
  const noData = !loading && sortedAnalyses.length === 0 && !error;
  return (
    <div className="min-h-screen">
      <Header
        lastUpdate={new Date()} // Toujours à jour grâce au WebSocket
        onRefresh={handleRefresh}
        isDarkMode={isDarkMode}
        onToggleDarkMode={handleToggleDarkMode}
      />
      <main className="p-6 min-h-screen bg-gradient-to-br
                    from-blue-3 via-gray-2 to-blue-3
                    dark:from-lime-2 dark:via-gray-2 dark:to-lime-2
                    bg-lime-1 text-gray-12 dark:text-lime-12
                    transition-colors duration-300">
        {/* Métriques du cluster */}
        <section className="mb-6">
          <ClusterMetrics />
        </section>
        <section>
          {loading && (
            <div className="text-center p-10">
              Chargement des analyses...
            </div>
          )}

          {error && (
            <div className="text-center p-10 text-red-500">
              {error}
              <br />
              <button
                onClick={handleRefresh}
                className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              >
                Réessayer
              </button>
            </div>
          )}

          {noData && (
            <div className="text-center p-10 flex flex-col items-center justify-center text-gray-11 dark:text-gray-10">
              <Smile size={40} className="mb-4" />
              <p className="text-xl">Aucune analyse à signaler ici !</p>
            </div>
          )}

          {!loading && !error && sortedAnalyses.length > 0 && (
            <AnalysisSectionParent analyses={sortedAnalyses} />
          )}
        </section>
        {/* Section des jobs utilitaires */}
        <section className="mb-6 space-y-6">
          <UniqueJobs />
        </section>
      </main>
      <TaskDialog />
    </div>
  );
};

export default HomePage;
