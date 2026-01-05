// src/contexts/RealtimeDataContext.jsx
import React, { createContext, useContext } from 'react';
import { useRealtimeData } from '../components/hooks/useRealtimeData';

const RealtimeDataContext = createContext(null);

export const RealtimeDataProvider = ({ children }) => {
  const data = useRealtimeData();
  
  return (
    <RealtimeDataContext.Provider value={data}>
      {children}
    </RealtimeDataContext.Provider>
  );
};

// Hook personnalisé pour utiliser le contexte facilement
export const useRealtimeDataContext = () => {
  const context = useContext(RealtimeDataContext);
  if (!context) {
    throw new Error('useRealtimeDataContext doit être utilisé dans un RealtimeDataProvider');
  }
  return context;
};