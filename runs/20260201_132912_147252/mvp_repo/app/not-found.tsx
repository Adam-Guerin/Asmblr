export default function NotFound() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center px-6">
      <div className="max-w-lg space-y-4 text-center">
        <p className="text-sm uppercase tracking-[0.4em] text-slate-400">404</p>
        <h1 className="text-3xl font-semibold">This page does not exist.</h1>
        <p className="text-slate-300">Try going back to the dashboard and restart the flow.</p>
      </div>
    </main>
  );
}
