-- Prototype


-- ============================================
-- TABLE: analyses (niveau analyse complète)
-- ============================================
CREATE TABLE analyses (
    id SERIAL PRIMARY KEY,
    sample_id VARCHAR(50) UNIQUE NOT NULL,       -- Ex : dijnbs10411
    status VARCHAR(20) NOT NULL,                 -- 'running' | 'pending' | 'completed' | 'error'
    
    -- Temps
    total_time INTERVAL,                         -- Temps total (queue + execution)
    running_time INTERVAL,                       -- Somme des execution_time des steps
    queue_time INTERVAL,                         -- total_time - running_time
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),          -- Soumission de l'analyse
    finished_at TIMESTAMP,                       -- Quand l'analyse est terminée
    
    -- Métadonnées
    priority VARCHAR(10),                        -- 'Low' | 'Medium' | 'High'
    user_name VARCHAR(50),                       -- Ex : ya0902du
    
    -- Erreurs et reloads
    total_reloaded INTEGER DEFAULT 0,            -- Additions de tous les pipeline_steps(reloaded)
    error_count INTEGER DEFAULT 0,               -- Nombre d'étapes en erreur
    last_error_message TEXT,                     -- Dernier message d'erreur
    
    -- Synchronisation externe
    labkey_id VARCHAR(100),                      -- ? ID dans LabKey (peut être différent)
    labkey_sync_time TIMESTAMP,                  -- Heure de la dernière synchro Labkey
    labkey_metadata JSONB,                       -- ? Cache des métadonnées LabKey
    
    -- Métriques
    node_hours_used DECIMAL(10,2),               -- Coût en heures-nœud (pour optimisation)
    
    CONSTRAINT chk_status CHECK (status IN ('pending', 'running', 'completed', 'error', 'cancelled'))
);

-- Pour comparer l’efficacité des pipelines (ex : une analyse qui prend 10 heures-nœuds vs une autre qui en prend 5 pour le même résultat)
UPDATE analyses
SET node_hours_used = (
    SELECT SUM(nodes_used * EXTRACT(EPOCH FROM execution_time)/3600)
    FROM pipeline_steps
    WHERE pipeline_steps.analysis_id = analyses.id
)
WHERE id = [ID_DE_L_ANALYSE];


-- ============================================
-- TABLE: pipeline_steps (étapes du pipeline)
-- ============================================
CREATE TABLE pipeline_steps (
    id BIGSERIAL PRIMARY KEY,                    -- Job ID SLURM, ex : 51122
    analysis_id INTEGER NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    
    -- Identification
    step_name VARCHAR(100) NOT NULL,             -- 'fq2vcf', 'bam_to_cram', etc.
    step_category VARCHAR(50),                   -- 'pretraitement', 'qualite', 'snv', etc.
    step_order INTEGER,                          -- Ordre dans la categorie (1, 2, 3...) -> à automatiser par json lecture
    
    -- État
    status VARCHAR(20) NOT NULL,                 -- 'pending' | 'running' | 'completed' | 'error'
    exit_code INTEGER,                           -- Code de sortie SLURM (0 = OK)
    
    -- Ressources
    nodes VARCHAR(50),                          -- 'mpi2[13-14,45-50]'
    num_nodes INTEGER,                           -- Nombre de nœuds
    num_cpus INTEGER,                            -- Nombre de CPUs alloués
    partition VARCHAR(50),                       -- 'gpu', 'cpu', 'bigmem', etc.
    
    -- Temps
    submitted_at TIMESTAMP,                      -- ? Soumission dans la queue
    started_at TIMESTAMP,                        -- Début d'exécution
    finished_at TIMESTAMP,                       -- Fin d'exécution
    execution_time INTERVAL,                     -- Temps d'exécution
    time_limit INTERVAL,                         -- ? Limite de temps demandée
    
    -- Erreurs et relances
    reloaded INTEGER DEFAULT 0,                  -- Nombre de reload effectués
    max_reload INTEGER DEFAULT 3,                -- Nombre de reload max autorisés
    error_message TEXT,                          -- Message d'erreur SLURM
    
    -- Données SLURM brutes
    slurm_raw_data JSONB,                        -- ? Données complètes de SLURM
    
    -- Métriques
    memory_used_mb INTEGER,                      -- ? Mémoire utilisée
    pu_efficiency DECIMAL(5,2),                  -- ? % d'utilisation CPU ou GPU
    
    CONSTRAINT chk_step_status CHECK (status IN ('pending', 'running', 'completed', 'error', 'cancelled', 'timeout', 'dependency'))
);

-- ============================================
-- TABLE: pipeline_dependencies
-- Pour gérer les dépendances entre steps
-- ============================================
CREATE TABLE pipeline_dependencies (
    id SERIAL PRIMARY KEY,
    step_id BIGINT REFERENCES pipeline_steps(id) ON DELETE CASCADE,
    depends_on_step_id BIGINT REFERENCES pipeline_steps(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) DEFAULT 'after_ok',  -- 'after_ok', 'after_any', 'after_not_ok'
    
    CONSTRAINT chk_no_self_dependency CHECK (step_id != depends_on_step_id)
);


-- ============================================
-- INDEX pour les performances
-- ============================================
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_sample_id ON analyses(sample_id);
CREATE INDEX idx_analyses_user ON analyses(user_name);
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);

CREATE INDEX idx_steps_analysis_id ON pipeline_steps(analysis_id);
CREATE INDEX idx_steps_status ON pipeline_steps(status);
CREATE INDEX idx_steps_category ON pipeline_steps(step_category);
CREATE INDEX idx_steps_started_at ON pipeline_steps(started_at DESC);

-- Index JSONB pour requêtes sur slurm_raw_data
CREATE INDEX idx_steps_slurm_jobname ON pipeline_steps USING gin ((slurm_raw_data->'JOBNAME'));


-- ============================================
-- TABLE: error_logs
-- Pour tracer l'historique des erreurs
-- ============================================
CREATE TABLE error_logs (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    step_id BIGINT REFERENCES pipeline_steps(id) ON DELETE SET NULL,
    error_type VARCHAR(50),                      -- 'timeout', 'memory', 'node_failure', etc.
    error_message TEXT,
    stack_trace TEXT,
    occurred_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_errors_analysis ON error_logs(analysis_id);
CREATE INDEX idx_errors_occurred_at ON error_logs(occurred_at DESC);


-- ============================================
-- TABLE: labkey_sync_log
-- Pour tracer les synchronisations avec LabKey
-- ============================================
CREATE TABLE labkey_sync_log (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    sync_type VARCHAR(20),                       -- 'create', 'update', 'status_change'
    sync_status VARCHAR(20),                     -- 'success', 'failed'
    request_payload JSONB,
    response_payload JSONB,
    error_message TEXT,
    synced_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_labkey_sync_analysis ON labkey_sync_log(analysis_id);