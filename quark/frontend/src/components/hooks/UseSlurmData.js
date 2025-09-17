// hooks/useSlurmData.js
import { useState, useEffect, useCallback } from 'react';
import SlurmAPI from '../../services/slurmAPI';

export const useSlurmData = (autoRefresh = true, refreshInterval = 30000) => {
  const [data, setData] = useState({
    sacct: [],
    squeue: [],
    sinfo: [],
    last_update: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Récupérer toutes les données
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await SlurmAPI.getAllData();
      if (response.success) {
        setData(response.data);
      } else {
        setError('Erreur lors de la récupération des données');
      }
    } catch (err) {
      setError(err.message);
      console.error('Erreur fetchAllData:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Forcer le rafraîchissement
  const refreshData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await SlurmAPI.refreshData();
      if (response.success) {
        setData(response.data);
      } else {
        setError('Erreur lors du rafraîchissement');
      }
    } catch (err) {
      setError(err.message);
      console.error('Erreur refreshData:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Récupérer les détails d'un job
  const getJobDetails = useCallback(async (jobId) => {
    try {
      const response = await SlurmAPI.getJobDetails(jobId);
      return response;
    } catch (err) {
      console.error('Erreur getJobDetails:', err);
      throw err;
    }
  }, []);

  // Effet pour la récupération initiale et auto-refresh
  useEffect(() => {
    fetchAllData();

    if (autoRefresh) {
      const interval = setInterval(fetchAllData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchAllData, autoRefresh, refreshInterval]);

  return {
    data,
    loading,
    error,
    refreshData,
    fetchAllData,
    getJobDetails,
    // Données spécifiques pour faciliter l'utilisation
    activeTasks: data.squeue || [],
    completedTasks: data.sacct || [],
    clusterInfo: data.sinfo || [],
    lastUpdate: data.last_update
  };
};