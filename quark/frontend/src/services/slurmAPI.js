// services/slurmAPI.js
const API_BASE_URL = 'http://localhost:5000/api';

class slurmAPI {
  // Vérifier la santé de l'API
  static async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return await response.json();
    } catch (error) {
      console.error('Erreur health check:', error);
      throw error;
    }
  }

  // Récupérer toutes les données SLURM
  static async getAllData() {
    try {
      const response = await fetch(`${API_BASE_URL}/slurm/all`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Erreur récupération données:', error);
      throw error;
    }
  }

  // Récupérer uniquement les données sacct
  static async getSacctData() {
    try {
      const response = await fetch(`${API_BASE_URL}/slurm/sacct`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Erreur récupération sacct:', error);
      throw error;
    }
  }

  // Récupérer uniquement les données squeue
  static async getSqueueData() {
    try {
      const response = await fetch(`${API_BASE_URL}/slurm/squeue`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Erreur récupération squeue:', error);
      throw error;
    }
  }

  // Forcer le rafraîchissement des données
  static async refreshData() {
    try {
      const response = await fetch(`${API_BASE_URL}/slurm/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Erreur rafraîchissement:', error);
      throw error;
    }
  }

  // Récupérer les détails d'un job
  static async getJobDetails(jobId) {
    try {
      const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Erreur récupération job:', error);
      throw error;
    }
  }
}
export default slurmAPI;