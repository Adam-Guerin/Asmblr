export function Badge({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-200">
      {label}
    </span>
  );
}
