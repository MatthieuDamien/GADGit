// src/components/hooks/useRealtimeData.js
import { useState, useEffect, useCallback } from 'react';
import { getClusterMetrics, getAnalysisSummaries, getUniqueJobs } from '../../services/mongoAPI';
import realtimeService from '../../services/realtimeService';

const COLLECTIONS = {
    CLUSTER: 'cluster_snapshots',
    ANALYSIS: 'analysis_summaries',
    // MODIFIÉ: Nom de collection corrigé et ajout de RAW pour référence future
    UNIQUE: 'unique_jobs',
    RAW: 'raw_jobs',
};

export const useRealtimeData = () => {
    const [clusterMetrics, setClusterMetrics] = useState(null);
    const [analysisSummaries, setAnalysisSummaries] = useState([]);
    const [uniqueJobs, setUniqueJobs] = useState([]); // MODIFIÉ: Initialisé comme un tableau
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

    // MODIFIÉ: Renommé pour correspondre à la nouvelle terminologie
    const fetchUniqueJobs = useCallback(async () => {
        try {
            const response = await getUniqueJobs();
            setUniqueJobs(response.data || []); // S'assurer que c'est toujours un tableau
        } catch (err) { setError(err.message); }
    }, []);

    const fetchData = useCallback(async () => {
        setLoading(true);
        await Promise.all([
            fetchClusterMetrics(),
            fetchAnalysisSummaries(),
            fetchUniqueJobs()
        ]);
        setLoading(false);
    }, [fetchClusterMetrics, fetchAnalysisSummaries, fetchUniqueJobs]);

    useEffect(() => {
        realtimeService.connect();
        fetchData();

        const handleDataUpdate = (updateInfo) => {
            console.log('📡 Mise à jour reçue via WebSocket:', updateInfo);
            const { collection, operation, document } = updateInfo;

            switch (collection) {
                case COLLECTIONS.CLUSTER:
                    if (document && document.metrics) {
                        setClusterMetrics({ ...document.metrics });
                        console.log('✅ ClusterMetrics mis à jour');
                    } else {
                        fetchClusterMetrics();
                    }
                    break;
                    
                // MODIFIÉ: Logique de mise à jour pour le tableau de jobs uniques
                case COLLECTIONS.UNIQUE:
                    if (!document || !document.JOBID) {
                        // Si le document est invalide, refetcher toute la liste par sécurité
                        fetchUniqueJobs();
                        return;
                    }

                    const incomingJobId = document.JOBID;

                    setUniqueJobs(prevJobs => {
                        const jobExists = prevJobs.some(job => job.JOBID === incomingJobId);

                        if (operation === 'insert' && !jobExists) {
                            console.log('➕ INSERT unique job:', incomingJobId);
                            // Ajoute le nouveau job au début de la liste
                            return [document, ...prevJobs];
                        }

                        if (operation === 'update' || operation === 'replace') {
                            console.log('✏️ UPDATE unique job:', incomingJobId);
                            // Si le job existe, on le remplace. Sinon, on l'ajoute (comportement upsert).
                            return jobExists
                                ? prevJobs.map(job => (job.JOBID === incomingJobId ? document : job))
                                : [document, ...prevJobs];
                        }

                        if (operation === 'delete') {
                            console.log('🗑️ DELETE unique job (non implémenté côté client, refetch)');
                            // Pour 'delete', le document est souvent null. Un refetch est plus simple.
                            fetchUniqueJobs();
                            return prevJobs;
                        }

                        return prevJobs; // Ne rien faire pour les autres opérations
                    });
                    break;
                
                case COLLECTIONS.ANALYSIS:
                    if (!document || !document._id) {
                        fetchAnalysisSummaries(); 
                        return;
                    }

                    const cleanedDocument = JSON.parse(JSON.stringify(document)); 
                    const incomingId = cleanedDocument._id.toString(); 
                    
                    setAnalysisSummaries(prevSummaries => {
                        let newSummaries;
                        
                        switch (operation) {
                            case 'insert':
                                console.log('➕ INSERT analysis:', incomingId);
                                
                                // 🔧 DÉDUPLICATION : Vérifier si l'ID existe déjà
                                const alreadyExists = prevSummaries.some(
                                    summary => summary._id.toString() === incomingId
                                );
                                
                                if (alreadyExists) {
                                    console.warn('⚠️ Duplicate insert ignored for:', incomingId);
                                    return prevSummaries; // Ne rien faire, éviter le doublon
                                }
                                
                                newSummaries = [cleanedDocument, ...prevSummaries];
                                break;
                            
                            case 'replace':
                            case 'update':
                                console.log('✏️ UPDATE analysis:', incomingId);
                                newSummaries = prevSummaries.map(summary => 
                                    summary._id.toString() === incomingId ? cleanedDocument : summary
                                );
                                break;
                            
                            case 'delete':
                                console.log('🗑️ DELETE analysis:', incomingId);
                                newSummaries = prevSummaries.filter(summary => 
                                    summary._id.toString() !== incomingId
                                );
                                break;
                            
                            default:
                                return prevSummaries;
                        }
                        
                        // 🔧 DÉDUPLICATION FINALE : Au cas où
                        const deduped = deduplicateAnalyses(newSummaries);
                        console.log(`📊 État final: ${deduped.length} analyses uniques`);
                        
                        return [...deduped];
                    });
                    break;
                    
                default:
                    console.log(`⚠️ Changement non géré pour la collection: ${collection}`);
            }
        };

        realtimeService.onDataUpdated(handleDataUpdate);

    }, [fetchData, fetchClusterMetrics, fetchAnalysisSummaries, fetchUniqueJobs]);

    return { clusterMetrics, analysisSummaries, uniqueJobs, loading, error };
};

// DÉDUPLICATION
// Garde uniquement la version la plus récente de chaque analyse
function deduplicateAnalyses(analyses) {
    const seen = new Map();
    
    analyses.forEach(analysis => {
        const id = analysis._id?.toString() || analysis.analysis_id;
        
        if (!seen.has(id)) {
            seen.set(id, analysis);
        } else {
            // Garder la version avec la date de mise à jour la plus récente
            const existing = seen.get(id);
            const existingDate = new Date(existing.last_update);
            const newDate = new Date(analysis.last_update);
            
            if (newDate > existingDate) {
                seen.set(id, analysis);
            }
        }
    });
    
    return Array.from(seen.values());
}