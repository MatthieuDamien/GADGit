import React from 'react';
import { RefreshCw } from 'lucide-react';
import logoQuark from '../../assets/icons/logoQuark.svg';
import DarkModeToggle from '../ui/DarkModeToggle';

// Composant Header
const Header = ({ lastUpdate, onRefresh, isDarkMode, onToggleDarkMode }) => (
  <header className="sticky top-0 z-50 border-b border-marine-border800 dark:border-primary-dark 
                     bg-white/95 dark:bg-black/95 backdrop-blur-sm shadow-sm">
    <div className="px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 bg-gradient-to-br from-primary-light to-marine-border700 
                          dark:from-jaune-interactive300 dark:to-jaune-interactive500/70 
                          rounded-lg flex items-center justify-center shadow-lg">
            <img src={logoQuark} className="w-10 h-10" alt="Logo Quark" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-marine-text1300 dark:text-jaune-text1200">
              Quark
            </h1>
          </div>
          <span className="text-sm text-marine-border600 dark:text-jaune-text1300 ml-2 hidden sm:inline">
            Orchestrateur de calcul bioinformatique
          </span>
        </div>
        <div className="flex items-center gap-4">
          <DarkModeToggle isDark={isDarkMode} onToggle={onToggleDarkMode} />
          <button 
            onClick={onRefresh}
            className="p-2 hover:bg-neutral/10 dark:hover:bg-neutral/20 
                       rounded-lg transition-colors"
            aria-label="Rafraîchir"
          >
            <RefreshCw className="w-5 h-5 text-neutral" />
          </button>
          <div className="text-sm text-neutral">
            MAJ: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  </header>
);

export default Header;