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