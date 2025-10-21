require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const http = require('http');
const { Server } = require("socket.io");

const ClusterSnapshot = require('./models/ClusterSnapshot');
const AnalysisSummary = require('./models/AnalysisSummaries');
const UtilityJobSnapshot = require('./models/UtilityJobSnapshot');

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, { 
  cors: {
    origin: process.env.CLIENT_URL || "http://localhost:3000", // Utilisation d'une variable d'environnement pour la production
    methods: ["GET", "POST", "PUT", "DELETE"]
  }
});

// Connexion à MongoDB
mongoose.connect(process.env.MONGODB_URI)
  .then(() => {
    console.log('Connecté à MongoDB !');
    // Démarrer l'écoute des changements une fois connecté
    watchCollections();
  })
  .catch(err => console.error('Erreur de connexion à MongoDB :', err));

// Gestionnaires d'événements pour la connexion MongoDB
mongoose.connection.on('error', err => console.error('Erreur de connexion MongoDB :', err));
mongoose.connection.on('disconnected', () => console.log('Déconnecté de MongoDB.'));
mongoose.connection.on('reconnected', () => console.log('Reconnecté à MongoDB.'));


io.on('connection', (socket) => {
  console.log('Un client est connecté via WebSocket:', socket.id);
  socket.on('disconnect', () => {
    console.log('Client déconnecté:', socket.id);
  });
});

// Route pour récupérer uniquement les métriques du dernier snapshot
app.get('/api/cluster_snapshots/metrics', async (req, res) => {
  try {
    const latestSnapshot = await ClusterSnapshot.findOne().sort({ timestamp: -1 });
    if (!latestSnapshot) {
      // Retourner un objet vide avec un statut 200 pour que le frontend ne le traite pas comme une erreur.
      return res.status(200).json(null);
    }
    // S'assurer que latestSnapshot.metrics existe avant de le renvoyer
    res.status(200).json(latestSnapshot.metrics || null);
  } catch (error) {
    console.error('Erreur lors de la recherche du snapshot :', error);
    res.status(500).json({ error: error.message });
  }
});

// Route pour récupérer tous les résumés d'analyses
app.get('/api/analysis_summaries', async (req, res) => {
  try {
    const summaries = await AnalysisSummary.find().sort({ 'infos.created_at': -1 });
    
    // Si la base de données est vide, summaries sera un tableau vide [].
    // On renvoie ce tableau vide avec un statut 200 OK.
    // Le frontend interprétera cela comme "aucune donnée" et non comme une erreur,
    // ce qui correspond au comportement que vous souhaitez.
    res.status(200).json(summaries || []);
  } catch (error) {
    console.error("Erreur lors de la récupération des résumés d'analyses :", error);
    res.status(500).json({ error: error.message });
  }
});

// Route pour récupérer les métriques du dernier snapshot de jobs utilitaires
app.get('/api/utility_job_snapshot/metrics', async (req, res) => {
  try {
    const latestSnapshot = await UtilityJobSnapshot.findOne().sort({ timestamp: -1 });
    if (!latestSnapshot) {
      return res.status(200).json(null);
    }
    res.status(200).json(latestSnapshot.raw_data || null);
  } catch (error) {
    console.error('Erreur lors de la recherche du snapshot de jobs utilitaires :', error);
    res.status(500).json({ error: error.message });
  }
});

// Route de santé pour vérifier l'état de l'API et de la connexion à la base de données.
// Inspiré de la route existante dans le backend Python.
app.get('/api/health', (req, res) => {
  const dbState = mongoose.connection.readyState;
  const dbStatus = {
    0: 'disconnected',
    1: 'connected',
    2: 'connecting',
    3: 'disconnecting',
  }[dbState] || 'unknown';

  res.status(200).json({ status: 'ok', mongodb: dbStatus });
});

// Fonction pour surveiller les collections MongoDB
function watchCollections() {
  console.log("Mise en place des Change Streams sur les collections...");

  const collectionsToWatch = [
    ClusterSnapshot,
    AnalysisSummary,
    UtilityJobSnapshot
  ];

  collectionsToWatch.forEach(model => {
    // fullDocument: 'updateLookup' récupère le document complet lors des mises à jour.
    const changeStream = model.collection.watch([], { fullDocument: 'updateLookup' });
    changeStream.on('change', (change) => {
      console.log(`Changement détecté dans '${model.collection.name}':`, change.operationType);
      
      // Préparer les données à émettre. fullDocument est disponible pour 'insert' et 'update'.
      const dataToEmit = {
        collection: model.collection.name,
        operation: change.operationType,
        document: change.fullDocument || change.documentKey // Utiliser fullDocument ou documentKey pour les opérations 'delete'
      };
      io.emit('data_updated', dataToEmit);
    });

    // Gérer les erreurs pour éviter que le serveur ne crash
    changeStream.on('error', (error) => {
      console.error(`Erreur sur le Change Stream pour '${model.collection.name}':`, error.message);
      if (error.code === 40573) { // Code d'erreur pour "not a replica set"
        console.error("ASTUCE: Assurez-vous que votre MongoDB est lancé en tant que Replica Set et que votre URI de connexion contient '?replicaSet=rs0'.");
      }
    });
    console.log(`-> Surveillance active sur '${model.collection.name}'`);
  });
}


// Démarrer le serveur
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => { // On utilise server.listen au lieu de app.listen
  console.log(`Serveur démarré sur le port ${PORT}`);
});
