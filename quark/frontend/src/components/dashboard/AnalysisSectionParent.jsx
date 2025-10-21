// src/components/dashboard/AnalysisSectionParent.jsx
import React from 'react';
import AnalysisSection from './AnalysisSection';
import { Zap, AlertTriangle, Clock, CheckCircle } from 'lucide-react';

function AnalysisSectionParent({ analyses }) {
    // Ce composant ne fait plus que filtrer et afficher les données reçues.
    // Les statuts sont en minuscules pour correspondre à App.jsx
    const runningAnalyses = analyses.filter(a => a.status === 'running');
    const completedAnalyses = analyses.filter(a => a.status === 'completed');
    const failedAnalyses = analyses.filter(a => a.status === 'error');
    const pendingAnalyses = analyses.filter(a => a.status === 'pending');
    
    return (
        <>
            <AnalysisSection 
                title="Analyses en Cours" 
                analyses={runningAnalyses} 
                icon={Zap} 
            />
            <AnalysisSection 
                title="En Erreur" 
                analyses={failedAnalyses} 
                icon={AlertTriangle} 
            />
            <AnalysisSection 
                title="Analyses en Attente" 
                analyses={pendingAnalyses} 
                icon={Clock} 
            />
            <AnalysisSection 
                title="Terminées Récemment" 
                analyses={completedAnalyses} 
                icon={CheckCircle} 
            />
        </>
    );
}

export default AnalysisSectionParent;