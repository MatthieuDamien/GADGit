// hooks/useSlurmData.js
import { useState, useEffect, useCallback, useRef } from 'react';
import SlurmAPI from '../../services/slurmAPI';
// 30000 ms = 30s
export const useSlurmData = (autoRefresh = true, refreshInterval = 5000) => {
  const [data, setData] = useState({
    connection_status: 'unknown',
    last_error: null,
    last_update: null,
    sacct:  [],
    squeue: [],
    sinfo:  [],
  });
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);                // Différencier chargement initial vs refresh
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('unknown');

  // Ref pour éviter les re-renders inutiles
  const lastUpdatRef = useRef(null);
  const intervalRef  = useRef(null);
  
  
  const updateData = useCallback((newData) => {
    setData(prevData => {
      const hasChanged = (
        JSON.stringify(prevData.sacct)  !== JSON.stringify(newData.sacct)  ||
        JSON.stringify(prevData.squeue) !== JSON.stringify(newData.squeue) ||
        JSON.stringify(prevData.sinfo)  !== JSON.stringify(newData.sinfo)  ||
        // Ajouter d'autres listes si nécessaire
        prevData.last_update !== newData.last_update
      );
      
      // previous data devient new data
      if (hasChanged) {
        console.log('Données mises à jour');
        prevData.sacct  = newData.sacct;
        prevData.squeue = newData.squeue;
        prevData.sinfo  = newData.sinfo;
        prevData.last_update = newData.last_update;
        // Mettre à jour les refs pour éviter les re-renders inutiles
        return { ...newData };
      }

      return prevData   // si pas de changement, on retourne l'ancienne data
    });
  }, []);
    


  // Récupérer toutes les données
  const fetchAllData = useCallback(async () => {
    try {
      const response = await SlurmAPI.getAllData();
      if (response.success && response.data) {
        updateData(response.data);
        setError(null);
        setConnectionStatus(response.data.connection_status || 'success');
        lastUpdatRef.current = response.data.last_update;
      } else {
        setError('Réponse API invalide', response);
        console.warn('Réponse API invalide', response);
      }
    } catch (err) {
      setError(err.message);
      console.error('Erreur fetchAllData:', err);
    }
  }, [updateData]);


// Inutile car fetchAllData fait la même chose en mieux
  // Forcer le rafraîchissement
//   const refreshData = useCallback(async () => {
//     setLoading(true);
//     setError(null);
    
//     try {
//       const response = await SlurmAPI.getAllData();
//       if (response.success && response.data) {
//         updateData(response.data);
//         setError(null);
//         setConnectionStatus(response.data.connection_status || 'success');
//         lastUpdatRef.current = response.data.last_update;
//       } else {
//         setError('Erreur de raffraichissment :', response);
//         console.warn('Erreur de raffraichissment :  ', response);
//       }
//     } catch (err) {
//       setError(err.message);
//       console.error('Erreur refreshData:', err);
//     } finally {
//       setLoading(false);
//     }
//  }, [updateData]);



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
    // refreshData,
    fetchAllData,
    getJobDetails,
    // Données spécifiques pour faciliter l'utilisation
    activeTasks: data.squeue || [],
    completedTasks: data.sacct || [],
    clusterInfo: data.sinfo || [],
    lastUpdate: data.last_update
  };
};