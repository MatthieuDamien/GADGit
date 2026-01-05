const mongoose = require('mongoose');

// Schéma flexible pour un job brut.
// L'index TTL est maintenant géré côté Python pour centraliser la configuration.
// On ne le définit plus ici pour éviter les conflits.
const rawJobSchema = new mongoose.Schema({
  JOBID: { type: String, unique: true, required: true },
  last_seen: { type: Date, required: true },
  // Le reste des champs sont flexibles.
}, { strict: false });

module.exports = mongoose.model('RawJob', rawJobSchema, 'raw_jobs');
