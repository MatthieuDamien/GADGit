import React from 'react';
import { Sun, Moon } from 'lucide-react';

const DarkModeToggle = ({ isDark, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      className="relative inline-flex items-center justify-center w-14 h-7 rounded-full 
                 bg-neutral/20 hover:bg-neutral/30 transition-all duration-200
                 focus:outline-none focus:ring-2 focus:ring-offset-2 
                 focus:ring-offset-transparent focus:ring-primary-light dark:focus:ring-primary-dark"
      aria-label="Toggle dark mode"
    >
      <span className="sr-only">Toggle dark mode</span>
      
      {/* Icons */}
      <Sun className="absolute left-1 w-4 h-4 text-primary-light dark:text-neutral/50 transition-colors" />
      <Moon className="absolute right-1 w-4 h-4 text-neutral/50 dark:text-primary-dark transition-colors" />
      
      {/* Slider */}
      <span
        className={`absolute w-5 h-5 bg-white dark:bg-surface-dark rounded-full shadow-lg 
                    transform transition-transform duration-200 toggle-slider
                    ${isDark ? 'translate-x-3.5' : '-translate-x-3.5'}`}
      />
    </button>
  );
};

export default DarkModeToggle;