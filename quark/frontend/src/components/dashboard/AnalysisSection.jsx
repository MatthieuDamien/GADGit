// src/sections/AnalysisSection.jsx (Aucun changement nécessaire)
import React from 'react';
import AnalysisCard from '../items/AnalysisCard';

const AnalysisSection = ({ title, analyses, icon: Icon }) => {
  if (!analyses || analyses.length === 0) {
    return null; // Ne rien afficher si la section est vide
  }

  return (
    <section className="mb-8">
      <h2 className="text-2xl font-bold mb-4 flex items-center text-gray-12 dark:text-lime-12">
        {title} ({analyses.length})
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {analyses.map(analysis => <AnalysisCard key={analysis.analysis_id} analysis={analysis} />)}
      </div>
    </section>
  );
};

export default AnalysisSection;