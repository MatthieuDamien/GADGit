import React from 'react';
import { RefreshCw } from 'lucide-react';
import logoQuark from '../../assets/icons/logoQuark.svg';

// Composant Header
const Header = ({ lastUpdate, onRefresh }) => (
  <header className="border-b border-jaune-500 bg-marine-500/50 backdrop-blur-sm">
    <div className="px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 bg-gradient-to-br from-gray-400 to-gray-500 rounded-lg flex items-center justify-center shadow-lg">
            <img src={logoQuark} className="w-10 h-10" alt="Logo Quark" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-100 to-gray-300 bg-clip-text text-transparent">
              Quark
            </h1>
          </div>
          <span className="text-sm text-slate-400 ml-2 hidden sm:inline">
            Orchestrateur de calcul bioinformatique
          </span>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={onRefresh}
            className="p-2 hover:bg-marine-600 rounded-lg transition-colors"
            aria-label="Rafraîchir"
          >
            <RefreshCw className="w-5 h-5 text-slate-400" />
          </button>
          <div className="text-sm text-slate-400">
            MAJ: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  </header>
);

export default Header;