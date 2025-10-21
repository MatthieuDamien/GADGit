// src/services/realtimeService.js
import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000';

class RealtimeService {
  socket;

  connect() {
    if (!this.socket) {
      this.socket = io(SOCKET_URL, {
        reconnection: true, // Active la reconnexion automatique
        reconnectionAttempts: 5, // Tente 5 fois
        reconnectionDelay: 1000, // Attend 1s entre chaque tentative
        transports: ['websocket'], // Force le transport websocket pour de meilleures performances
      });

      this.socket.on('connect', () => {
        console.log('Connecté au serveur WebSocket ! ID:', this.socket.id);
      });

      this.socket.on('disconnect', () => {
        console.log('Déconnecté du serveur WebSocket.');
      });
    }
  }

  onDataUpdated(callback) {
    this.socket?.on('data_updated', callback);
  }
}

export default new RealtimeService();