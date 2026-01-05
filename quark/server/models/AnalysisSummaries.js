const mongoose = require('mongoose');

// Schéma pour les informations détaillées d'une analyse
const analysisInfosSchema = new mongoose.Schema({
  sample_id: { type: String, required: true },
  priority: String,
  user_name: String,

  // Timestamps
  created_at: { type: Date },
  started_at: { type: Date },   // Premier job de l'analyse à démarrer
  finished_at: { type: Date },  // Dernier job de l'analyse à finir
  submitted_at: { type: Date }, // Premier job de l'analyse à être soumis
  first_job_start: { type: Date },
  last_job_end: { type: Date },

  // Métriques de temps
  total_time_seconds: Number,
  queue_time_seconds: Number,
  execution_time_seconds: { type: Number, default: 0 },

  // Compteurs de jobs
  jobs_total: { type: Number, default: 0 },
  jobs_running: { type: Number, default: 0 },
  jobs_pending: { type: Number, default: 0 },
  jobs_completed: { type: Number, default: 0 },
  jobs_error: { type: Number, default: 0 },

  // Autres compteurs
  total_reloaded: { type: Number, default: 0 },
  error_count: { type: Number, default: 0 },
  steps_completed: { type: Number, default: 0 },
  steps_total: { type: Number, default: 0 },

  // Erreurs et Ressources
  last_error_message: String,
  node_hours_used: { type: Number, default: 0 },
}, { _id: false }); // _id: false car c'est un sous-document

const analysisSummariesSchema = new mongoose.Schema({
  analysis_id:       { type: String, required: true, unique: true },
  status:            { type: String, enum: ['running', 'error', 'pending', 'completed'], required: true },
  last_update:       { type: Date, default: Date.now, expires: parseInt(process.env.ANALYSES_SUMMARIES_TTL_SECONDS || '21600', 10) },
  infos:             analysisInfosSchema
});

module.exports = mongoose.model('AnalysisSummary', analysisSummariesSchema, 'analysis_summaries');