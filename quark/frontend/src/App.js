import React, { useState, useEffect } from 'react';
import { Activity, Server, Clock, AlertCircle, XCircle, Cpu, HardDrive, Zap, RefreshCw } from 'lucide-react';
import logoQuark from './assets/icons/logoQuark.svg';

// ============== COMPOSANTS RÉUTILISABLES ==============

// Composant Card générique
const Card = ({ children, className = "" }) => (
  <div className={`bg-marine-500/50 backdrop-blur-sm rounded-xl border border-slate-700 ${className}`}>
    {children}
  </div>
);

// En-tête de Card
const CardHeader = ({ title, icon: Icon, iconColor = "text-slate-400", count, children }) => (
  <div className="p-4 border-b border-slate-700">
    <div className="flex items-center justify-between">
      <h2 className="text-lg font-semibold text-white flex items-center gap-2">
        {Icon && <Icon className={`w-5 h-5 ${iconColor}`} />}
        {title}
      </h2>
      {count !== undefined && (
        <span className="text-sm text-slate-400">{count}</span>
      )}
      {children}
    </div>
  </div>
);

// Corps de Card
const CardContent = ({ children, className = "" }) => (
  <div className={`p-4 ${className}`}>
    {children}
  </div>
);

// Composant de statistique de ressource
const ResourceCard = ({ label, icon: Icon, iconColor, value, color }) => {
  const getProgressColor = (val) => {
    if (val > 80) return 'bg-red-500';
    if (val > 60) return 'bg-orange-500';
    return 'bg-green-500';
  };

  return (
    <Card>
      <CardContent>
        <div className="flex items-center justify-between mb-2">
          <span className="text-slate-400 text-sm">{label}</span>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
        <div className="text-2xl font-bold text-white mb-2">{value.toFixed(0)}%</div>
        <ProgressBar value={value} className={getProgressColor(value)} />
      </CardContent>
    </Card>
  );
};

// Barre de progression
const ProgressBar = ({ value, className = "bg-blue-500", height = "h-2" }) => (
  <div className={`w-full bg-slate-700 rounded-full ${height} overflow-hidden`}>
    <div 
      className={`${height} rounded-full transition-all duration-500 ${className}`}
      style={{ width: `${value}%` }}
    />
  </div>
);

// Badge de priorité
const PriorityBadge = ({ priority }) => {
  const getColorClass = () => {
    switch(priority) {
      case 'Urgente': return 'bg-red-500';
      case 'Haute': return 'bg-orange-500';
      case 'Normale': return 'bg-blue-500';
      case 'Basse': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs text-white font-medium ${getColorClass()}`}>
      {priority}
    </span>
  );
};

// Composant d'élément de file d'attente
const QueueItem = ({ task, index }) => (
  <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-600 transition-all duration-200">
    <div className="flex items-center gap-3">
      <span className="text-slate-400 text-sm w-6">#{index + 1}</span>
      <div>
        <div className="text-white font-medium">{task.id}</div>
        <div className="text-slate-400 text-sm">{task.type}</div>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <PriorityBadge priority={task.priority} />
      <span className="text-slate-400 text-sm">{task.waitTime}</span>
    </div>
  </div>
);

// Composant de tâche active
const ActiveTask = ({ task }) => (
  <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
    <div className="flex items-center justify-between mb-2">
      <div>
        <div className="text-white font-medium">{task.id}</div>
        <div className="text-slate-400 text-sm">{task.type} • {task.node}</div>
      </div>
      <div className="text-right">
        <div className="text-cyan-400 font-medium">{task.progress}%</div>
        <div className="text-slate-400 text-sm">{task.time}</div>
      </div>
    </div>
    <ProgressBar 
      value={task.progress} 
      className="bg-gradient-to-r from-cyan-400 to-blue-500"
    />
  </div>
);

// Composant d'erreur
const ErrorItem = ({ error }) => {
  const getSeverityColor = () => {
    switch(error.severity) {
      case 'error': return 'text-red-500';
      case 'warning': return 'text-orange-500';
      default: return 'text-blue-500';
    }
  };

  const IconComponent = error.severity === 'error' ? XCircle : AlertCircle;

  return (
    <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700">
      <div className="flex items-center gap-3">
        <IconComponent className={`w-5 h-5 ${getSeverityColor()}`} />
        <div>
          <div className="text-white font-medium">{error.id} - {error.type}</div>
          <div className="text-slate-400 text-sm">{error.message}</div>
        </div>
      </div>
      <span className="text-slate-400 text-sm whitespace-nowrap">{error.time}</span>
    </div>
  );
};

// Composant Header
const Header = ({ lastUpdate, onRefresh }) => (
  <header className="border-b border-jaune-500 bg-marine-500/50 backdrop-blur-sm">
    <div className="px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 bg-gradient-to-br from-gray-400 to-gray-500 rounded-lg flex items-center justify-center shadow-lg">
            <img src={logoQuark} className="w-10 h-10" alt="Logo Quark" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-100 to-gray-300 bg-clip-text text-transparent">
              Quark
            </h1>
          </div>
          <span className="text-sm text-slate-400 ml-2 hidden sm:inline">
            Orchestrateur de calcul bioinformatique
          </span>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={onRefresh}
            className="p-2 hover:bg-marine-600 rounded-lg transition-colors"
            aria-label="Rafraîchir"
          >
            <RefreshCw className="w-5 h-5 text-slate-400" />
          </button>
          <div className="text-sm text-slate-400">
            MAJ: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  </header>
);

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
    { id: 'PED12010', type: 'Genome', progress: 35, node: 'gpu-node-01', time: '2h 15min' },
    { id: 'PED20025', type: 'Genome', progress: 45, node: 'cpu-node-03', time: '1h 08min' },
    { id: 'djex19087', type: 'Exome', progress: 8, node: 'gpu-node-02', time: '3h 42min' },
    { id: 'djen19087', type: 'Dépistage néonatal', progress: 54, node: 'gpu-node-04', time: '3h 42min' }
  ]);

  const [errors, setErrors] = useState([
    { id: 'PED20025', type: 'Genome 2', time: '10:32', message: 'Mémoire insuffisante', severity: 'warning' },
    { id: 'djex18045', type: 'Exome', time: '09:15', message: 'Échec connexion LabKey', severity: 'error' },
    { id: 'PED30012', type: 'Genome', time: '08:47', message: 'Timeout SLURM', severity: 'warning' },
    { id: 'PED30012', type: 'Genome', time: 'hier - 21:12(', message: 'Timeout SLURM', severity: 'warning' }
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
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
      </main>
    </div>
  );
};

export default QuarkDashboard;