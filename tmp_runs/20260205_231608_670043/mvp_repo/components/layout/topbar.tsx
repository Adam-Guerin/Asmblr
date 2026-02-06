export function Topbar({ title }: { title: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-4">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Workspace</p>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
      </div>
      <div className="rounded-full bg-slate-100 px-4 py-2 text-sm text-slate-700">
        Active: {title}
      </div>
    </div>
  );
}
