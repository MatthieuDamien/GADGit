import React, { useState, useEffect } from 'react';
import { Activity, Server, Clock, AlertCircle, Cpu, HardDrive, Zap, CheckIcon } from 'lucide-react';
import { Card, CardHeader, CardContent } from './components/ui/Card';
import { ResourceCard } from './components/dashboard/ResourceCard';
import QueueItem from './components/items/QueueItem';
import ActiveTask from './components/items/ActiveTask';
import ErrorItem from './components/items/ErrorItem';
import CompletedTask from './components/items/CompletedTask';
import Header from './components/dashboard/Header';

const QuarkDashboard = () => {
  // État pour le dark mode
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Vérifier la préférence locale ou système
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('darkMode');
      if (saved !== null) {
        return saved === 'true';
      }
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  // États existants
  const [resources, setResources] = useState({
    cpu: 68,
    memory: 72,
    gpu: 45,
    storage: 89
  });

  const [queue, setQueue] = useState([
    { id: 'djen10010.1', type: 'Genome', priority: 'Urgente', waitTime: '5 min' },
    { id: 'djen10010.2', type: 'Genome', priority: 'Haute', waitTime: '12 min' },
    { id: 'djen10011.1', type: 'Genome', priority: 'Normale', waitTime: '18 min' },
    { id: 'djex20024', type: 'Exome', priority: 'Normale', waitTime: '22 min' },
    { id: 'djenbs104', type: 'Dépistage néonatal', priority: 'Normale', waitTime: '25 min' }
  ]);

  const [activeTasks, setActiveTasks] = useState([
    { id: 'djen12010', type: 'Genome', progress: 35, user: 'Yannis', node: 'gpu-node-01', time: '2h 15min' },
    { id: 'djen20025', type: 'Genome', progress: 45, user: 'AutoLauncher', node: 'cpu-node-03', time: '1h 08min' },
    { id: 'djex19087', type: 'Exome', progress: 8, user: 'NovaSeqX (AL)', node: 'gpu-node-02', time: '3h 42min' },
    { id: 'djenbs19087', type: 'Dépistage néonatal', user: 'AutoLauncher', progress: 54, node: 'gpu-node-04', time: '3h 42min' }
  ]);

  const [errors, setErrors] = useState([
    { id: 'djen20025', type: 'Genome', time: '10:32', message: 'Mémoire insuffisante', severity: 'warning' },
    { id: 'djex18045', type: 'Exome', time: '09:15', message: 'Échec connexion LabKey', severity: 'error' },
    { id: 'djen30012', type: 'Genome', time: '08:47', message: 'Timeout SLURM', severity: 'warning' },
    { id: 'djen30012', type: 'Genome', time: 'hier - 21:12', message: 'Mémoire insuffisante', severity: 'error' }
  ]);

  const [doneTasks, setDoneTasks] = useState([
    { id: 'djen12001', type: 'Genome', node: 'gpu-node-01', timeToBeDone: '2h 15min', time: 'Auj - 08:23' },
    { id: 'djen20002', type: 'Genome', node: 'cpu-node-03', timeToBeDone: '1h 08min', time: 'Hier - 21:32'},
    { id: 'djenbs19008', type: 'Dépistage néonatal', node: 'gpu-node-04', timeToBeDone: '3h 42min', time: 'Hier - 16:12'},
    { id: 'djex19003', type: 'Exome', node: 'gpu-node-02', timeToBeDone: '3h 42min', time: 'Hier - 14:05' },
    { id: 'djenbs19004', type: 'Dépistage néonatal', node: 'gpu-node-04', timeToBeDone: '44min', time: 'Hier - 12:30' },
    { id: 'djen12005', type: 'Genome', node: 'gpu-node-01', timeToBeDone: '2h 15min', time: '08/09/25 - 18:15' },
    { id: 'djen20006', type: 'Genome', node: 'cpu-node-03', timeToBeDone: '1h 08min', time: '08/09/24 - 11:42' },
    { id: 'djex19007', type: 'Exome', node: 'gpu-node-02', timeToBeDone: '3h 42min', time: '08/09/23 - 09:17' },
  ]);

  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Effet pour appliquer/retirer la classe dark sur le document
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    // Sauvegarder la préférence
    localStorage.setItem('darkMode', isDarkMode.toString());
  }, [isDarkMode]);

  // Fonction pour toggle le dark mode
  const handleToggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  // Gestion des clics
  const handleTaskClick = (task) => {
    console.log('Tâche cliquée:', task);
  };

  const handleErrorClick = (error) => {
    console.log('Erreur cliquée:', error);
  };

  // Simulation de mise à jour des données
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date());
      setResources(prev => ({
        cpu: Math.min(100, Math.max(0, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.min(100, Math.max(0, prev.memory + (Math.random() - 0.5) * 8)),
        gpu: Math.min(100, Math.max(0, prev.gpu + (Math.random() - 0.5) * 12)),
        storage: Math.min(100, Math.max(0, prev.storage + (Math.random() - 0.5) * 2))
      }));

      setActiveTasks(prev => prev.map(task => ({
        ...task,
        progress: Math.min(100, task.progress + Math.random() * 2)
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setLastUpdate(new Date());
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-gray-50 
                    dark:from-black dark:via-gray-900 dark:to-black transition-colors duration-300">
      <Header 
        lastUpdate={lastUpdate} 
        onRefresh={handleRefresh} 
        isDarkMode={isDarkMode}
        onToggleDarkMode={handleToggleDarkMode}
      />

      <main className="p-6">
        {/* Grille de ressources */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <ResourceCard 
            label="CPU" 
            icon={Cpu} 
            iconColor="text-primary-light dark:text-primary-dark" 
            value={resources.cpu} 
          />
          <ResourceCard 
            label="Mémoire" 
            icon={Server} 
            iconColor="text-primary-light dark:text-primary-dark" 
            value={resources.memory} 
          />
          <ResourceCard 
            label="GPU" 
            icon={Zap} 
            iconColor="text-primary-light dark:text-primary-dark" 
            value={resources.gpu} 
          />
          <ResourceCard 
            label="Stockage" 
            icon={HardDrive} 
            iconColor="text-primary-light dark:text-primary-dark" 
            value={resources.storage} 
          />
        </section>
        
        {/* Section Erreurs */}
        <section className="mb-6">
          <Card>
            <CardHeader 
              title="Erreurs récentes" 
              icon={AlertCircle} 
              iconColor="text-red-500 dark:text-red-400"
              count={`${errors.length} erreurs`}
            />
            <CardContent>
              {errors.length === 0 ? (
                <div className="text-neutral text-center py-4">Aucune erreur récente.</div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 max-h-60 overflow-y-auto">
                  {errors.map((error, index) => (
                    <ErrorItem 
                      key={`${error.id}-${index}`} 
                      error={error} 
                      onClick={handleErrorClick}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </section>

        {/* Grille principale */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* File d'attente */}
          <Card>
            <CardHeader 
              title="File d'attente" 
              icon={Clock} 
              iconColor="text-orange-400 dark:text-orange-300"
              count={`${queue.length} tâches`}
            />
            <CardContent>
              {queue.length === 0 ? (
                <div className="text-neutral text-center py-4">Aucune tâche en attente.</div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {queue.map((task, index) => (
                    <QueueItem 
                      key={task.id} 
                      task={task} 
                      index={index} 
                      onClick={handleTaskClick}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Tâches en cours */}
          <Card>
            <CardHeader 
              title="Tâches en cours" 
              icon={Activity} 
              iconColor="text-primary-light dark:text-primary-dark"
              count={`${activeTasks.length} actives`}
            />
            <CardContent>
              {activeTasks.length === 0 ? (
                <div className="text-neutral text-center py-4">Aucune tâche en cours.</div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {activeTasks.map(task => (
                    <ActiveTask 
                      key={task.id} 
                      task={task} 
                      onClick={handleTaskClick}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* Tâches terminées */}
        <section>
          <Card>
            <CardHeader 
              title="Tâches terminées" 
              icon={CheckIcon} 
              iconColor="text-green-400 dark:text-green-300"
              count={`${doneTasks.length} tâches terminées durant les 3 derniers mois`}
            />
            <CardContent>
              {doneTasks.length === 0 ? (
                <div className="text-neutral text-center py-4">Aucune tâche terminée récemment.</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-3 max-h-80 overflow-y-auto">
                  {doneTasks.map((task, index) => (
                    <CompletedTask 
                      key={`${task.id}-completed-${index}`} 
                      task={task} 
                      onClick={handleTaskClick}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
};

export default QuarkDashboard;