// src/components/hooks/ClusterMetrics.jsx
import React from 'react';
import { useRealtimeData } from './useRealtimeData'; // Import du hook central
import { ResourceCard } from '../dashboard/ResourceCard';
import { Activity, Cpu, Gpu, Server } from 'lucide-react';

function ClusterMetrics() {
  // Récupération des données temps réel 
  const { 
    clusterMetrics: metrics, 
    loading, 
    error 
  } = useRealtimeData(); 

  // La logique de chargement et d'erreur est gérée par le hook
  if (loading) return <div className="text-center p-4">Chargement des métriques...</div>;
  if (error && !metrics) return <div className="text-center p-4 text-red-500">Erreur de chargement: {error}</div>;
  if (!metrics) return null;

  const { totals, jobs } = metrics;

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
        <InfoBox icon={Activity} title="Jobs Actifs" value={`${jobs.running} Running / ${jobs.pending} Pending`} />
        <InfoBox icon={Server}   title="Nœuds" value={`${totals.nodes.allocated} / ${totals.nodes.total-totals.nodes.other}`} />
        <InfoBox icon={Cpu} title="CPUs Alloués" value={`${totals.cpus.allocated} / ${totals.cpus.total-totals.cpus.other}`} />
        <InfoBox icon={Gpu} title="GPUs Alloués" value={`${totals.gpus.allocated} / ${totals.gpus.total-totals.gpus.other}`} />
      </div>
      <ResourceCard metrics={metrics} />
    </>
  );
}

const InfoBox = ({ icon: Icon, title, value }) => (
  <div className="p-4 rounded-lg shadow-md flex items-center bg-gray-2 dark:bg-gray-3">
    <Icon className="h-8 w-8 text-blue-11 dark:text-lime-11 mr-4" />
    <div>
      <p className="text-sm text-gray-11 dark:text-lime-11">{title}</p>
      <p className="text-lg font-bold text-gray-12 dark:text-white">{value}</p>
    </div>
  </div>
);

export default ClusterMetrics;