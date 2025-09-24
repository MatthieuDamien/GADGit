import React from 'react';

const AntiProgressBar = ({ blueValue, redValue, idleValue = 0, height = "h-2" }) => {
  const blueWidth = `${blueValue}%`;
  const redWidth = `${redValue}%`;
  const idleWidth = `${idleValue}%`;

  return (
    <div className={`relative w-full bg-neutral/20 dark:bg-neutral/10 rounded-full ${height} overflow-hidden`}>
      
      {/* Barre bleue (running → gauche → droite) */}
      <div
        className={`absolute left-0 top-0 ${height} rounded-full transition-all duration-500 bg-primary-light dark:bg-primary-dark`}
        style={{ width: blueWidth }}
      />

      {/* Barre grise (idle → après le bleu) */}
      {idleValue > 0 && (
        <div
          className={`absolute left-[${blueWidth}] top-0 ${height} rounded-full transition-all duration-500 bg-gray-500`}
          style={{ width: idleWidth, left: blueWidth }}
        />
      )}

      {/* Barre rouge (down/drained → droite → gauche) */}
      {redValue > 0 && (
        <div
          className={`absolute right-0 top-0 ${height} rounded-full transition-all duration-500 bg-red-500`}
          style={{ width: redWidth }}
        />
      )}
    </div>
  );
};

export { AntiProgressBar };
