import React, { useState, useEffect } from 'react';
import { Activity, Server, Clock, AlertCircle, CheckCircle, XCircle, Cpu, HardDrive, Zap, Users, FileText, RefreshCw } from 'lucide-react';

const QuarkDashboard = () => {
  // États pour les données du dashboard
  const [resources, setResources] = useState({
    cpu: 68,
    memory: 72,
    gpu: 45,
    storage: 89
  });

  const [queue, setQueue] = useState([
    { id: 'PED10010.1', type: 'Genome', priority: 'Haute', waitTime: '5 min' },
    { id: 'PED10010.2', type: 'Genome', priority: 'Normale', waitTime: '12 min' },
    { id: 'PED10011.1', type: 'Genome', priority: 'Normale', waitTime: '18 min' },
    { id: 'djex20024', type: 'Exome', priority: 'Haute', waitTime: '22 min' },
    { id: 'djenbs104', type: 'Dépistage néonatal', priority: 'Urgente', waitTime: '25 min' }
  ]);

  const [activeTasks, setActiveTasks] = useState([
    { id: 'PED12010', type: 'Genome', progress: 75, node: 'gpu-node-01', time: '2h 15min' },
    { id: 'PED20025', type: 'Genome', progress: 45, node: 'cpu-node-03', time: '1h 08min' },
    { id: 'djex19087', type: 'Exome', progress: 92, node: 'gpu-node-02', time: '3h 42min' }
  ]);

  const [errors, setErrors] = useState([
    { id: 'PED20025', type: 'Genome 2', time: '10:32', message: 'Mémoire insuffisante', severity: 'warning' },
    { id: 'djex18045', type: 'Exome', time: '09:15', message: 'Échec connexion LabKey', severity: 'error' },
    { id: 'PED30012', type: 'Genome', time: '08:47', message: 'Timeout SLURM', severity: 'warning' }
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
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getProgressColor = (value) => {
    if (value > 80) return '#ef4444';
    if (value > 60) return '#f59e0b';
    return '#10b981';
  };

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'error': return '#ef4444';
      case 'warning': return '#f59e0b';
      default: return '#3b82f6';
    }
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      'Urgente': 'bg-red-500',
      'Haute': 'bg-orange-500',
      'Normale': 'bg-blue-500',
      'Basse': 'bg-gray-500'
    };
    return colors[priority] || 'bg-gray-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                Quark
              </h1>
              <span className="text-sm text-slate-400 ml-2">Orchestrateur de calcul médical</span>
            </div>
            <div className="flex items-center space-x-4">
              <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                <RefreshCw className="w-5 h-5 text-slate-400" />
              </button>
              <div className="text-sm text-slate-400">
                Dernière MAJ: {lastUpdate.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="p-6">
        {/* Statistiques principales */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">CPU</span>
              <Cpu className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-white mb-2">{resources.cpu.toFixed(0)}%</div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div 
                className="h-2 rounded-full transition-all duration-500"
                style={{
                  width: `${resources.cpu}%`,
                  backgroundColor: getProgressColor(resources.cpu)
                }}
              />
            </div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Mémoire</span>
              <Server className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white mb-2">{resources.memory.toFixed(0)}%</div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div 
                className="h-2 rounded-full transition-all duration-500"
                style={{
                  width: `${resources.memory}%`,
                  backgroundColor: getProgressColor(resources.memory)
                }}
              />
            </div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">GPU</span>
              <Zap className="w-4 h-4 text-green-400" />
            </div>
            <div className="text-2xl font-bold text-white mb-2">{resources.gpu.toFixed(0)}%</div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div 
                className="h-2 rounded-full transition-all duration-500"
                style={{
                  width: `${resources.gpu}%`,
                  backgroundColor: getProgressColor(resources.gpu)
                }}
              />
            </div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Stockage</span>
              <HardDrive className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white mb-2">{resources.storage.toFixed(0)}%</div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div 
                className="h-2 rounded-full transition-all duration-500"
                style={{
                  width: `${resources.storage}%`,
                  backgroundColor: getProgressColor(resources.storage)
                }}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* File d'attente */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700">
            <div className="p-4 border-b border-slate-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white flex items-center">
                  <Clock className="w-5 h-5 mr-2 text-cyan-400" />
                  File d'attente
                </h2>
                <span className="text-sm text-slate-400">{queue.length} tâches</span>
              </div>
            </div>
            <div className="p-4">
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {queue.map((task, index) => (
                  <div key={task.id} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors">
                    <div className="flex items-center space-x-3">
                      <span className="text-slate-400 text-sm w-6">#{index + 1}</span>
                      <div>
                        <div className="text-white font-medium">{task.id}</div>
                        <div className="text-slate-400 text-sm">{task.type}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs text-white ${getPriorityBadge(task.priority)}`}>
                        {task.priority}
                      </span>
                      <span className="text-slate-400 text-sm">{task.waitTime}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tâches en cours */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700">
            <div className="p-4 border-b border-slate-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white flex items-center">
                  <Activity className="w-5 h-5 mr-2 text-green-400" />
                  Tâches en cours
                </h2>
                <span className="text-sm text-slate-400">{activeTasks.length} actives</span>
              </div>
            </div>
            <div className="p-4">
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {activeTasks.map((task) => (
                  <div key={task.id} className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
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
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-500"
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Erreurs */}
        <div className="mt-6 bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700">
          <div className="p-4 border-b border-slate-700">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white flex items-center">
                <AlertCircle className="w-5 h-5 mr-2 text-red-400" />
                Erreurs récentes
              </h2>
              <span className="text-sm text-slate-400">{errors.length} erreurs</span>
            </div>
          </div>
          <div className="p-4">
            <div className="space-y-3 max-h-60 overflow-y-auto">
              {errors.map((error, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                  <div className="flex items-center space-x-3">
                    {error.severity === 'error' ? 
                      <XCircle className="w-5 h-5" style={{ color: getSeverityColor(error.severity) }} /> :
                      <AlertCircle className="w-5 h-5" style={{ color: getSeverityColor(error.severity) }} />
                    }
                    <div>
                      <div className="text-white font-medium">{error.id} - {error.type}</div>
                      <div className="text-slate-400 text-sm">{error.message}</div>
                    </div>
                  </div>
                  <span className="text-slate-400 text-sm">{error.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuarkDashboard;