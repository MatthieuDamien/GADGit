// components/dialogs/TaskDialog.jsx
import React from 'react';
import { X, Clock, CheckCircle, AlertCircle, Loader2, Timer } from 'lucide-react';
import useTaskStore from '../../store/taskStore';

const TaskDialog = () => {
  const {
    isDialogOpen,
    selectedTask,
    taskDetails,
    showTimeOptimization,
    loading,
    error,
    closeDialog,
    toggleTimeOptimization,
    getStatusColor,
    getStatusText
  } = useTaskStore();

  console.log('isDialogOpen:', isDialogOpen);
  if (!isDialogOpen) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'pending':
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getEfficiencyColor = (efficiency) => {
    if (efficiency >= 80) return 'text-green-400';
    if (efficiency >= 60) return 'text-yellow-400';
    if (efficiency >= 40) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-marine-500/90 backdrop-blur-sm rounded-xl border border-slate-700 w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-white">
              Détails de la tâche: {selectedTask?.id}
            </h2>
            {selectedTask && (
              <span className="text-sm text-slate-400">
                {selectedTask.type} - {selectedTask.node}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTimeOptimization}
              className={`flex items-center gap-2 px-3 py-1 rounded-lg transition-colors ${
                showTimeOptimization 
                  ? 'bg-green-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <Timer className="w-4 h-4" />
              <span className="text-sm">
                {showTimeOptimization ? 'Temps affiché' : 'Afficher temps'}
              </span>
            </button>
            <button
              onClick={closeDialog}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-80px)]">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
              <span className="ml-2 text-slate-400">Chargement des détails...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <span className="text-red-400 font-medium">Erreur</span>
              </div>
              <p className="text-red-300 mt-1">{error}</p>
            </div>
          )}

          {taskDetails && (
            <div className="space-y-6">
              {/* Métadonnées */}
              <div className="bg-slate-900/50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-3">Informations générales</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-slate-400">Début:</span>
                    <div className="text-white font-medium">{taskDetails.metadata.startTime}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Fin estimée:</span>
                    <div className="text-white font-medium">{taskDetails.metadata.estimatedEndTime}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Utilisateur:</span>
                    <div className="text-white font-medium">{taskDetails.metadata.user}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Priorité:</span>
                    <div className="text-white font-medium">{taskDetails.metadata.priority}</div>
                  </div>
                </div>
              </div>

              {/* Traitements */}
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Traitements</h3>
                <div className="space-y-4">
                  {taskDetails.treatments.map((treatment, index) => (
                    <div key={treatment.id} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                      {/* Header du traitement */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-slate-400 text-sm">Traitement {index + 1}</span>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(treatment.status)}
                            <span className="text-white font-medium">{treatment.name}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          {showTimeOptimization && (
                            <div className="text-right">
                              <div className="text-slate-400">Efficacité</div>
                              <div className={`font-medium ${getEfficiencyColor(treatment.efficiency)}`}>
                                {treatment.efficiency}%
                              </div>
                            </div>
                          )}
                          <div className="text-right">
                            <div className="text-slate-400">Durée</div>
                            <div className="text-white font-medium">{treatment.duration}</div>
                            {showTimeOptimization && (
                              <div className="text-xs text-slate-500">
                                / {treatment.expectedDuration}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Barre de progression */}
                      <div className="mb-3">
                        <div className="flex justify-between text-xs text-slate-400 mb-1">
                          <span>Progression</span>
                          <span>{treatment.progress}%</span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-500 ${getStatusColor(treatment.status, treatment.efficiency)}`}
                            style={{ width: `${treatment.progress}%` }}
                          />
                        </div>
                      </div>

                      {/* Erreur si présente */}
                      {treatment.error && (
                        <div className="bg-red-900/30 border border-red-700/50 rounded p-2 mb-3">
                          <div className="flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-red-400" />
                            <span className="text-red-400 text-sm font-medium">Erreur:</span>
                            <span className="text-red-300 text-sm">{treatment.error}</span>
                          </div>
                        </div>
                      )}

                      {/* Sous-tâches avec temps si activé */}
                      {showTimeOptimization && (
                        <div className="mt-3">
                          <div className="text-sm text-slate-400 mb-2">Sous-tâches:</div>
                          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                            {treatment.subtasks.map((subtask, subIndex) => (
                              <div 
                                key={subIndex}
                                className={`p-2 rounded text-center text-xs ${getStatusColor(subtask.status)}`}
                              >
                                <div className="text-white font-medium">{subtask.name}</div>
                                <div className="text-white/80">{subtask.duration}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Suggestions d'optimisation */}
              {showTimeOptimization && (
                <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-4">
                  <h4 className="text-yellow-400 font-medium mb-2">💡 Suggestions d'optimisation</h4>
                  <ul className="text-sm text-yellow-200 space-y-1">
                    <li>• Le traitement 4 présente une faible efficacité (31%)</li>
                    <li>• Considérer l'allocation de plus de mémoire pour éviter les erreurs</li>
                    <li>• Le traitement 1 pourrait être optimisé (78% d'efficacité)</li>
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskDialog;