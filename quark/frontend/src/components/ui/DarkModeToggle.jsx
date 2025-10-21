import React from 'react';
import { Sun, Moon } from 'lucide-react';

const DarkModeToggle = ({ isDark, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      className="relative inline-flex items-center justify-center w-14 h-7 rounded-full
                 bg-gray-3 hover:bg-blue-3 dark:bg-gray-5 dark:hover:bg-lime-4 transition-all duration-200"
      aria-label="Toggle dark mode"
    >
      <span className="sr-only">Toggle dark mode</span>
      
      {/* Icons */}
      <Sun className="absolute left-1.5 w-4 h-4 text-blue-11 dark:text-gray-8 transition-colors" />
      <Moon className="absolute right-1.5 w-4 h-4 text-gray-8 dark:text-lime-11 transition-colors" />
      
      {/* Slider */}
      <span
        className={`absolute w-5 h-5 bg-white dark:bg-gray-1 rounded-full shadow-lg
                    transform transition-transform duration-200 toggle-slider
                    ${isDark ? 'translate-x-3.5' : '-translate-x-3.5'}`}
      />
    </button>
  );
};

export default DarkModeToggle;