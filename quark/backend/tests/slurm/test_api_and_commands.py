#!/usr/bin/env python3
"""
Test simple de l'API à lancer ici
À exécuter si l'API est lancée (port 5000 par défaut)
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:5000"

def test_api():
    """Test complet de l'API"""
    print("=" * 60)
    print(f"TEST API SLURM - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Test Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API accessible")
            print(f"   Status: {data.get('status')}")
            print(f"   Update count: {data.get('update_count')}")
            print(f"   Connection: {data.get('connection_status')}")
            
            cache_sizes = data.get('cache_sizes', {})
            print(f"   Cache: sacct={cache_sizes.get('sacct', 0)}, "
                  f"squeue={cache_sizes.get('squeue', 0)}, "
                  f"sinfo={cache_sizes.get('sinfo', 0)}")
        else:
            print(f"   ❌ Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 2: Récupérer toutes les données
    print("\n2. Test récupération données...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/slurm/all", timeout=30)
        if response.status_code == 200:
            data = response.json()
            slurm_data = data.get('data', {})
            
            print(f"   ✅ Données récupérées")
            print(f"   Last update: {slurm_data.get('last_update')}")
            print(f"   Sacct jobs: {len(slurm_data.get('sacct', []))}")
            print(f"   Squeue jobs: {len(slurm_data.get('squeue', []))}")
            print(f"   Sinfo entries: {len(slurm_data.get('sinfo', []))}")
            
            # Afficher un échantillon
            if slurm_data.get('sacct'):
                print(f"   Premier job sacct: {slurm_data['sacct'][0].get('JOBID', 'N/A')}")
            if slurm_data.get('squeue'):
                print(f"   Premier job squeue: {slurm_data['squeue'][0].get('JOBID', 'N/A')}")
            if slurm_data.get('sinfo'):
                print(f"   Première partition: {slurm_data['sinfo'][0].get('PARTITION', 'N/A')}")
                
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Debug info
    print("\n3. Test debug info...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/debug", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Debug accessible")
            
            imports = data.get('imports_available', {})
            ssh_config = data.get('ssh_config', {})
            
            print(f"   Imports: connect_ssh={imports.get('connect_ssh')}, "
                  f"get_sinfo={imports.get('get_sinfo')}")
            print(f"   SSH: host={ssh_config.get('host')}, "
                  f"user={ssh_config.get('username')}")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 4: Refresh
    print("\n4. Test refresh (peut prendre du temps)...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/slurm/refresh", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Refresh réussi")
            print(f"   Message: {data.get('message')}")
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("TESTS TERMINÉS")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_api()