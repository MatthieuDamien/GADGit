import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { AntiProgressBar } from '../ui/AntiProgressBar';
import { useSlurmData } from '../hooks/UseSlurmData';

// Fonction pour calculer les stats par partition
const getPartitionStats = (sinfo) => {
  const partitions = {};
  sinfo.forEach((node) => {
    const { PARTITION, STATE, NODES_AIOT } = node;
    const [, idle, , total] = NODES_AIOT.split('/').map(Number);

    if (!partitions[PARTITION]) {
      partitions[PARTITION] = {
        totalNodes: 0,
        runningNodes: 0,
        downOrDrainedNodes: 0,
      };
    }

    partitions[PARTITION].totalNodes += total;

    if (STATE === 'running' | STATE === 'idle') { // | STATE === 'idle'
      partitions[PARTITION].runningNodes += idle;
    } else if (STATE === 'down*' || STATE === 'down' || STATE === 'drained' || STATE === 'drained*') {
      partitions[PARTITION].downOrDrainedNodes += total;
    }
  });
  return partitions;
};

// Composant pour afficher une partition
const PartitionCard = ({ partitionName, stats }) => {
  const { totalNodes, runningNodes, downOrDrainedNodes } = stats;
  const runningPercent = totalNodes > 0 ? (runningNodes / totalNodes) * 100 : 0;
  const downPercent = totalNodes > 0 ? (downOrDrainedNodes / totalNodes) * 100 : 0;
  const idleNodes = totalNodes - runningNodes - downOrDrainedNodes;
  const idlePercent = totalNodes > 0 ? (idleNodes / totalNodes) * 100 : 0;
  const allowedRunningNodesPercent = totalNodes > 0 && runningNodes > 0 ? runningNodes/(totalNodes - downOrDrainedNodes)*100 : 0;

  return (
    <Card>
      <CardContent className="">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold mb-2">{partitionName}</h3>
          <h3 className="flex items-end text-gray-600 mb-4 dark:text-gray-400">{parseFloat(allowedRunningNodesPercent).toFixed(2)}%</h3>
        </div>
        <AntiProgressBar
          blueValue={runningPercent}
          redValue ={downPercent}
          idleValue={idlePercent}
        />
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <p className="text-sm text-gray-500">Total Nodes</p>
            <p className="font-bold">{totalNodes}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Running Nodes</p>
            <p className="font-bold">{runningNodes}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Down/Drained Nodes</p>
            <p className="font-bold">{downOrDrainedNodes}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Idle Nodes</p>
            <p className="font-bold">{idleNodes}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};


// Composant principal
const ResourceCard = () => {
  const { loading, error, clusterInfo } = useSlurmData(true, 5000);

  if (error) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 rounded">
        <h3 className="text-red-800">Erreur</h3>
      </div>
    );
  }

  if (loading) {
    return <div className="p-4">Chargement des données SLURM...</div>;
  }

  // Calcul des stats par partition
  const partitionStats = getPartitionStats(clusterInfo);

  // Affichage des cartes par partition
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {Object.entries(partitionStats).map(([partitionName, stats]) => (
        <PartitionCard
          key={partitionName}
          partitionName={partitionName}
          stats={stats}
        />
      ))}
    </div>
  );
};

export { ResourceCard };
