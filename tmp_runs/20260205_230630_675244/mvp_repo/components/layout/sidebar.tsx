import Link from 'next/link';
import { LayoutGrid, Store, Settings } from 'lucide-react';

const navItems = [
  { href: '/app', label: 'Dashboard', icon: LayoutGrid },
  { href: '/app/marketplace', label: 'Marketplace', icon: Store },
  { href: '/app/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden h-screen w-64 flex-col border-r border-slate-200 bg-white p-6 md:flex">
      <div className="flex items-center gap-2 text-lg font-semibold text-slate-900">
        <span className="h-2 w-2 rounded-full bg-sky-600" />
        mvp audit
      </div>
      <nav className="mt-10 space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            <item.icon className="h-4 w-4 text-slate-500" />
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="mt-auto rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
        Keep your launch checklist updated before sharing it.
      </div>
    </aside>
  );
}
