'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Global runtime error:', error);
  }, [error]);

  return (
    <html>
      <body className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center px-6">
        <div className="max-w-lg space-y-4 text-center">
          <p className="text-sm uppercase tracking-[0.4em] text-slate-400">System</p>
          <h1 className="text-3xl font-semibold">Global error caught.</h1>
          <p className="text-slate-300">
            A critical exception was trapped. You can retry to recover the UI shell.
          </p>
          <button
            className="inline-flex items-center justify-center rounded-full border border-white/20 px-6 py-2 text-sm font-semibold text-white hover:bg-white/10"
            onClick={() => reset()}
          >
            Retry
          </button>
          <p className="text-xs text-slate-500">Digest: {error?.digest ?? 'n/a'}</p>
        </div>
      </body>
    </html>
  );
}
