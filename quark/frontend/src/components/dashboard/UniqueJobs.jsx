// src/components/dashboard/UniqueJobs.jsx
import React, { useMemo } from 'react';
import { useRealtimeDataContext } from '../../contexts/RealtimeDataContext';
import UniqueJobCard from '../items/UniqueJobCard';
import { ServerCrash, Hourglass, Play, CheckCircle, AlertTriangle, Smile } from 'lucide-react';

const UniqueJobs = () => {
    const { uniqueJobs, loading, error } = useRealtimeDataContext();

    const categorizedJobs = useMemo(() => {
        const categories = {
            pending: [],
            running: [],
            completed: [],
            error: [],
        };

        if (!uniqueJobs || uniqueJobs.length === 0) {
            return categories;
        }

        // Tri des jobs par ID (du plus récent au plus ancien)
        const allJobs = [...uniqueJobs].sort((a, b) => {
            const idA = parseInt(a.JOBID);
            const idB = parseInt(b.JOBID);
            return idB - idA;
        });

        allJobs.forEach(job => {
            const state = (job.STATE || 'UNKNOWN').toUpperCase();            
            if (state.includes('RUNNING') || state.includes('COMPLETING') || state === 'R') {
                categories.running.push(job);
            } else if (state.includes('PENDING') || state === 'PD' || state.includes('CONFIGURING')) {
                categories.pending.push(job);
            } else if (state.includes('COMPLETED')) {
                categories.completed.push(job);
            } else if (state.includes('FAILED') || state.includes('CANCELLED') || state.includes('TIMEOUT') || state.includes('NODE_FAIL')) {
                categories.error.push(job);
            }
        });

        return categories;
    }, [uniqueJobs]);

    const totalJobs = Object.values(categorizedJobs).reduce((sum, arr) => sum + arr.length, 0);

    const jobSections = [
        { title: "En Cours", jobs: categorizedJobs.running, icon: Play, color: "text-blue-11 dark:text-lime-12" },
        { title: "En Attente", jobs: categorizedJobs.pending, icon: Hourglass, color: "text-yellow-11 dark:text-yellow-11" },
        { title: "Terminés", jobs: categorizedJobs.completed, icon: CheckCircle, color: "text-blue-12 dark:text-lime-11" },
        { title: "Erreur / Annulé", jobs: categorizedJobs.error, icon: AlertTriangle, color: "text-red-11 dark:text-red-11" },
    ];

    if (error) {
        return (
            <div className="text-center p-4 text-red-9 dark:text-red-10 flex items-center justify-center">
                <ServerCrash className="w-5 h-5 mr-2" /> Erreur de chargement des jobs uniques: {error}
            </div>
        );
    }

    if (loading) {
        return <div className="text-center p-10">Chargement des jobs uniques...</div>;
    }

    if (totalJobs === 0 && !loading) {
        return (
            <section className="mb-8 text-center p-6 rounded-lg">
                <div className="flex flex-col items-center text-gray-11 dark:text-gray-10">
                    <Smile size={40} className="mb-2" />
                    <p className="text-xl">Aucun job à afficher pour le moment.</p>
                </div>
            </section>
        );
    }

    return (
        <section className="mb-8">
            <h2 className="text-2xl font-bold mb-4 flex items-center text-gray-12 dark:text-lime-12">
                Jobs Uniques ({totalJobs})
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
                {jobSections.map(({ title, jobs, icon: Icon, color }) => (
                    <div key={title} className="bg-gray-1 dark:bg-gray-2 p-4 rounded-lg shadow-sm">
                        <h3 className={`text-lg font-semibold mb-3 flex items-center ${color}`}>
                            <Icon className="w-5 h-5 mr-2" />
                            {title} ({jobs.length})
                        </h3>
                        <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-3 pb-3">
                            {jobs.length > 0 ? (
                                jobs.map(job => <UniqueJobCard key={job.JOBID} job={job} />)
                            ) : (
                                <p className="text-sm text-gray-10 dark:text-gray-9 px-2">
                                    Aucun job dans cette catégorie.
                                </p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
};

export default UniqueJobs;