// store/taskStore.js
import { create } from 'zustand';

const useTaskStore = create((set, get) => ({
  // État du dialogue
  isDialogOpen: false,
  selectedTask: null,
  taskDetails: null,
  showTimeOptimization: false,
  loading: false,
  error: null,

  // Actions
  openDialog: (task) => {
    console.log('Tâche cliquée:', task.id);
    set({
      isDialogOpen: true,
      selectedTask: task,
      loading: true,
      error: null
    });
    // Simuler le chargement des détails
    get().fetchTaskDetails(task.id);
  },

  closeDialog: () => set({
    isDialogOpen: false,
    selectedTask: null,
    taskDetails: null,
    showTimeOptimization: false,
    error: null
  }),

  toggleTimeOptimization: () => set((state) => ({
    showTimeOptimization: !state.showTimeOptimization
  })),

  // Simulation de récupération des données JSON
  fetchTaskDetails: async (taskId) => {
    try {
      set({ loading: true, error: null });
      
      // Simulation d'un appel API - remplace par ton vrai appel
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Données mockées - remplace par ton vrai JSON
      const mockTaskDetails = {
        id: taskId,
        treatments: [
          {
            id: 'traitement1',
            name: `Traitement 1 pour ${taskId}`,
            status: 'completed',
            duration: '2h22min',
            progress: 100,
            expectedDuration: '3h00min',
            efficiency: 78,
            subtasks: [
              { name: 'djen150', duration: '15ms', status: 'completed' },
              { name: 'djen151', duration: '15ms', status: 'completed' },
              { name: 'djen152', duration: '15ms', status: 'completed' }
            ]
          },
          {
            id: 'traitement2',
            name: `Traitement 2 pour ${taskId}`,
            status: 'running',
            duration: '1h45min',
            progress: 65,
            expectedDuration: '2h30min',
            efficiency: 92,
            subtasks: [
              { name: 'step1', duration: '15ms', status: 'completed' },
              { name: 'step2', duration: '15ms', status: 'running' },
              { name: 'step3', duration: '15ms', status: 'pending' }
            ]
          },
          {
            id: 'traitement3',
            name: `Traitement 3 pour ${taskId}`,
            status: 'pending',
            duration: '0min',
            progress: 0,
            expectedDuration: '35min',
            efficiency: 0,
            subtasks: [
              { name: 'init', duration: '12ms', status: 'pending' },
              { name: 'process', duration: '12ms', status: 'pending' },
              { name: 'finalize', duration: '12ms', status: 'pending' }
            ]
          },
          {
            id: 'traitement4',
            name: `Traitement 4 pour ${taskId}`,
            status: 'error',
            duration: '45min',
            progress: 25,
            expectedDuration: '1h20min',
            efficiency: 31,
            error: 'Erreur interne - Realod fait : 3',
            subtasks: [
              { name: 'prep', duration: '12ms', status: 'completed' },
              { name: 'exec', duration: '12ms', status: 'error' },
              { name: 'cleanup', duration: '12ms', status: 'pending' }
            ]
          }
        ],
        metadata: {
          startTime: '08:23',
          estimatedEndTime: '14:30',
          node: 'gpu-node-01',
          user: 'AutoLauncher',
          priority: 'Normale'
        }
      };

      set({ 
        taskDetails: mockTaskDetails, 
        loading: false 
      });
    } catch (error) {
      set({ 
        error: 'Erreur lors du chargement des détails', 
        loading: false 
      });
    }
  },

  // Utilitaire pour obtenir la couleur selon le statut
  getStatusColor: (status, efficiency = 0) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'running':
        return efficiency > 40 ? 'bg-yellow-500' : 'bg-blue-500';
      case 'error':
        return 'bg-red-500';
      case 'pending':
      default:
        return 'bg-gray-500';
    }
  },

  getStatusText: (status) => {
    switch (status) {
      case 'completed': return 'Terminé';
      case 'running': return 'En cours';
      case 'error': return 'Erreur';
      case 'pending': return 'En attente';
      default: return 'Inconnu';
    }
  }
}));

export default useTaskStore;