const mongoose = require('mongoose');

// Schéma flexible pour un job unique.
// Pas de TTL ici, car on veut garder l'historique complet de ces jobs.
const uniqueJobSchema = new mongoose.Schema({
  JOBID: { type: String, unique: true, required: true },
  // Le reste des champs sont flexibles pour s'adapter aux données de Slurm.
}, { strict: false });

// Le troisième argument spécifie le nom de la collection.
module.exports = mongoose.model('UniqueJob', uniqueJobSchema, 'unique_jobs');