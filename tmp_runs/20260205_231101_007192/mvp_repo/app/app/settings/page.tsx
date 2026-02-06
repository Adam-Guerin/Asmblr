'use client';

import { useState } from 'react';
import { Topbar } from '@/components/layout/topbar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

export default function Settings() {
  const [name, setName] = useState('mvp audit');
  const [email, setEmail] = useState('hello@mvp-audit.com');
  const [error, setError] = useState('');
  const { addToast } = useToast();

  const handleSave = () => {
    if (!name.trim()) {
      setError('Workspace name is required.');
      return;
    }
    if (!email.includes('@')) {
      setError('Enter a valid email address.');
      return;
    }
    setError('');
    addToast({
      title: 'Settings saved',
      description: 'Your launch profile is up to date.',
    });
  };

  return (
    <div>
      <Topbar title="Settings" />
      <div className="mx-auto max-w-3xl space-y-8 px-6 py-10">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-slate-900">Workspace details</h2>
            <p className="text-sm text-slate-600">Keep contact details current for launch updates.</p>
          </div>
          <div className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Workspace name</Label>
              <Input id="name" value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Contact email</Label>
              <Input id="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            {error ? <p className="text-sm text-sky-700">{error}</p> : null}
            <Button onClick={handleSave}>Save changes</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
