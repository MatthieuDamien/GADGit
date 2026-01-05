import React from 'react';
import { RefreshCw } from 'lucide-react';
import logoQuark from '../../assets/icons/logoQuark.svg';
import DarkModeToggle from '../ui/DarkModeToggle';

// Composant Header
const Header = ({ lastUpdate, onRefresh, isDarkMode, onToggleDarkMode }) => (
  <header className="sticky top-0 z-50 border-b border-gray-6 dark:border-lime-6 
                     backdrop-blur-sm shadow-sm">
    <div className="px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-9 to-blue-7 
                          dark:from-lime-3 dark:to-lime-5 
                          rounded-lg flex items-center justify-center shadow-lg">
            <img src={logoQuark} className="w-10 h-10" alt="Logo Quark" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-blue-12 dark:text-lime-12">
              Quark
            </h1>
          </div>
          <span className="text-sm text-gray-11 dark:text-lime-11 ml-2 hidden sm:inline">
            Orchestrateur de calcul bioinformatique
          </span>
        </div>
        <div className="flex items-center gap-4">
          <DarkModeToggle isDark={isDarkMode} onToggle={onToggleDarkMode} />
          {/* <button 
            onClick={onRefresh}
            className="p-2 hover:bg-gray-4 dark:hover:bg-lime-4 
                       rounded-lg transition-colors"
            aria-label="Rafraîchir"
          >
            <RefreshCw className="w-5 h-5 text-gray-11 dark:text-lime-11" />
          </button> */}
          <div className="text-sm text-gray-11 dark:text-lime-11">
            MAJ: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  </header>
);

export default Header;