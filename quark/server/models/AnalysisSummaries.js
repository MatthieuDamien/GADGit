const mongoose = require('mongoose');

// Schéma pour les informations détaillées d'une analyse
const analysisInfosSchema = new mongoose.Schema({
  sample_id: { type: String, required: true },
  priority: String,
  user_name: String,

  // Timestamps
  created_at: Date,
  started_at: Date,
  finished_at: Date,

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
  last_update:       { type: Date, default: Date.now,
    // Crée un index TTL. Utilise la variable d'environnement SUMMARIES_TTL_SECONDS,
    // avec une valeur par défaut de 7 jours (604800s) si non définie.
    expires: parseInt(process.env.SUMMARIES_TTL_SECONDS || '604800', 10)
  },
  infos:             analysisInfosSchema
});

module.exports = mongoose.model('AnalysisSummary', analysisSummariesSchema, 'analysis_summaries');