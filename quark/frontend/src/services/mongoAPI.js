// src/services/mongoAPI.js
import axios from 'axios';

const mongoAPI = axios.create({
  baseURL: 'http://localhost:5000/api',
});

export const getClusterMetrics = () => {
  return mongoAPI.get('/cluster_snapshots/metrics');
};

// MODIFIÉ: Renommé et mis à jour pour la nouvelle collection/route
export const getUniqueJobs = () => {
  return mongoAPI.get('/unique_jobs');
};

export const getAnalysisSummaries = () => {
  return mongoAPI.get('/analysis_summaries');
};

export const getHealthStatus = () => {
  return mongoAPI.get('/health');
};

export default mongoAPI;
