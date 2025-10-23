import React from 'react';
import { User, Server, Clock } from 'lucide-react';

const UtilityJobCard = ({ job }) => {
  const { JOBID, JOBNAME, USER, PARTITION, TIME, ELAPSED } = job;

  return (
    <div className="p-4 rounded-lg shadow-md bg-gray-2 dark:bg-gray-3 border border-transparent hover:border-blue-7 dark:hover:border-lime-7 transition-all duration-200">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-md text-gray-12 dark:text-white truncate" title={JOBNAME}>
          {JOBID} - {JOBNAME}
        </h3>
      </div>
      <div className="text-sm text-gray-11 dark:text-gray-10 space-y-1">
        <p className="flex items-center"><User className="w-4 h-4 mr-2" /> <strong>Utilisateur:</strong><span className="ml-1">{USER || 'N/A'}</span></p>
        <p className="flex items-center"><Server className="w-4 h-4 mr-2" /> <strong>Partition:</strong><span className="ml-1">{PARTITION || 'N/A'}</span></p>
        <p className="flex items-center"><Clock className="w-4 h-4 mr-2" /> <strong>Temps:</strong><span className="ml-1">{ELAPSED || TIME || 'N/A'}</span></p>
      </div>
    </div>
  );
};

export default UtilityJobCard;