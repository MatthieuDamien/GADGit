import React from 'react';
import { Card, CardContent, CardTitle } from '../ui/Card';
import { ProgressBar} from '../ui/ProgressBar';

const PartitionCard = ({ partitionName, stats }) => {
  const { nodes, cpus, gpus } = stats;
  const totalNodes = nodes.total;
  const runningNodes = nodes.allocated;
  const downOrDrainedNodes = nodes.other;

  const runningPercent = totalNodes > 0 ? (runningNodes / totalNodes) * 100 : 0;
  const downPercent = totalNodes > 0 ? (downOrDrainedNodes / totalNodes) * 100 : 0;
  const idleNodes = totalNodes - runningNodes - downOrDrainedNodes;
  const idlePercent = totalNodes > 0 ? (idleNodes / totalNodes) * 100 : 0;
  const allowedRunningNodesPercent = totalNodes > 0 && runningNodes > 0 ? runningNodes / (totalNodes - downOrDrainedNodes) * 100 : 0;

  // Détermine dynamiquement le nombre de colonnes pour la grille
  const gridColsClass = gpus.total > 0 ? 'grid-cols-3' : 'grid-cols-2';

  return (
    <Card className="shadow-md pt-6">
      <CardContent>
        <div className="flex justify-between items-center mb-4">
          <CardTitle>{partitionName}</CardTitle>
          <div className="text-gray-11 dark:text-gray-11">{parseFloat(allowedRunningNodesPercent).toFixed(2)}%</div>
        </div>
        <ProgressBar
          allocatedValue={runningPercent}
          otherValue={downPercent}
          idleValue={idlePercent}
        />
        {/* Utilise la classe dynamique pour la grille */}
        <div className={`grid ${gridColsClass} gap-4 mt-4`}>
          <div className="text-center">
            <p className="text-sm text-gray-11 dark:text-gray-11">Total Nodes</p>
            <p className="font-bold text-gray-12 dark:text-gray-12">{runningNodes}/{totalNodes - downOrDrainedNodes}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-11 dark:text-gray-11">CPUs</p>
            <p className="font-bold text-gray-12 dark:text-gray-12">{cpus.allocated}/{cpus.total - cpus.other}</p>
          </div>
          {gpus.total > 0 && (
            <div className="text-center"> 
              <p className="text-sm text-gray-11 dark:text-gray-11">GPUs</p>
              <p className="font-bold text-gray-12 dark:text-gray-12">{gpus.allocated}/{gpus.total - gpus.other}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Composant principal
const ResourceCard = ({ metrics }) => {
  if (!metrics || !metrics.partitions) {
    return (
      <div className="p-4 text-center text-gray-11 dark:text-gray-11">
        Aucune donnée de partition disponible.
      </div>
    );
  }

  const getGridLayoutClass = (count) => {
    switch (count) {
      case 1:
        return "grid grid-cols-1 gap-4 justify-center";
      case 2:
        return "grid grid-cols-1 md:grid-cols-2 gap-4 justify-center";
      case 3:
      case 5:
      case 6:
        return "grid grid-cols-1 md:grid-cols-3 gap-4 justify-center";
      default: // 4, 7, 8, etc.
        return "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 justify-center";
    }
  };

  // Affichage des cartes par partition
  return (
    <div className={getGridLayoutClass(Object.keys(metrics.partitions).length)}>
      {Object.entries(metrics.partitions).map(([partitionName, stats]) => (
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
