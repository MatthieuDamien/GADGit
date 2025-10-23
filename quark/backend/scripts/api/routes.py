import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# pylint: disable=E0401, E0402
from ..database.mongodb_client import MongoDBClient
from ..scheduler import QuarkScheduler
from bson import ObjectId


app = Flask(__name__)
CORS(app)

db = MongoDBClient()
scheduler = QuarkScheduler(
    host='login-1.mesobfc.fr',
    username='umw040ir',
    password='PaeDaegh5uiX'
)

logger = logging.getLogger(__name__)

# Helper pour convertir ObjectId en string
def serialize_doc(doc):
    if doc:
        doc['_id'] = str(doc['_id'])
    return doc

def serialize_docs(docs):
    return [serialize_doc(doc) for doc in docs]

# Routes analyses
@app.route('/api/analysis_summaries', methods=['GET'])
def get_analyses():
    """Liste toutes les analyses"""
    status = request.args.get('status')
    
    query = {}
    if status:
        query['status'] = status
    
    analyses = list(db.analyses.find(query).sort('created_at', -1))
    # Il est crucial de toujours retourner une liste, même vide, avec un statut 200.
    # Le frontend interprétera une liste vide correctement, sans déclencher d'erreur.
    # Une erreur 404 serait inappropriée ici, car la ressource (la collection) existe.
    return jsonify(serialize_docs(analyses))

@app.route('/api/analyses/<sample_id>', methods=['GET'])
def get_analysis(sample_id):
    """Détails d'une analyse"""
    analysis = db.analyses.find_one({'sample_id': sample_id})
    
    if not analysis:
        return jsonify({'error': 'Analyse non trouvée'}), 404
    
    # Récupérer les steps
    steps = list(db.pipeline_steps.find({
        'analysis_id': str(analysis['_id'])
    }).sort('step_order', 1))
    
    return jsonify({
        'analysis': serialize_doc(analysis),
        'steps': serialize_docs(steps)
    })

@app.route('/api/cluster/status', methods=['GET'])
def get_cluster_status():
    """État actuel du cluster"""
    snapshot = db.cluster_snapshots.find_one(
        sort=[('timestamp', -1)]
    )
    
    if not snapshot:
        return jsonify({'error': 'Aucune donnée disponible'}), 404
    
    return jsonify(serialize_doc(snapshot))

@app.route('/api/cluster/history', methods=['GET'])
def get_cluster_history():
    """Historique du cluster (dernières 24h par exemple)"""
    from datetime import timedelta
    
    limit = int(request.args.get('limit', 100))
    
    snapshots = list(
        db.cluster_snapshots.find()
        .sort('timestamp', -1)
        .limit(limit)
    )
    
    return jsonify(serialize_docs(snapshots))

@app.route('/api/utility_job_snapshots/jobs', methods=['GET'])
def get_utility_job_metrics():
    """Dernier snapshot des jobs utilitaires."""
    snapshot = db.utility_job_snapshots.find_one(
        sort=[('timestamp', -1)]
    )
    
    if not snapshot:
        # Retourne un objet vide si aucune donnée n'est disponible
        return jsonify({'jobs': {}, 'raw_data': {}, 'timestamp': None}), 200
    
    return jsonify(serialize_doc(snapshot))

@app.route('/api/scheduler/run', methods=['POST'])
def run_scheduler():
    """Lance manuellement un cycle du scheduler"""
    try:
        scheduler.run_cycle()
        return jsonify({'success': True, 'message': 'Cycle exécuté'})
    except Exception as e:
        logger.error(f"Erreur scheduler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs/queue', methods=['GET'])
def get_job_queue():
    """Liste des jobs en attente"""
    queue = list(
        db.job_queue.find({'status': 'queued'})
        .sort([('priority_score', -1), ('created_at', 1)])
    )
    
    return jsonify(serialize_docs(queue))

# Route santé
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'mongodb': 'connected' if db.client.server_info() else 'disconnected'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)