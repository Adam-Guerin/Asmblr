'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-3xl space-y-4 px-6 py-20 text-center">
      <h1 className="text-3xl font-semibold text-slate-900">Something went wrong</h1>
      <p className="text-sm text-slate-600">Try again or reach out if the issue continues.</p>
      <Button onClick={() => reset()}>Try again</Button>
    </div>
  );
}
