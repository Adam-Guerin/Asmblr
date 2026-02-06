import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Topbar } from '@/components/layout/topbar';

const stats = [
  { label: 'Active trials', value: '18' },
  { label: 'Conversion rate', value: '12%' },
  { label: 'Launch tasks', value: '7' },
];

const activity = [
  'Updated pricing copy for mvp audit.',
  'Added a new testimonial to the landing page.',
  'Scheduled the next launch review.',
];

export default function Dashboard() {
  return (
    <div>
      <Topbar title="Dashboard" />
      <div className="mx-auto max-w-6xl space-y-8 px-6 py-10">
        <div className="grid gap-6 md:grid-cols-3">
          {stats.map((stat) => (
            <Card key={stat.label}>
              <CardHeader>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{stat.label}</p>
                <p className="text-2xl font-semibold text-slate-900">{stat.value}</p>
              </CardHeader>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <p className="text-lg font-semibold text-slate-900">Recent activity</p>
            <p className="text-sm text-slate-600">Keep your launch plan aligned.</p>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-sm text-slate-700">
              {activity.map((item) => (
                <li key={item} className="rounded-xl bg-slate-50 p-3">{item}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
