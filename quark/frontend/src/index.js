// src/index.jsx ou src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { RealtimeDataProvider } from './contexts/RealtimeDataContext';
import './styles/index.css'; // Vos styles globaux

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RealtimeDataProvider>
      <App />
    </RealtimeDataProvider>
  </React.StrictMode>
);