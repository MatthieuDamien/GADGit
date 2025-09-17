from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
from datetime import datetime

# Vos imports existants
from slurmAccess import connect_ssh

from slurmInfo import *
from slurmQueue import *
from slurmSacct import *

app = Flask(__name__)
CORS(app)  # Permettre les requêtes depuis React

# Configuration SSH
username = "umw040ir"
host = "login-1.mesobfc.fr"
password = "PaeDaegh5uiX"

# Cache des données
cache_data = {
    "squeue": [],
    "sacct": [],
    "sinfo": [],
    "last_update": None
}

def fetch_slurm_data():
    """Récupérer toutes les données SLURM"""
    ssh = connect_ssh(HOST = host, USERNAME = username, PASSWORD = password)
    if not ssh:
        return None
    
    try:
        # Récupérer les données
        squeue_data = get_squeue(ssh)
        sacct_data = get_sacct(ssh)
        sinfo_data = get_sinfo(ssh)
        
        ssh.close()
        
        # Mettre à jour le cache
        cache_data.update({
            "squeue": squeue_data if squeue_data != "Error" else [],
            "sacct": sacct_data if sacct_data != "Error" else [],
            "sinfo": sinfo_data if sinfo_data != "Error" else [],
            "last_update": datetime.now().isoformat()
        })
        
        print(f"Données mises à jour: {len(cache_data['sacct'])} jobs sacct, {len(cache_data['squeue'])} jobs squeue")
        return cache_data
        
    except Exception as e:
        print(f"Erreur lors de la récupération: {e}")
        if ssh:
            ssh.close()
        return None



# ------------------------------------------------------------------------------

# Routes API pour React

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifier que l'API fonctionne"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "last_data_update": cache_data.get("last_update")
    })

@app.route('/api/slurm/all', methods=['GET'])
def get_all_slurm_data():
    """Récupérer toutes les données SLURM"""
    return jsonify({
        "success": True,
        "data": cache_data,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/slurm/sacct', methods=['GET'])
def get_sacct_data():
    """Récupérer uniquement les données sacct"""
    return jsonify({
        "success": True,
        "data": cache_data["sacct"],
        "last_update": cache_data.get("last_update"),
        "count": len(cache_data["sacct"])
    })

@app.route('/api/slurm/squeue', methods=['GET'])
def get_squeue_data():
    """Récupérer uniquement les données squeue"""
    return jsonify({
        "success": True,
        "data": cache_data["squeue"],
        "last_update": cache_data.get("last_update"),
        "count": len(cache_data["squeue"])
    })

@app.route('/api/slurm/sinfo', methods=['GET'])
def get_sinfo_data():
    """Récupérer uniquement les données sinfo"""
    return jsonify({
        "success": True,
        "data": cache_data["sinfo"],
        "last_update": cache_data.get("last_update"),
        "count": len(cache_data["sinfo"])
    })

@app.route('/api/slurm/refresh', methods=['POST'])
def refresh_data():
    """Force le rafraîchissement des données"""
    try:
        data = fetch_slurm_data()
        if data:
            return jsonify({
                "success": True,
                "message": "Données rafraîchies",
                "data": data
            })
        else:
            return jsonify({
                "success": False,
                "message": "Erreur lors du rafraîchissement"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur: {str(e)}"
        }), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_details(job_id):
    """Récupérer les détails d'un job spécifique"""
    # Chercher dans sacct
    for job in cache_data["sacct"]:
        if job["JOBID"] == job_id:
            return jsonify({
                "success": True,
                "data": job,
                "source": "sacct"
            })
    
    # Chercher dans squeue
    for job in cache_data["squeue"]:
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


# ------------------------------------------------------------------------------


def update_data_periodically():
    """Mettre à jour les données périodiquement"""
    while True:
        print("Mise à jour automatique des données...")
        fetch_slurm_data()
        time.sleep(5)  # Mise à jour toutes les 5 secondes

# Démarrer le thread de mise à jour automatique
def start_background_updates():
    update_thread = threading.Thread(target=update_data_periodically, daemon=True)
    update_thread.start()

if __name__ == '__main__':
    print("Démarrage de l'API SLURM...")
    
    # Récupérer les données initiales
    print("Récupération des données initiales...")
    fetch_slurm_data()
    
    # Démarrer les mises à jour automatiques
    print("Démarrage des mises à jour automatiques...")
    start_background_updates()
    
    # Démarrer l'API
    print("API disponible sur http://localhost:5000")
    print("Endpoints disponibles:")
    print("   - GET  /api/health")
    print("   - GET  /api/slurm/all")
    print("   - GET  /api/slurm/sacct")
    print("   - GET  /api/slurm/squeue")
    print("   - GET  /api/slurm/sinfo") 
    print("   - POST /api/slurm/refresh")
    print("   - GET  /api/jobs/<job_id>")
    
    app.run(host='0.0.0.0', port=5000, debug=True)