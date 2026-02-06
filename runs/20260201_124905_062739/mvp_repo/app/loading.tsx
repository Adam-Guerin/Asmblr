import { Skeleton } from '@/components/ui/skeleton';

export default function Loading() {
  return (
    <main className="max-w-6xl mx-auto px-6 py-12 space-y-6">
      <Skeleton className="h-10 w-1/2" />
      <Skeleton className="h-6 w-2/3" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
    </main>
  );
}
