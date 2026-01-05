// src/components/dashboard/AnalysisSectionParent.jsx - VERSION AVEC DEBUG
import React, { useMemo, useEffect, useRef } from 'react';
import AnalysisSection from './AnalysisSection';
import { Zap, AlertTriangle, Clock, CheckCircle } from 'lucide-react';

function AnalysisSectionParent({ analyses }) {
    // // 🔍 DÉBOGAGE : Compteur de renders
    // const renderCount = useRef(0);
    // renderCount.current += 1;

    // // 🔍 DÉBOGAGE : Log à chaque render
    // console.log(`🔵 AnalysisSectionParent render #${renderCount.current}:`, {
    //     totalAnalyses: analyses?.length || 0,
    //     hasAnalyses: !!analyses,
    //     firstAnalysis: analyses?.[0]?.analysis_id
    // });

    // // 🔍 DÉBOGAGE : Détecte les changements de analyses
    // useEffect(() => {
    //     console.log('🔄 AnalysisSectionParent - analyses prop a changé !', {
    //         count: analyses?.length || 0,
    //         analyses: analyses?.map(a => ({ id: a.analysis_id, status: a.status }))
    //     });
    // }, [analyses]);

    // ✅ UTILISER useMemo pour filtrer les analyses
    // Cela se recalcule automatiquement quand analyses change
    const categorizedAnalyses = useMemo(() => {
        // console.log('♻️ useMemo categorizedAnalyses recalculé');

        if (!Array.isArray(analyses)) {
            // console.warn('⚠️ analyses n\'est pas un array');
            return {
                running: [],
                completed: [],
                failed: [],
                pending: []
            };
        }

        const running = analyses.filter(a => a.status === 'running');
        const completed = analyses.filter(a => a.status === 'completed');
        const failed = analyses.filter(a => a.status === 'error');
        const pending = analyses.filter(a => a.status === 'pending');

        // console.log('📊 Analyses catégorisées:', {
        //     running: running.length,
        //     completed: completed.length,
        //     failed: failed.length,
        //     pending: pending.length
        // });

        return { running, completed, failed, pending };
    }, [analyses]);

    return (
        <section>
            <h1 className="text-3xl font-bold mb-6">Analyses</h1>
            <AnalysisSection 
                title="En Cours" 
                analyses={categorizedAnalyses.running} 
            />
            <AnalysisSection 
                title="En Erreur" 
                analyses={categorizedAnalyses.failed} 
            />
            <AnalysisSection 
                title="En Attente" 
                analyses={categorizedAnalyses.pending} 
            />
            <AnalysisSection 
                title="Terminées Récemment" 
                analyses={categorizedAnalyses.completed}  
            />
        </section>
    );
}

export default AnalysisSectionParent;