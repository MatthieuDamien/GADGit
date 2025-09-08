import React, { useState, useEffect } from 'react';
import { Activity, Server, Clock, AlertCircle, Cpu, HardDrive, Zap } from 'lucide-react';
import { Card, CardHeader, CardContent } from './components/ui/Card';
import { ResourceCard } from './components/dashboard/ResourceCard';
import PriorityBadge from './components/ui/PriorityBadge';
import QueueItem from './components/items/QueueItem';
import ActiveTask from './components/items/ActiveTask';
import ErrorItem from './components/items/ErrorItem';
import Header from './components/dashboard/Header';


// ============== COMPOSANT PRINCIPAL ==============

const QuarkDashboard = () => {
  // États
  const [resources, setResources] = useState({
    cpu: 68,
    memory: 72,
    gpu: 45,
    storage: 89
  });

  const [queue, setQueue] = useState([
    { id: 'PED10010.1', type: 'Genome', priority: 'Urgente', waitTime: '5 min' },
    { id: 'PED10010.2', type: 'Genome', priority: 'Haute', waitTime: '12 min' },
    { id: 'PED10011.1', type: 'Genome', priority: 'Normale', waitTime: '18 min' },
    { id: 'djex20024', type: 'Exome', priority: 'Normale', waitTime: '22 min' },
    { id: 'djenbs104', type: 'Dépistage néonatal', priority: 'Normale', waitTime: '25 min' }
  ]);

  const [activeTasks, setActiveTasks] = useState([
    { id: 'PED12010', type: 'Genome', progress: 35, user: 'Yannis', node: 'gpu-node-01', time: '2h 15min' },
    { id: 'PED20025', type: 'Genome', progress: 45, user: 'AutoLauncher', node: 'cpu-node-03', time: '1h 08min' },
    { id: 'djex19087', type: 'Exome', progress: 8, user: 'AutoLauncher', node: 'gpu-node-02', time: '3h 42min' },
    { id: 'djen19087', type: 'Dépistage néonatal', user: 'AutoLauncher', progress: 54, node: 'gpu-node-04', time: '3h 42min' }
  ]);

  const [errors, setErrors] = useState([
    { id: 'PED20025', type: 'Genome', time: '10:32', message: 'Mémoire insuffisante', severity: 'warning' },
    { id: 'djex18045', type: 'Exome', time: '09:15', message: 'Échec connexion LabKey', severity: 'error' },
    { id: 'PED30012', type: 'Genome', time: '08:47', message: 'Timeout SLURM', severity: 'warning' },
    { id: 'PED30012', type: 'Genome', time: 'hier - 21:12', message: 'Mémoire insuffisante', severity: 'error' }
  ]);

  const [lastUpdate, setLastUpdate] = useState(new Date());


  // Simulation de mise à jour des données
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date());
      // Simulation de variations des ressources
      setResources(prev => ({
        cpu: Math.min(100, Math.max(0, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.min(100, Math.max(0, prev.memory + (Math.random() - 0.5) * 8)),
        gpu: Math.min(100, Math.max(0, prev.gpu + (Math.random() - 0.5) * 12)),
        storage: Math.min(100, Math.max(0, prev.storage + (Math.random() - 0.5) * 2))
      }));

      // Mise à jour des progressions des tâches
      setActiveTasks(prev => prev.map(task => ({
        ...task,
        progress: Math.min(100, task.progress + Math.random() * 2)
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setLastUpdate(new Date());
    // Logique de rafraîchissement
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-marine-100 via-slate-700 to-marine-100">
      <Header lastUpdate={lastUpdate} onRefresh={handleRefresh} />

      <main className="p-6">
        {/* Grille de ressources */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <ResourceCard 
            label="CPU" 
            icon={Cpu} 
            iconColor="text-cyan-400" 
            value={resources.cpu}
          />
          <ResourceCard 
            label="Mémoire" 
            icon={Server} 
            iconColor="text-blue-400" 
            value={resources.memory}
          />
          <ResourceCard 
            label="GPU" 
            icon={Zap} 
            iconColor="text-green-400" 
            value={resources.gpu}
          />
          <ResourceCard 
            label="Stockage" 
            icon={HardDrive} 
            iconColor="text-purple-400" 
            value={resources.storage}
          />
        </section>
        
        {/* Section Erreurs */}
        <section className="mt-6">
          <Card>
            <CardHeader 
              title="Erreurs récentes" 
              icon={AlertCircle} 
              iconColor="text-red-400"
              count={`${errors.length} erreurs`}
            />
            <CardContent>
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {errors.map((error, index) => (
                  <ErrorItem key={index} error={error} />
                ))}
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Grille principale */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* File d'attente */}
          <Card>
            <CardHeader 
              title="File d'attente" 
              icon={Clock} 
              iconColor="text-cyan-400"
              count={`${queue.length} tâches`}
            />
            <CardContent>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {queue.map((task, index) => (
                  <QueueItem key={task.id} task={task} index={index} />
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Tâches en cours */}
          <Card>
            <CardHeader 
              title="Tâches en cours" 
              icon={Activity} 
              iconColor="text-green-400"
              count={`${activeTasks.length} actives`}
            />
            <CardContent>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {activeTasks.map(task => (
                  <ActiveTask key={task.id} task={task} />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

      </main>
    </div>
  );
};

export default QuarkDashboard;