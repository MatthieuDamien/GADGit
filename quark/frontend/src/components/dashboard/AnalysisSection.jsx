// src/components/dashboard/AnalysisSection.jsx
import React, { useEffect, useMemo, useState } from 'react';
import { ChevronRight } from 'lucide-react';
import AnalysisCard from '../items/AnalysisCard';

const AnalysisSection = ({ title, analyses: propAnalyses, icon: Icon }) => {
  // Persistance de l’état "plié/déplié" via localStorage
  const [isExpanded, setIsExpanded] = useState(() => {
    const saved = localStorage.getItem(`analysis-${title}-expanded`);
    return saved === null ? true : JSON.parse(saved);
  });

  useEffect(() => {
    localStorage.setItem(`analysis-${title}-expanded`, JSON.stringify(isExpanded));
  }, [isExpanded, title]);

  // Génération des cartes d’analyses
  const analysisList = useMemo(() => {
    if (!propAnalyses?.length) return null;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {propAnalyses.map((analysis) => {
          const id = analysis._id?.$oid || analysis._id || analysis.analysis_id;
          return <AnalysisCard key={id} analysis={analysis} />;
        })}
      </div>
    );
  }, [propAnalyses]);

  // Rien à afficher si pas d’analyses
  if (!propAnalyses?.length) return null;

  return (
    <section className="mb-8">
      <div
        className="flex justify-start items-center cursor-pointer mb-4 hover:bg-blue-4 dark:hover:bg-lime-4 rounded-lg p-2 transition-colors w-fit"
        onClick={() => setIsExpanded(!isExpanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setIsExpanded(!isExpanded)}
      >
        <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-12 dark:text-lime-12">
          {Icon && <Icon className="h-6 w-6 text-lime-11" />}
          {title} ({propAnalyses.length})
        </h2>
        <ChevronRight
          className={`h-6 w-6 text-gray-11 dark:text-gray-10 transform transition-transform duration-300 ml-2 ${
            isExpanded ? 'rotate-90' : 'rotate-0'
          }`}
        />
      </div>

      {isExpanded && analysisList}
    </section>
  );
};

export default AnalysisSection;
