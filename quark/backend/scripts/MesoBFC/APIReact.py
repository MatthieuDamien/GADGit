from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import logging
from datetime import datetime
import traceback

# Configuration du logging (sans emojis pour Windows)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_slurm.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Vos imports (à adapter selon votre structure)
try:
    from slurmAccess import connect_ssh
    from slurmInfo   import get_sinfo
    from slurmQueue  import get_squeue
    from slurmSacct  import get_sacct
    logger.info("IMPORTS: Imports SLURM reussis")

except ImportError as e:
    logger.error(f"IMPORT ERROR: {e}")

app = Flask(__name__)
CORS(app)

# Configuration SSH
USERNAME = "umw040ir"
HOST = "login-1.mesobfc.fr"
PASSWORD = "PaeDaegh5uiX"

# Cache des données avec plus d'informations
cache_data = {
    "squeue": [],
    "sacct": [],
    "sinfo": [],
    "last_update": None,
    "last_error": None,
    "update_count": 0,
    "connection_status": "never_tried"
}

# Lock pour éviter les accès concurrents
cache_lock = threading.Lock()

def fetch_slurm_data():
    """Récupérer toutes les données SLURM avec gestion d'erreurs améliorée"""
    global cache_data
    
    logger.info("FETCH: Debut de recuperation des donnees SLURM")
    
    with cache_lock:
        cache_data["connection_status"] = "connecting"
    
    ssh = None
    try:
        # Connexion SSH
        logger.info(f"SSH: Connexion a {HOST}...")
        ssh = connect_ssh(HOST=HOST, USERNAME=USERNAME, PASSWORD=PASSWORD)
        
        if not ssh:
            logger.error("SSH: Echec de la connexion SSH")
            with cache_lock:
                cache_data["connection_status"] = "failed"
                cache_data["last_error"] = "SSH connection failed"
            return False
        
        logger.info("SSH: Connexion SSH etablie")
        
        with cache_lock:
            cache_data["connection_status"] = "connected"
        
        # Récupération des données
        results = {}
        commands = [
            ("squeue", get_squeue),
            ("sacct", get_sacct),
            ("sinfo", get_sinfo)
        ]
        
        for name, func in commands:
            try:
                logger.info(f"DATA: Recuperation {name}...")
                result = func(ssh)
                
                if result == "Error":
                    logger.error(f"ERROR: Erreur dans {name}")
                    results[name] = []
                elif isinstance(result, list):
                    logger.info(f"SUCCESS: {name}: {len(result)} entrees")
                    results[name] = result
                else:
                    logger.warning(f"WARNING: {name}: type inattendu {type(result)}")
                    results[name] = []
                    
            except Exception as e:
                logger.error(f"EXCEPTION: Exception dans {name}: {e}")
                results[name] = []
        
        # Mise à jour du cache
        with cache_lock:
            cache_data.update({
                "squeue": results.get("squeue", []),
                "sacct": results.get("sacct", []),
                "sinfo": results.get("sinfo", []),
                "last_update": datetime.now().isoformat(),
                "last_error": None,
                "update_count": cache_data.get("update_count", 0) + 1,
                "connection_status": "success"
            })
        
        total_entries = sum(len(results.get(key, [])) for key in ["squeue", "sacct", "sinfo"])
        logger.info(f"UPDATE: Mise a jour terminee: {total_entries} entrees au total")
        
        return True
        
    except Exception as e:
        logger.error(f"GENERAL ERROR: Erreur generale: {e}")
        logger.error(traceback.format_exc())
        
        with cache_lock:
            cache_data.update({
                "last_error": str(e),
                "connection_status": "error"
            })
        
        return False
        
    finally:
        if ssh:
            try:
                ssh.close()
                logger.info("SSH: Connexion SSH fermee")
            except:
                pass

# Routes API

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifier que l'API fonctionne"""
    with cache_lock:
        data = cache_data.copy()
    
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "last_data_update": data.get("last_update"),
        "last_error": data.get("last_error"),
        "update_count": data.get("update_count", 0),
        "connection_status": data.get("connection_status", "unknown"),
        "cache_sizes": {
            "squeue": len(data.get("squeue", [])),
            "sacct": len(data.get("sacct", [])),
            "sinfo": len(data.get("sinfo", []))
        }
    })

@app.route('/api/slurm/all', methods=['GET'])
def get_all_slurm_data():
    """Récupérer toutes les données SLURM"""
    with cache_lock:
        data = cache_data.copy()
    
    return jsonify({
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/slurm/sacct', methods=['GET'])
def get_sacct_data():
    """Récupérer uniquement les données sacct"""
    with cache_lock:
        sacct_data = cache_data["sacct"].copy()
        last_update = cache_data.get("last_update")
    
    return jsonify({
        "success": True,
        "data": sacct_data,
        "last_update": last_update,
        "count": len(sacct_data)
    })

@app.route('/api/slurm/squeue', methods=['GET'])
def get_squeue_data():
    """Récupérer uniquement les données squeue"""
    with cache_lock:
        squeue_data = cache_data["squeue"].copy()
        last_update = cache_data.get("last_update")
    
    return jsonify({
        "success": True,
        "data": squeue_data,
        "last_update": last_update,
        "count": len(squeue_data)
    })

@app.route('/api/slurm/sinfo', methods=['GET'])
def get_sinfo_data():
    """Récupérer uniquement les données sinfo"""
    with cache_lock:
        sinfo_data = cache_data["sinfo"].copy()
        last_update = cache_data.get("last_update")
    
    return jsonify({
        "success": True,
        "data": sinfo_data,
        "last_update": last_update,
        "count": len(sinfo_data)
    })

@app.route('/api/slurm/refresh', methods=['POST'])
def refresh_data():
    """Force le rafraîchissement des données"""
    logger.info("REFRESH: Rafraichissement force demande")
    
    try:
        success = fetch_slurm_data()
        
        with cache_lock:
            data = cache_data.copy()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Données rafraîchies avec succès",
                "data": data
            })
        else:
            return jsonify({
                "success": False,
                "message": "Erreur lors du rafraîchissement",
                "data": data,  # On envoie quand même les anciennes données
                "error": data.get("last_error")
            }), 500
            
    except Exception as e:
        logger.error(f"REFRESH ERROR: Erreur dans refresh_data: {e}")
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_details(job_id):
    """Récupérer les détails d'un job spécifique"""
    with cache_lock:
        sacct_data = cache_data["sacct"]
        squeue_data = cache_data["squeue"]
    
    # Chercher dans sacct
    for job in sacct_data:
        if job.get("JOBID") == job_id:
            return jsonify({
                "success": True,
                "data": job,
                "source": "sacct"
            })
    
    # Chercher dans squeue
    for job in squeue_data:
        if job.get("JOBID") == job_id:
            return jsonify({
                "success": True,
                "data": job,
                "source": "squeue"
            })
    
    return jsonify({
        "success": False,
        "message": "Job non trouvé"
    }), 404

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Endpoint de débogage"""
    with cache_lock:
        data = cache_data.copy()
    
    debug_info = {
        "cache_data": data,
        "ssh_config": {
            "host": HOST,
            "username": USERNAME,
            "password_set": bool(PASSWORD)
        },
        "imports_available": {
            "connect_ssh": "connect_ssh" in globals(),
            "get_sinfo": "get_sinfo" in globals(),
            "get_squeue": "get_squeue" in globals(),
            "get_sacct": "get_sacct" in globals()
        }
    }
    
    return jsonify(debug_info)

# Fonction de mise à jour périodique améliorée
def update_data_periodically():
    """Mettre à jour les données périodiquement"""
    logger.info("THREAD: Demarrage des mises a jour automatiques")
    
    while True:
        try:
            logger.info("THREAD: Mise a jour automatique...")
            fetch_slurm_data()
            
            # Attendre 30 secondes (plus raisonnable que 5 secondes)
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("THREAD: Arret des mises a jour automatiques")
            break
        except Exception as e:
            logger.error(f"THREAD ERROR: Erreur dans la mise a jour automatique: {e}")
            time.sleep(60)  # Attendre plus longtemps en cas d'erreur

def start_background_updates():
    """Démarrer le thread de mise à jour automatique"""
    update_thread = threading.Thread(target=update_data_periodically, daemon=True)
    update_thread.start()
    logger.info("THREAD: Thread de mise a jour automatique demarre")

# Gestionnaire d'erreur global
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"GLOBAL ERROR: Erreur non geree: {e}")
    logger.error(traceback.format_exc())
    return jsonify({
        "success": False,
        "error": "Erreur interne du serveur",
        "message": str(e)
    }), 500

if __name__ == '__main__':
    print("STARTUP: Demarrage de l'API SLURM...")
    logger.info("STARTUP: Demarrage de l'API SLURM")
    
    # Vérifier les imports
    missing_imports = []
    required_functions = ["connect_ssh", "get_sinfo", "get_squeue", "get_sacct"]
    for func_name in required_functions:
        if func_name not in globals():
            missing_imports.append(func_name)
    
    if missing_imports:
        logger.error(f"IMPORTS: Fonctions manquantes: {missing_imports}")
        print("ERROR: Certaines fonctions SLURM ne sont pas disponibles")
        print("Vérifiez vos imports et la structure de vos fichiers")
    
    # Récupérer les données initiales
    logger.info("INIT: Recuperation des donnees initiales...")
    print("INIT: Récupération des données initiales...")
    
    initial_success = fetch_slurm_data()
    if initial_success:
        print("SUCCESS: Données initiales récupérées avec succès")
    else:
        print("WARNING: Échec de récupération des données initiales")
        print("L'API démarre quand même, vous pouvez forcer un refresh via POST /api/slurm/refresh")
    
    # Démarrer les mises à jour automatiques
    print("BACKGROUND: Démarrage des mises à jour automatiques...")
    start_background_updates()
    
    # Afficher les informations de l'API
    print("\n" + "="*60)
    print("API: API disponible sur http://localhost:5000")
    print("ENDPOINTS: Endpoints disponibles:")
    print("   - GET  /api/health          # État de l'API")
    print("   - GET  /api/slurm/all       # Toutes les données")
    print("   - GET  /api/slurm/sacct     # Jobs sacct")
    print("   - GET  /api/slurm/squeue    # Jobs squeue")
    print("   - GET  /api/slurm/sinfo     # Info clusters")
    print("   - POST /api/slurm/refresh   # Forcer refresh")
    print("   - GET  /api/jobs/<job_id>   # Détails job")
    print("   - GET  /api/debug           # Debug info")
    print("="*60)
    print("LOGS: Logs disponibles dans: api_slurm.log")
    print("STOP: Ctrl+C pour arrêter\n")
    
    # Démarrer l'API
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("SHUTDOWN: Arret de l'API demande par l'utilisateur")
        print("\nSHUTDOWN: API arrêtée")