import React, { useState, useEffect } from 'react';
import { Activity, Server, Clock, AlertCircle, CheckCircle, XCircle, Cpu, HardDrive, Zap, Users, FileText, RefreshCw } from 'lucide-react';
import './App.css'; // Import du fichier CSS

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

  const getPriorityClass = (priority) => {
    const classes = {
      'Urgente': 'priority-urgent',
      'Haute': 'priority-high',
      'Normale': 'priority-normal',
      'Basse': 'priority-low'
    };
    return classes[priority] || 'priority-normal';
  };

  return (
    <div className="quark-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <div className="logo">
              <Zap className="logo-icon" />
            </div>
            <h1 className="app-title">Quark</h1>
            <span className="app-subtitle">Orchestrateur de calcul médical</span>
          </div>
          <div className="header-right">
            <button className="refresh-btn">
              <RefreshCw className="refresh-icon" />
            </button>
            <div className="last-update">
              Dernière MAJ: {lastUpdate.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Statistiques principales */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-label">CPU</span>
              <Cpu className="stat-icon cpu-icon" />
            </div>
            <div className="stat-value">{resources.cpu.toFixed(0)}%</div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{
                  width: `${resources.cpu}%`,
                  backgroundColor: getProgressColor(resources.cpu)
                }}
              />
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-label">Mémoire</span>
              <Server className="stat-icon memory-icon" />
            </div>
            <div className="stat-value">{resources.memory.toFixed(0)}%</div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{
                  width: `${resources.memory}%`,
                  backgroundColor: getProgressColor(resources.memory)
                }}
              />
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-label">GPU</span>
              <Zap className="stat-icon gpu-icon" />
            </div>
            <div className="stat-value">{resources.gpu.toFixed(0)}%</div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{
                  width: `${resources.gpu}%`,
                  backgroundColor: getProgressColor(resources.gpu)
                }}
              />
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-label">Stockage</span>
              <HardDrive className="stat-icon storage-icon" />
            </div>
            <div className="stat-value">{resources.storage.toFixed(0)}%</div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{
                  width: `${resources.storage}%`,
                  backgroundColor: getProgressColor(resources.storage)
                }}
              />
            </div>
          </div>
        </div>

        <div className="main-grid">
          {/* File d'attente */}
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">
                <Clock className="panel-icon queue-icon" />
                File d'attente
              </h2>
              <span className="panel-count">{queue.length} tâches</span>
            </div>
            <div className="panel-content">
              <div className="queue-list">
                {queue.map((task, index) => (
                  <div key={task.id} className="queue-item">
                    <div className="queue-item-left">
                      <span className="queue-number">#{index + 1}</span>
                      <div className="queue-info">
                        <div className="queue-id">{task.id}</div>
                        <div className="queue-type">{task.type}</div>
                      </div>
                    </div>
                    <div className="queue-item-right">
                      <span className={`priority-badge ${getPriorityClass(task.priority)}`}>
                        {task.priority}
                      </span>
                      <span className="queue-time">{task.waitTime}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tâches en cours */}
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">
                <Activity className="panel-icon active-icon" />
                Tâches en cours
              </h2>
              <span className="panel-count">{activeTasks.length} actives</span>
            </div>
            <div className="panel-content">
              <div className="tasks-list">
                {activeTasks.map((task) => (
                  <div key={task.id} className="task-item">
                    <div className="task-header">
                      <div className="task-info">
                        <div className="task-id">{task.id}</div>
                        <div className="task-details">{task.type} • {task.node}</div>
                      </div>
                      <div className="task-stats">
                        <div className="task-progress">{task.progress}%</div>
                        <div className="task-time">{task.time}</div>
                      </div>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill task-progress-fill"
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
        <div className="panel errors-panel">
          <div className="panel-header">
            <h2 className="panel-title">
              <AlertCircle className="panel-icon error-icon" />
              Erreurs récentes
            </h2>
            <span className="panel-count">{errors.length} erreurs</span>
          </div>
          <div className="panel-content">
            <div className="errors-list">
              {errors.map((error, index) => (
                <div key={index} className="error-item">
                  <div className="error-left">
                    {error.severity === 'error' ? 
                      <XCircle className="error-severity-icon" style={{ color: getSeverityColor(error.severity) }} /> :
                      <AlertCircle className="error-severity-icon" style={{ color: getSeverityColor(error.severity) }} />
                    }
                    <div className="error-info">
                      <div className="error-id">{error.id} - {error.type}</div>
                      <div className="error-message">{error.message}</div>
                    </div>
                  </div>
                  <span className="error-time">{error.time}</span>
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