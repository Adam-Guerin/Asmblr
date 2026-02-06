'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { LoadingSpinner, Skeleton } from '@/components/ui/loading';

const stackCards = [
  "Prototype ready for fast validation",
  "Frontend: Next.js + Tailwind CSS + shadcn-inspired UI + TypeScript",
  "Backend: Next.js API routes + Prisma + SQLite"
];

const metrics = [
  { label: 'Flows', value: '3 ready' },
  { label: 'API', value: 'status + data' },
  { label: 'Focus', value: 'Prototype built' },
];

export default function Page() {
  const [isLoading, setIsLoading] = useState(true);
  const [metricsData, setMetricsData] = useState(metrics);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading data
    const loadData = async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 1500));
        setMetricsData(metrics);
      } catch (err) {
        setError('Failed to load metrics');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  if (error) {
    return (
      <main className="max-w-5xl mx-auto p-6 space-y-10">
        <div className="text-center py-20">
          <h2 className="text-2xl font-semibold text-white mb-4">Something went wrong</h2>
          <p className="text-slate-300 mb-6">{error}</p>
          <Button onClick={() => window.location.reload()}>Try again</Button>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-5xl mx-auto p-6 space-y-10">
      <section className="space-y-4">
        <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Audit MVP</p>
        <h1 className="text-4xl font-semibold text-white">
          {isLoading ? <Skeleton className="w-64 h-12" /> : 'Prototype launched'}
        </h1>
        <p className="text-lg text-slate-300">
          {isLoading ? <Skeleton className="w-48 h-6" /> : 'Audit MVP'}
        </p>
        <div className="flex gap-3 flex-wrap">
          {isLoading ? (
            <>
              <Skeleton className="w-32 h-10" />
              <Skeleton className="w-24 h-10" />
            </>
          ) : (
            <>
              <Button>
                {isLoading ? <LoadingSpinner size="sm" className="mr-2" /> : null}
                Launch prototype
              </Button>
              <Button variant="ghost">View docs</Button>
            </>
          )}
        </div>
      </section>
      
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <article
                key={i}
                className="rounded-2xl border border-slate-800 bg-white/5 p-4 space-y-2"
              >
                <Skeleton className="w-16 h-4" />
                <Skeleton className="w-24 h-8" />
              </article>
            ))
          ) : (
            metricsData.map((metric) => (
              <article
                key={metric.label}
                className="rounded-2xl border border-slate-800 bg-white/5 p-4 space-y-2"
              >
                <p className="text-sm uppercase tracking-[0.4em] text-slate-400">{metric.label}</p>
                <p className="text-2xl font-semibold text-white">{metric.value}</p>
              </article>
            ))
          )}
        </div>
      </section>
      
      <section>
        <h2 className="text-2xl font-semibold text-white">
          {isLoading ? <Skeleton className="w-48 h-8" /> : 'Stack highlights'}
        </h2>
        {isLoading ? (
          <div className="mt-4 space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="w-full h-6" />
            ))}
          </div>
        ) : (
          <ul className="mt-4 list-disc list-inside space-y-2 text-slate-200">
            {stackCards.map((card) => (
              <li key={card}>{card}</li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
