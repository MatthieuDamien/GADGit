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
                // Pour les snapshots (dernier document), on met à jour le state directement
                case COLLECTIONS.CLUSTER:
                    if (document && document.metrics) { // Vérifie que le document et les métriques sont présents
                        setClusterMetrics(document.metrics);
                    } else {
                        // Fallback de sécurité : si le document est incomplet, on refait un fetch
                        fetchClusterMetrics();
                    }
                    break;
                case COLLECTIONS.UTILITY:
                    if (document) { // On veut le document entier, incluant `jobs` et `raw_data`
                        setUtilityJobMetrics(document);
                    } else {
                        // Fallback de sécurité
                        fetchUtilityJobMetrics();
                    }
                    break;
                
                // Le code existant pour ANALYSIS est déjà parfait pour l'hydratation
                case COLLECTIONS.ANALYSIS:
                    if (!document || !document._id) {
                         // Si on n'a pas le document, on refetch par sécurité
                         fetchAnalysisSummaries(); 
                         return;
                    }

                    // 1. Normalisation de l'ID entrant en chaîne de caractères (Défense en profondeur)
                    const incomingId = String(document._id); 
                    
                    // 2. Clonage (nouvelle référence) du document pour forcer la détection de changement par React
                    // L'objet est déjà "propre" grâce à la correction du backend
                    const newDocumentReference = { ...document };

                    setAnalysisSummaries(prevSummaries => {
                        
                        switch (operation) {
                            case 'insert':
                                console.log('ACTION: INSERTING new analysis document'); // Log de confirmation
                                // Insère la nouvelle référence en tête de liste
                                return [newDocumentReference, ...prevSummaries];
                            
                            case 'replace':
                            case 'update':
                                console.log('ACTION: UPDATING analysis document with ID', incomingId); // Log de confirmation
                                return prevSummaries.map(summary => 
                                    // DÉFENSE EN PROFONDEUR : Convertit l'ID du summary existant en chaîne pour la comparaison
                                    String(summary._id) === incomingId ? newDocumentReference : summary
                                );
                            
                            case 'delete':
                                console.log('ACTION: DELETING analysis document with ID', incomingId); // Log de confirmation
                                // Filtre en comparant les chaînes (Défense en profondeur)
                                return prevSummaries.filter(summary => 
                                    String(summary._id) !== incomingId
                                );
                            
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