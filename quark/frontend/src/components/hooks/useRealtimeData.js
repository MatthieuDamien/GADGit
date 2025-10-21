// src/components/hooks/useRealtimeData.js
import { useState, useEffect, useCallback } from 'react';
import { getClusterMetrics, getAnalysisSummaries, getUtilityJobMetrics } from '../../services/mongoAPI';
import realtimeService from '../../services/realtimeService';

// Noms des collections en minuscules, tels qu'émis par le backend
const COLLECTIONS = {
    CLUSTER: 'cluster_snapshots',
    ANALYSIS: 'analysis_summaries',
    UTILITY: 'utility_job_snapshots',
};

export const useRealtimeData = () => {
    const [clusterMetrics, setClusterMetrics] = useState(null);
    const [analysisSummaries, setAnalysisSummaries] = useState([]);
    const [utilityJobMetrics, setUtilityJobMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fonctions de fetch pour chaque collection
    const fetchClusterMetrics = useCallback(async () => {
        try {
            const response = await getClusterMetrics();
            setClusterMetrics(response.data);
        } catch (err) { setError(err.message); }
    }, []);

    const fetchAnalysisSummaries = useCallback(async () => {
        try {
            const response = await getAnalysisSummaries();
            setAnalysisSummaries(response.data);
        } catch (err) { setError(err.message); }
    }, []);

    const fetchUtilityJobMetrics = useCallback(async () => {
        try {
            const response = await getUtilityJobMetrics();
            setUtilityJobMetrics(response.data);
        } catch (err) { setError(err.message); }
    }, []);

    const fetchData = useCallback(async () => {
        setLoading(true);
        await Promise.all([
            fetchClusterMetrics(),
            fetchAnalysisSummaries(),
            fetchUtilityJobMetrics()
        ]);
        setLoading(false);
    }, [fetchClusterMetrics, fetchAnalysisSummaries, fetchUtilityJobMetrics]);

    useEffect(() => {
        realtimeService.connect();
        fetchData();

        const handleDataUpdate = (updateInfo) => {
            console.log('Mise à jour reçue via WebSocket:', updateInfo);
            const { collection, operation, document } = updateInfo;

            switch (collection) {
                // Pour les snapshots (dernier document), on refetch pour être certain d'avoir la dernière version
                case COLLECTIONS.CLUSTER:
                    fetchClusterMetrics();
                    break;
                case COLLECTIONS.UTILITY:
                    fetchUtilityJobMetrics();
                    break;

                // Pour les listes (AnalysisSummaries), on manipule le state directement (performance)
                case COLLECTIONS.ANALYSIS:
                    if (!document) {
                         // Si on n'a pas le document (ex: erreur ou suppression sans fullDocument), on refetch
                         fetchAnalysisSummaries();
                         return;
                    }
                    setAnalysisSummaries(prevSummaries => {
                        const documentId = document._id.toHexString ? document._id.toHexString() : document._id;
                        
                        switch (operation) {
                            case 'insert':
                                // Ajoute le nouveau document en tête de liste
                                return [document, ...prevSummaries];
                            
                            case 'replace':
                            case 'update':
                                // Met à jour le document existant
                                return prevSummaries.map(summary => 
                                    summary._id === documentId ? document : summary
                                );
                            
                            case 'delete':
                                // Filtre et supprime le document
                                return prevSummaries.filter(summary => summary._id !== documentId);
                            
                            default:
                                return prevSummaries;
                        }
                    });
                    break;
                default:
                    console.log(`Changement non géré pour la collection: ${collection}`);
            }
        };

        realtimeService.onDataUpdated(handleDataUpdate);

        // Nettoyage non implémenté car le service est un singleton.
    }, [fetchData, fetchClusterMetrics, fetchAnalysisSummaries, fetchUtilityJobMetrics]);

    return { clusterMetrics, analysisSummaries, utilityJobMetrics, loading, error };
};