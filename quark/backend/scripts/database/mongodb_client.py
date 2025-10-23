"""
Client de connexion et de configuration pour la base de données MongoDB.
"""
import os
import logging
from pymongo import MongoClient
from pymongo import errors as pymongo_errors

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        # L'URI par défaut pointe maintenant vers un Replica Set nommé 'rs0'
        # C'est le nom standard pour les configurations Docker, mais il peut être surchargé par la variable d'environnement.
        default_mongo_uri = 'mongodb://localhost:27017/?replicaSet=rs0'
        mongo_uri = os.getenv('MONGO_URI', default_mongo_uri)
        
        try:
            # Ajout du paramètre replicaSet directement dans l'appel si non présent dans l'URI pour plus de robustesse
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, replicaSet='rs0')
            self.client.server_info()
            self.db = self.client['quark_db']
            logger.info("Connexion à MongoDB réussie.")

            # Définition explicite des collections
            self.analyses = self.db['analyses']
            self.pipeline_steps = self.db['pipeline_steps']
            self.cluster_snapshots = self.db['cluster_snapshots']
            self.job_queue = self.db['job_queue']
            
            # les résumés d'analyse
            self.analysis_summaries = self.db['analysis_summaries'] 
            self.utility_job_snapshots = self.db['utility_job_snapshots']
            
            self._create_indexes()

        except pymongo_errors.ConnectionFailure as e:
            logger.error("Échec de la connexion à MongoDB: %s", e)
            raise

    def _create_indexes(self):
        """Créer les index nécessaires s'ils n'existent pas déjà."""
        logger.info("Vérification et création des index MongoDB...")
        try:
            # Index pour les analyses (inchangé)
            self.analyses.create_index([('sample_id', 1)], unique=True, name='idx_sample_id')
            self.analyses.create_index([('status', 1)], name='idx_analysis_status')
            
            # Index pour les étapes de pipeline (inchangé)
            self.pipeline_steps.create_index([('analysis_id', 1)], name='idx_step_analysis_id')
            self.pipeline_steps.create_index([('job_id', 1)], name='idx_step_job_id', sparse=True) 
            self.pipeline_steps.create_index([('status', 1)], name='idx_step_status')
            
            # Index pour les snapshots de cluster (inchangé)
            self.cluster_snapshots.create_index([('timestamp', -1)], name='idx_cluster_timestamp')

            # Index unique sur l'ID pour les upserts rapides
            self.analysis_summaries.create_index([('analysis_id', 1)], unique=True, name='idx_summary_analysis_id')
            
            # --- Gestion de l'index TTL pour analysis_summaries ---
            ttl_seconds = int(os.getenv('SUMMARIES_TTL_SECONDS', 21600)) # 6h par défaut
            index_name = 'idx_ttl_last_update'
            logger.info("TTL for analysis_summaries configured to %s seconds (from SUMMARIES_TTL_SECONDS env var or default).", ttl_seconds)

            # Avertissement si la valeur est très basse pour éviter les erreurs de configuration silencieuses
            if ttl_seconds < 3600: # Moins d'une heure
                logger.warning(
                    "ATTENTION: Le TTL pour 'analysis_summaries' est configuré à une valeur très basse (%s secondes). "
                    "Les données disparaîtront rapidement. Vérifiez la variable d'environnement 'SUMMARIES_TTL_SECONDS'.", ttl_seconds
                )
            
            # ÉTAPE 1: Vérifier si l'index TTL existe et si sa valeur est incorrecte. Si c'est le cas, le supprimer.
            existing_indexes = self.analysis_summaries.index_information()
            if index_name in existing_indexes and existing_indexes[index_name].get('expireAfterSeconds') != ttl_seconds:
                logger.warning(
                    "L'index TTL '%s' a une valeur incorrecte (%s). Il va être recréé avec la valeur %s secondes.",
                    index_name,
                    existing_indexes[index_name].get('expireAfterSeconds'),
                    ttl_seconds
                )
                self.analysis_summaries.drop_index(index_name)
                logger.info("Ancien index TTL '%s' supprimé.", index_name)
            
            # ÉTAPE 2: Créer les index. PyMongo est assez intelligent pour ne pas recréer ceux qui existent déjà et sont corrects.
            # Index unique sur l'ID pour les upserts rapides
            self.analysis_summaries.create_index([('analysis_id', 1)], unique=True, name='idx_summary_analysis_id')
            # Index TTL pour la suppression automatique
            self.analysis_summaries.create_index([('last_update', 1)], expireAfterSeconds=ttl_seconds, name='idx_ttl_last_update')
            # Index sur le statut pour le filtrage dans l'UI
            self.analysis_summaries.create_index([('status', 1)], name='idx_summary_status')

            # Index pour les snapshots de jobs utilitaires (inchangé)
            self.utility_job_snapshots.create_index([('timestamp', -1)], name='idx_utility_snapshot_time')
            
            logger.info("Index MongoDB vérifiés avec succès.")
        
        except pymongo_errors.OperationFailure as e:
            if "Index already exists" in str(e) or "IndexOptionsConflict" in str(e):
                logger.info("Les index existent déjà, aucune action requise.")
            else:
                logger.error("Erreur lors de la création d'un index: %s", e)
