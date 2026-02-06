import { Topbar } from '@/components/layout/topbar';
import { EmptyState } from '@/components/ui/empty-state';

export default function Marketplace() {
  return (
    <div>
      <Topbar title="Marketplace" />
      <div className="mx-auto max-w-6xl px-6 py-10">
        <EmptyState
          title="No offers yet"
          description="Publish your pricing page to unlock marketplace listings."
          actionLabel="Create a listing"
        />
      </div>
    </div>
  );
}
