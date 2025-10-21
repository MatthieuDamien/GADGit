import React, { useState, useEffect } from 'react';
import Header from './components/dashboard/Header';
import TaskDialog from './components/dialogs/TaskDialog';
import ClusterMetrics from './components/hooks/ClusterMetrics';
import AnalysisSection from './components/dashboard/AnalysisSection';
import AnalysisSectionParent from './components/dashboard/AnalysisSectionParent';
import { getAnalysisSummaries, getHealthStatus } from './services/mongoAPI'; // Ajout de getHealthStatus
import { Smile } from 'lucide-react';

const QuarkDashboard = () => {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // État pour le dark mode
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Vérifier la préférence locale ou système
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
    // Sauvegarder la préférence
    localStorage.setItem('darkMode', isDarkMode.toString());
  }, [isDarkMode]);

  // Effet pour récupérer les données des analyses
  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        setLoading(true);
        setError(null); // Réinitialiser l'erreur au début de chaque fetch
        const response = await getAnalysisSummaries();
        // On trie les analyses pour avoir un ordre prédictible
        // S'assurer que response.data est un tableau avant de trier
        const analysesData = Array.isArray(response.data) ? response.data : [];

        const sortedAnalyses = analysesData.sort((a, b) => 
            new Date(b.last_update) - new Date(a.last_update)
          );
        setAnalyses(sortedAnalyses);
      } catch (err) {
        console.error("Erreur lors de la récupération des analyses:", err);
        // On vérifie l'état de la connexion pour affiner le message d'erreur.
        try {
          const health = await getHealthStatus();
          if (health.data.mongodb !== 'connected') {
            setError("Erreur : La connexion à la base de données a échoué.");
          } else {
            setError("Impossible de charger les analyses. Le serveur répond mais les données sont inaccessibles.");
          }
        } catch (healthErr) {
          setError("Erreur : Impossible de se connecter au serveur backend.");
        }
        setAnalyses([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyses();
  }, [lastUpdate]); // Se déclenche au montage et lors du rafraîchissement

  // Fonction pour toggle le dark mode
  const handleToggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleRefresh = () => {
    setLastUpdate(new Date());
  };

  const noData = !loading && analyses.length === 0 && !error;

  return (
    <div className="min-h-screen">
      <Header 
        lastUpdate={lastUpdate} 
        onRefresh={handleRefresh} 
        isDarkMode={isDarkMode}
        onToggleDarkMode={handleToggleDarkMode}
      />

      <main className="p-6 min-h-screen bg-gradient-to-br 
                    from-blue-3 via-gray-2 to-blue-3 
                    dark:from-lime-2 dark:via-gray-2 dark:to-lime-2
                    bg-lime-1 text-gray-12 dark:text-lime-12 
                    transition-colors duration-300" >
        {/* Métriques du cluster */}
        <section className="mb-6">
          <ClusterMetrics />
        </section>

        <section>
          {loading && <div className="text-center p-10">Chargement des analyses...</div>}
          {error && <div className="text-center p-10 text-red-500">{error}</div>}
          {noData && (
            <div className="text-center p-10 flex flex-col items-center justify-center text-gray-11 dark:text-gray-10">
              <Smile size={40} className="mb-4" />
              <p className="text-xl">Aucune analyse à signaler ici !</p>
            </div>
          )}

          {!loading && !error && analyses.length > 0 && (
            <AnalysisSectionParent analyses={analyses} />
          )}
        </section>
      </main>
      <TaskDialog />
    </div>
  );
};

export default QuarkDashboard;