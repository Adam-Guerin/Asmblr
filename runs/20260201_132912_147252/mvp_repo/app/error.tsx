'use client';

import { useEffect } from 'react';

import { Button } from '@/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Runtime error:', error);
  }, [error]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center px-6">
      <div className="max-w-lg space-y-4 text-center">
        <p className="text-sm uppercase tracking-[0.4em] text-slate-400">Recovery</p>
        <h1 className="text-3xl font-semibold">We hit a runtime issue.</h1>
        <p className="text-slate-300">
          The MVP is still running. Reload or retry the last action and we will recover cleanly.
        </p>
        <div className="flex justify-center">
          <Button onClick={() => reset()}>Retry</Button>
        </div>
      </div>
    </main>
  );
}
