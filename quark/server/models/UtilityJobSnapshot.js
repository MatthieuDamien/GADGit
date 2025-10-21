const mongoose = require('mongoose');

// Ce schéma est flexible pour accepter n'importe quelle structure de job
const jobSchema = new mongoose.Schema({}, { strict: false});

const utilityJobSnapshotSchema = new mongoose.Schema({
  timestamp: { type: Date, default: Date.now, required: true ,
    // Crée un index TTL. Utilise la variable d'environnement SNAPSHOT_TTL_SECONDS,
    // avec une valeur par défaut de 24h (86400s) si non définie.
    expires: parseInt(process.env.SNAPSHOT_TTL_SECONDS || '86400', 10)
  },
  jobs: {
    type: Map,
    of: jobSchema
  },
  raw_data: {
    squeue_count: Number,
    sacct_count: Number,
    total_jobs: Number
  }
});

module.exports = mongoose.model('UtilityJobSnapshot', utilityJobSnapshotSchema, 'utility_job_snapshots');