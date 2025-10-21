#!/usr/bin/env python3
"""
Test de l'API Flask pour déboguer les problèmes
Fichier à placer dans backend/tests/MesoBFC/
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000"

def test_api_health():
    """Test du endpoint /api/health"""
    print("=" * 50)
    print("TEST API 1: Health Check")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API accessible")
            print(f"Status: {data.get('status')}")
            print(f"Timestamp: {data.get('timestamp')}")
            print(f"Last Update: {data.get('last_data_update')}")
        else:
            print(f"❌ Status code inattendu: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API")
        print("Vérifiez que l'API Flask est démarrée sur le port 5000")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def test_api_all_data():
    """Test du endpoint /api/slurm/all"""
    print("\n" + "=" * 50)
    print("TEST API 2: All SLURM Data")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/slurm/all", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Données récupérées")
            
            slurm_data = data.get('data', {})
            print(f"Success: {data.get('success')}")
            print(f"Last Update: {slurm_data.get('last_update')}")
            print(f"Sacct jobs: {len(slurm_data.get('sacct', []))}")
            print(f"Squeue jobs: {len(slurm_data.get('squeue', []))}")
            print(f"Sinfo entries: {len(slurm_data.get('sinfo', []))}")
            
            # Afficher un échantillon si disponible
            if slurm_data.get('sacct'):
                print("\nPremier job sacct:")
                first_job = slurm_data['sacct'][0]
                for key, value in first_job.items():
                    print(f"  {key}: {value}")
                    
        else:
            print(f"❌ Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_api_refresh():
    """Test du endpoint /api/slurm/refresh"""
    print("\n" + "=" * 50)
    print("TEST API 3: Refresh Data")
    print("=" * 50)
    
    try:
        print("Lancement du refresh (peut prendre du temps)...")
        response = requests.post(f"{API_BASE_URL}/api/slurm/refresh", timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Refresh réussi")
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            
            refresh_data = data.get('data', {})
            if refresh_data:
                print(f"Last Update: {refresh_data.get('last_update')}")
                print(f"Sacct jobs: {len(refresh_data.get('sacct', []))}")
                print(f"Squeue jobs: {len(refresh_data.get('squeue', []))}")
                print(f"Sinfo entries: {len(refresh_data.get('sinfo', []))}")
        else:
            print(f"❌ Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - la requête a pris trop de temps")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_individual_endpoints():
    """Test des endpoints individuels"""
    print("\n" + "=" * 50)
    print("TEST API 4: Endpoints individuels")
    print("=" * 50)
    
    endpoints = ['sacct', 'squeue', 'sinfo']
    
    for endpoint in endpoints:
        print(f"\n--- Test {endpoint} ---")
        try:
            response = requests.get(f"{API_BASE_URL}/api/slurm/{endpoint}", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: {data.get('count', 0)} entrées")
                print(f"Last Update: {data.get('last_update')}")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur {endpoint}: {e}")

def monitor_api():
    """Monitoring continu de l'API"""
    print("\n" + "=" * 50)
    print("TEST API 5: Monitoring (10 secondes)")
    print("=" * 50)
    
    start_time = time.time()
    
    while time.time() - start_time < 10:
        try:
            response = requests.get(f"{API_BASE_URL}/api/slurm/all", timeout=5)
            if response.status_code == 200:
                data = response.json()
                slurm_data = data.get('data', {})
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Sacct: {len(slurm_data.get('sacct', []))}, "
                      f"Squeue: {len(slurm_data.get('squeue', []))}, "
                      f"Update: {slurm_data.get('last_update', 'None')}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] API Error: {response.status_code}")
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Exception: {e}")
        
        time.sleep(2)

def main():
    """Fonction principale"""
    print(f"🧪 Tests API Flask - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Test de base
    if not test_api_health():
        print("\n❌ API non accessible, arrêt des tests")
        return
    
    # Tests des fonctionnalités
    test_api_all_data()
    test_api_refresh()
    test_individual_endpoints()
    monitor_api()
    
    print("\n" + "=" * 70)
    print("🏁 Tests API terminés")

if __name__ == "__main__":
    main()