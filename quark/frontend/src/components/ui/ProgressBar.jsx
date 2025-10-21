import React from 'react';

const ProgressBar = ({ allocatedValue, otherValue, idleValue = 0, height = "h-2" }) => {
  const allocatedWidth = `${allocatedValue}%`;
  const otherWidth = `${otherValue}%`;
  const idleWidth = `${idleValue}%`;

  return (
    <div className={`relative w-full bg-gray-3 dark:bg-lime-3 rounded-full ${height} overflow-hidden flex`}>
      
      {/* Barre bleue (running → gauche → droite) */}
      {allocatedValue > 0 && (
        <div
          className={`transition-all duration-500 bg-blue-11 dark:bg-lime-9`}
          style={{ width: allocatedWidth }}
        />
      )}

      {/* Barre bleur clair (idle → après le bleu) */}
      {idleValue > 0 && (
        <div
          className={`transition-all duration-500 bg-blue-4 dark:bg-lime-4`}
          style={{ width: idleWidth }}
        />
      )}

      {/* Barre grise (down/drained → droite → gauche) */}
      {otherValue > 0 && (
        <div
          className={`transition-all duration-500 bg-gray-3 dark:bg-gray-4 ml-auto`}
          style={{ width: otherWidth }}
        />
      )}
    </div>
  );
};

export { ProgressBar };
