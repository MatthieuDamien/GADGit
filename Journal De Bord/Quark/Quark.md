pour init : 
```bash
cd GAD/GADGIT/quark
yarn start
```
Pourquoi Yarn : [[2025-09-03]]
si c'est lancé : http://localhost:3000/

ne pas oublier d'installer les dépendances suivantes :
```bash
# Tailwind CSS
yarn add -D tailwindcss@^3 postcss autoprefixer

# Lucide React pour les icônes
yarn install lucide-react

## Flask pour Run Python
pip install flask

```

Il est possible qu'il y est de petits bugs, donc, parfois, réinstaller react-scripts
```bash
yarn add react-scripts
```

organisation :
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
│   ├── components/ 
│   │   ├── ui/
│   │   │   ├── Card.jsx
│   │   │   ├── ProgressBar.jsx
│   │   │   └── PriorityBadge.jsx
│   │   ├── dashboard/ 
│   │   │   ├── Header.jsx
│   │   │   ├── ResourceCard.jsx
│   │   │   ├── QueueSection.jsx 
│   │   │   ├── ActiveTasksSection.jsx 
│   │   │   └── ErrorsSection.jsx 
│   │   ├── modals/ 
│   │   │   ├── TaskDetailModal.jsx 
│   │   │   └── ErrorDetailModal.jsx 
│   │   └── items/ 
│   │       ├── QueueItem.jsx 
│   │       ├── ActiveTask.jsx 
│   │       └── ErrorItem.jsx
│   │
│   ├── pages/              # Pages de l'application
│   │   ├── Dashboard/
│   │   │   ├── QuarkDashboard.jsx
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