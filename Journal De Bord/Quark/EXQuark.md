Excellente idée de réorganiser ! Voici une structure professionnelle et scalable pour votre projet Quark :

## 📁 Structure Recommandée

```
quark/
├── public/
│   ├── favicon.ico
│   ├── index.html
│   ├── manifest.json
│   └── robots.txt
│
├── src/
│   ├── assets/              # Ressources statiques
│   │   ├── images/
│   │   │   ├── logo192.png
│   │   │   └── logo512.png
│   │   └── icons/
│   │       └── logo.svg
│   │
│   ├── components/          # Composants réutilisables
│   │   ├── common/         # Composants génériques
│   │   │   ├── Card/
│   │   │   │   ├── Card.jsx
│   │   │   │   └── index.js
│   │   │   ├── ProgressBar/
│   │   │   │   ├── ProgressBar.jsx
│   │   │   │   └── index.js
│   │   │   ├── Badge/
│   │   │   │   ├── Badge.jsx
│   │   │   │   └── index.js
│   │   │   └── Button/
│   │   │       ├── Button.jsx
│   │   │       └── index.js
│   │   │
│   │   ├── dashboard/      # Composants spécifiques au dashboard
│   │   │   ├── ResourceCard/
│   │   │   │   ├── ResourceCard.jsx
│   │   │   │   └── index.js
│   │   │   ├── QueueItem/
│   │   │   │   ├── QueueItem.jsx
│   │   │   │   └── index.js
│   │   │   ├── ActiveTask/
│   │   │   │   ├── ActiveTask.jsx
│   │   │   │   └── index.js
│   │   │   └── ErrorItem/
│   │   │       ├── ErrorItem.jsx
│   │   │       └── index.js
│   │   │
│   │   └── layout/         # Composants de mise en page
│   │       ├── Header/
│   │       │   ├── Header.jsx
│   │       │   └── index.js
│   │       ├── Footer/
│   │       │   ├── Footer.jsx
│   │       │   └── index.js
│   │       └── Layout/
│   │           ├── Layout.jsx
│   │           └── index.js
│   │
│   ├── pages/              # Pages de l'application
│   │   ├── Dashboard/
│   │   │   ├── QuarkDashboard.jsx
│   │   │   └── index.js
│   │   ├── Queue/          # Future page dédiée
│   │   ├── Tasks/          # Future page dédiée
│   │   └── Settings/       # Future page dédiée
│   │
│   ├── services/           # Services et API
│   │   ├── api/
│   │   │   ├── slurm.js   # Communication SLURM
│   │   │   ├── labkey.js  # Communication LabKey
│   │   │   └── index.js
│   │   └── websocket/
│   │       └── socket.js   # WebSocket pour temps réel
│   │
│   ├── hooks/              # Custom React hooks
│   │   ├── useResources.js
│   │   ├── useWebSocket.js
│   │   └── useInterval.js
│   │
│   ├── utils/              # Utilitaires
│   │   ├── constants.js   # Constantes globales
│   │   ├── helpers.js     # Fonctions helper
│   │   └── formatters.js  # Formatage des données
│   │
│   ├── styles/             # Styles globaux
│   │   └── index.css       # Tailwind imports
│   │
│   ├── App.jsx             # Composant principal
│   ├── App.test.js
│   ├── index.js            # Point d'entrée
│   ├── setupTests.js
│   └── reportWebVitals.js
│
├── .gitignore
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── README.md
└── yarn.lock
```

## 🛠️ Scripts de Migration

Créez ces fichiers pour migrer votre code actuel :

### 1. `src/components/common/Card/Card.jsx`

```jsx
export const Card = ({ children, className = "" }) => (
  <div className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 ${className}`}>
    {children}
  </div>
);

export const CardHeader = ({ title, icon: Icon, iconColor = "text-slate-400", count, children }) => (
  <div className="p-4 border-b border-slate-700">
    <div className="flex items-center justify-between">
      <h2 className="text-lg font-semibold text-white flex items-center gap-2">
        {Icon && <Icon className={`w-5 h-5 ${iconColor}`} />}
        {title}
      </h2>
      {count && <span className="text-sm text-slate-400">{count}</span>}
      {children}
    </div>
  </div>
);

export const CardContent = ({ children, className = "" }) => (
  <div className={`p-4 ${className}`}>
    {children}
  </div>
);
```

### 2. `src/components/common/Card/index.js`

```jsx
export { Card, CardHeader, CardContent } from './Card';
```

### 3. `src/services/api/slurm.js`

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const slurm = {
  // Récupérer l'état du cluster
  async getClusterStatus() {
    const response = await fetch(`${API_BASE_URL}/api/cluster/status`);
    return response.json();
  },

  // Récupérer les ressources
  async getResources() {
    const response = await fetch(`${API_BASE_URL}/api/resources`);
    return response.json();
  },

  // Soumettre une tâche
  async submitJob(jobData) {
    const response = await fetch(`${API_BASE_URL}/api/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jobData)
    });
    return response.json();
  },

  // Récupérer la file d'attente
  async getQueue() {
    const response = await fetch(`${API_BASE_URL}/api/queue`);
    return response.json();
  }
};
```

### 4. `src/hooks/useResources.js`

```javascript
import { useState, useEffect } from 'react';
import { slurm } from '../services/api';

export const useResources = (refreshInterval = 5000) => {
  const [resources, setResources] = useState({
    cpu: 0,
    memory: 0,
    gpu: 0,
    storage: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchResources = async () => {
      try {
        const data = await slurm.getResources();
        setResources(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchResources();
    const interval = setInterval(fetchResources, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { resources, loading, error };
};
```

### 5. `src/utils/constants.js`

```javascript
export const PRIORITY_LEVELS = {
  URGENT: 'Urgente',
  HIGH: 'Haute',
  NORMAL: 'Normale',
  LOW: 'Basse'
};

export const TASK_TYPES = {
  GENOME: 'Genome',
  EXOME: 'Exome',
  NEONATAL: 'Dépistage néonatal'
};

export const SEVERITY_LEVELS = {
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
};

export const REFRESH_INTERVALS = {
  RESOURCES: 5000,
  QUEUE: 10000,
  TASKS: 3000
};
```

### 6. `.env.example`

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WEBSOCKET_URL=ws://localhost:8000/ws
REACT_APP_LABKEY_URL=https://labkey.hospital.com
```

### 7. `package.json` - Scripts utiles

```json
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "lint": "eslint src/",
    "format": "prettier --write \"src/**/*.{js,jsx,json,css,md}\""
  }
}
```

## 🚀 Commandes pour réorganiser :

```bash
# Créer la structure de dossiers
mkdir -p src/{assets/{images,icons},components/{common,dashboard,layout},pages,services/{api,websocket},hooks,utils,styles}

# Déplacer les fichiers existants
mv src/logo.svg src/assets/icons/
mv src/logo*.png src/assets/images/
mv src/App.css src/styles/
mv src/index.css src/styles/

# Créer les index.js pour faciliter les imports
echo "export { default } from './QuarkDashboard';" > src/pages/Dashboard/index.js
```

## 💡 Avantages de cette structure :

1. **Séparation des responsabilités** - Chaque dossier a un rôle clair
2. **Scalabilité** - Facile d'ajouter de nouvelles features
3. **Maintenabilité** - Code organisé et facile à naviguer
4. **Réutilisabilité** - Composants modulaires
5. **Tests** - Structure adaptée aux tests unitaires
6. **CI/CD Ready** - Prêt pour l'intégration continue

Cette organisation suit les meilleures pratiques React et facilitera le travail en équipe !