const mongoose = require('mongoose');

const clusterSnapshotSchema = new mongoose.Schema({
  timestamp: { type: Date, default: Date.now ,
    // Crée un index TTL. Utilise la variable d'environnement SNAPSHOT_TTL_SECONDS,
    // avec une valeur par défaut de 24h (86400s) si non définie.
    expires: parseInt(process.env.SNAPSHOT_TTL_SECONDS || '86400', 10)
  },
  metrics: {
    total_nodes:         Number,
    jobs_running:        Number,
    jobs_pending:        Number,
    nodes_cpu_total:     Number,
    nodes_cpu_idle:      Number,
    nodes_cpu_allocated: Number,
    nodes_cpu_down:      Number,
    cpus_total:          Number,
    cpus_allocated:      Number,
    cpus_idle:           Number,
    nodes_gpu_total:     Number,
    nodes_gpu_idle:      Number,
    nodes_gpu_allocated: Number,
    nodes_gpu_down:      Number,
    gpus_total:          Number,
    gpus_allocated:      Number,
    gpus_idle:           Number,
  },
});

// Le 3ème argument spécifie explicitement le nom de la collection pour éviter toute ambiguïté.
module.exports = mongoose.model('ClusterSnapshot', clusterSnapshotSchema, 'cluster_snapshots');
