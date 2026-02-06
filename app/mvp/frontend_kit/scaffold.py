from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent


def _slugify(value: str) -> str:
    sanitized = re.sub(r"[^a-z0-9-]", "-", value.lower())
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized or "startup"


SECTION_ORDER = [
    "Hero",
    "Features",
    "HowItWorks",
    "SocialProof",
    "Pricing",
    "FAQ",
    "CTA",
    "Footer",
]


def _resolve_section_order() -> list[str]:
    template_dir = Path(__file__).parent / "section_templates"
    if not template_dir.exists():
        return SECTION_ORDER
    available = {path.stem for path in template_dir.glob("*.md")}
    ordered = [name for name in SECTION_ORDER if name in available]
    return ordered or SECTION_ORDER


def write_frontend_scaffold(
    repo_dir: Path,
    app_name: str,
    brief: str | None = None,
    audience: str | None = None,
    style: str = "startup_clean",
) -> None:
    if style != "startup_clean":
        raise ValueError(f"Unsupported frontend style: {style}")
    app_name = app_name.strip() or "Launchpad"
    tag_line = (brief or f"{app_name} helps early teams launch with clarity.").strip()
    audience = (audience or "founders and small teams").strip()
    slug = _slugify(app_name)
    section_order = _resolve_section_order()

    def _render(template: str) -> str:
        rendered = (
            template.replace("__APP_NAME__", app_name)
            .replace("__TAG_LINE__", tag_line)
            .replace("__AUDIENCE__", audience)
            .replace("__SLUG__", slug)
        )
        return rendered.replace("{{", "{").replace("}}", "}")

    lib_dir = repo_dir / "lib"
    components_dir = repo_dir / "components"
    ui_dir = components_dir / "ui"
    layout_dir = components_dir / "layout"

    for path in [lib_dir, ui_dir, layout_dir]:
        path.mkdir(parents=True, exist_ok=True)

    (lib_dir / "utils.ts").write_text(
        dedent(
            """\
            import { clsx, type ClassValue } from 'clsx';
            import { twMerge } from 'tailwind-merge';

            export function cn(...inputs: ClassValue[]) {
              return twMerge(clsx(inputs));
            }
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "button.tsx").write_text(
        dedent(
            """\
            import * as React from 'react';
            import { Slot } from '@radix-ui/react-slot';
            import { cva, type VariantProps } from 'class-variance-authority';
            import { cn } from '@/lib/utils';

            const buttonVariants = cva(
              'inline-flex items-center justify-center whitespace-nowrap rounded-full text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:pointer-events-none disabled:opacity-50',
              {
                variants: {
                  variant: {
                    primary: 'bg-sky-600 text-white shadow-soft hover:bg-sky-700 focus-visible:outline-sky-600',
                    secondary: 'bg-white text-slate-900 border border-slate-200 shadow-card hover:border-slate-300',
                    ghost: 'text-slate-700 hover:bg-slate-100',
                  },
                  size: {
                    sm: 'h-9 px-4',
                    md: 'h-11 px-6',
                    lg: 'h-12 px-8',
                  },
                },
                defaultVariants: {
                  variant: 'primary',
                  size: 'md',
                },
              }
            );

            export interface ButtonProps
              extends React.ButtonHTMLAttributes<HTMLButtonElement>,
                VariantProps<typeof buttonVariants> {
              asChild?: boolean;
            }

            const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
              ({ className, variant, size, asChild = false, ...props }, ref) => {
                const Comp = asChild ? Slot : 'button';
                return (
                  <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
                );
              }
            );
            Button.displayName = 'Button';

            export { Button, buttonVariants };
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "card.tsx").write_text(
        dedent(
            """\
            import * as React from 'react';
            import { cn } from '@/lib/utils';

            const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
              ({ className, ...props }, ref) => (
                <div
                  ref={ref}
                  className={cn('rounded-2xl border border-slate-200 bg-white shadow-card', className)}
                  {...props}
                />
              )
            );
            Card.displayName = 'Card';

            const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
              ({ className, ...props }, ref) => (
                <div ref={ref} className={cn('flex flex-col gap-2 p-6', className)} {...props} />
              )
            );
            CardHeader.displayName = 'CardHeader';

            const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
              ({ className, ...props }, ref) => (
                <div ref={ref} className={cn('px-6 pb-6', className)} {...props} />
              )
            );
            CardContent.displayName = 'CardContent';

            export { Card, CardHeader, CardContent };
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "section.tsx").write_text(
        dedent(
            """\
            import * as React from 'react';
            import { cn } from '@/lib/utils';

            export function Section({
              eyebrow,
              title,
              description,
              className,
              dataSection,
              children,
            }: {
              eyebrow?: string;
              title?: string;
              description?: string;
              className?: string;
              dataSection?: string;
              children?: React.ReactNode;
            }) {
              return (
                <section
                  className={cn('mx-auto max-w-6xl px-6 py-16', className)}
                  data-section={dataSection}
                >
                  {title ? (
                    <div className="flex flex-col gap-3">
                      {eyebrow ? (
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                          {eyebrow}
                        </p>
                      ) : null}
                      <h2 className="text-3xl font-semibold text-slate-900">{title}</h2>
                      {description ? <p className="text-base text-slate-600">{description}</p> : null}
                    </div>
                  ) : null}
                  {children ? <div className={title ? 'mt-10' : ''}>{children}</div> : null}
                </section>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "badge.tsx").write_text(
        dedent(
            """\
            import * as React from 'react';
            import { cn } from '@/lib/utils';

            export function Badge({
              className,
              ...props
            }: React.HTMLAttributes<HTMLSpanElement>) {
              return (
                <span
                  className={cn(
                    'inline-flex items-center rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700',
                    className
                  )}
                  {...props}
                />
              );
            }
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "input.tsx").write_text(
        dedent(
            """\
            import * as React from 'react';
            import { cn } from '@/lib/utils';

            export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

            const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => (
              <input
                ref={ref}
                className={cn(
                  'flex h-11 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 shadow-card placeholder:text-slate-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600',
                  className
                )}
                {...props}
              />
            ));
            Input.displayName = 'Input';

            export { Input };
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "label.tsx").write_text(
        dedent(
            """\
            import * as React from 'react';
            import * as LabelPrimitive from '@radix-ui/react-label';
            import { cn } from '@/lib/utils';

            const Label = React.forwardRef<
              React.ElementRef<typeof LabelPrimitive.Root>,
              React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root>
            >(({ className, ...props }, ref) => (
              <LabelPrimitive.Root
                ref={ref}
                className={cn('text-sm font-semibold text-slate-900', className)}
                {...props}
              />
            ));
            Label.displayName = LabelPrimitive.Root.displayName;

            export { Label };
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "skeleton.tsx").write_text(
        dedent(
            """\
            import { cn } from '@/lib/utils';

            export function Skeleton({ className }: { className?: string }) {
              return <div className={cn('animate-pulse rounded-xl bg-slate-100', className)} />;
            }
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "empty-state.tsx").write_text(
        dedent(
            """\
            import { Button } from '@/components/ui/button';

            export function EmptyState({
              title,
              description,
              actionLabel,
            }: {
              title: string;
              description: string;
              actionLabel: string;
            }) {
              return (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
                  <p className="text-lg font-semibold text-slate-900">{title}</p>
                  <p className="mt-2 text-sm text-slate-600">{description}</p>
                  <div className="mt-6">
                    <Button variant="secondary">{actionLabel}</Button>
                  </div>
                </div>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "toast.tsx").write_text(
        dedent(
            """\
            import * as React from 'react';
            import * as ToastPrimitives from '@radix-ui/react-toast';
            import { cva, type VariantProps } from 'class-variance-authority';
            import { cn } from '@/lib/utils';

            const ToastProvider = ToastPrimitives.Provider;
            const ToastViewport = React.forwardRef<
              React.ElementRef<typeof ToastPrimitives.Viewport>,
              React.ComponentPropsWithoutRef<typeof ToastPrimitives.Viewport>
            >(({ className, ...props }, ref) => (
              <ToastPrimitives.Viewport
                ref={ref}
                className={cn(
                  'fixed bottom-6 right-6 z-50 flex max-h-screen w-[360px] flex-col gap-2 outline-none',
                  className
                )}
                {...props}
              />
            ));
            ToastViewport.displayName = ToastPrimitives.Viewport.displayName;

            const toastVariants = cva(
              'group pointer-events-auto relative flex w-full items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-card',
              {
                variants: {
                  variant: {
                    default: 'text-slate-900',
                  },
                },
                defaultVariants: {
                  variant: 'default',
                },
              }
            );

            const Toast = React.forwardRef<
              React.ElementRef<typeof ToastPrimitives.Root>,
              React.ComponentPropsWithoutRef<typeof ToastPrimitives.Root> & VariantProps<typeof toastVariants>
            >(({ className, variant, ...props }, ref) => (
              <ToastPrimitives.Root ref={ref} className={cn(toastVariants({ variant }), className)} {...props} />
            ));
            Toast.displayName = ToastPrimitives.Root.displayName;

            const ToastTitle = React.forwardRef<
              React.ElementRef<typeof ToastPrimitives.Title>,
              React.ComponentPropsWithoutRef<typeof ToastPrimitives.Title>
            >(({ className, ...props }, ref) => (
              <ToastPrimitives.Title ref={ref} className={cn('text-sm font-semibold', className)} {...props} />
            ));
            ToastTitle.displayName = ToastPrimitives.Title.displayName;

            const ToastDescription = React.forwardRef<
              React.ElementRef<typeof ToastPrimitives.Description>,
              React.ComponentPropsWithoutRef<typeof ToastPrimitives.Description>
            >(({ className, ...props }, ref) => (
              <ToastPrimitives.Description ref={ref} className={cn('text-sm text-slate-600', className)} {...props} />
            ));
            ToastDescription.displayName = ToastPrimitives.Description.displayName;

            const ToastClose = React.forwardRef<
              React.ElementRef<typeof ToastPrimitives.Close>,
              React.ComponentPropsWithoutRef<typeof ToastPrimitives.Close>
            >(({ className, ...props }, ref) => (
              <ToastPrimitives.Close
                ref={ref}
                className={cn('text-slate-500 hover:text-slate-700', className)}
                {...props}
              />
            ));
            ToastClose.displayName = ToastPrimitives.Close.displayName;

            export {
              ToastProvider,
              ToastViewport,
              Toast,
              ToastTitle,
              ToastDescription,
              ToastClose,
            };
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "use-toast.ts").write_text(
        dedent(
            """\
            import * as React from 'react';

            type ToastProps = {
              title: string;
              description?: string;
            };

            type ToastState = ToastProps & { id: string };

            const ToastContext = React.createContext<{
              toasts: ToastState[];
              addToast: (toast: ToastProps) => void;
              dismissToast: (id: string) => void;
            } | null>(null);

            export function ToastProvider({ children }: { children: React.ReactNode }) {
              const [toasts, setToasts] = React.useState<ToastState[]>([]);

              const addToast = (toast: ToastProps) => {
                const id = Math.random().toString(36).slice(2);
                setToasts((prev) => [...prev, { ...toast, id }]);
              };

              const dismissToast = (id: string) => {
                setToasts((prev) => prev.filter((item) => item.id !== id));
              };

              return (
                <ToastContext.Provider value={{ toasts, addToast, dismissToast }}>
                  {children}
                </ToastContext.Provider>
              );
            }

            export function useToast() {
              const ctx = React.useContext(ToastContext);
              if (!ctx) {
                throw new Error('useToast must be used within ToastProvider');
              }
              return ctx;
            }
            """
        ),
        encoding="utf-8",
    )

    (ui_dir / "toaster.tsx").write_text(
        dedent(
            """\
            import { useToast } from '@/components/ui/use-toast';
            import {
              ToastProvider as ToastRoot,
              ToastViewport,
              Toast,
              ToastTitle,
              ToastDescription,
              ToastClose,
            } from '@/components/ui/toast';

            function ToastList() {
              const { toasts, dismissToast } = useToast();
              return (
                <>
                  {toasts.map((toast) => (
                    <Toast key={toast.id}>
                      <div className="flex-1">
                        <ToastTitle>{toast.title}</ToastTitle>
                        {toast.description ? <ToastDescription>{toast.description}</ToastDescription> : null}
                      </div>
                      <ToastClose onClick={() => dismissToast(toast.id)}>Close</ToastClose>
                    </Toast>
                  ))}
                  <ToastViewport />
                </>
              );
            }

            export function Toaster() {
              return (
                <ToastRoot>
                  <ToastList />
                </ToastRoot>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    (layout_dir / "sidebar.tsx").write_text(
        _render(
            dedent(
                """\
            import Link from 'next/link';
            import {{ LayoutGrid, Store, Settings }} from 'lucide-react';

            const navItems = [
              {{ href: '/app', label: 'Dashboard', icon: LayoutGrid }},
              {{ href: '/app/marketplace', label: 'Marketplace', icon: Store }},
              {{ href: '/app/settings', label: 'Settings', icon: Settings }},
            ];

            export function Sidebar() {{
              return (
                <aside className="hidden h-screen w-64 flex-col border-r border-slate-200 bg-white p-6 md:flex">
                  <div className="flex items-center gap-2 text-lg font-semibold text-slate-900">
                    <span className="h-2 w-2 rounded-full bg-sky-600" />
                    __APP_NAME__
                  </div>
                  <nav className="mt-10 space-y-2">
                    {{navItems.map((item) => (
                      <Link
                        key={{item.href}}
                        href={{item.href}}
                        className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
                      >
                        <item.icon className="h-4 w-4 text-slate-500" />
                        {{item.label}}
                      </Link>
                    ))}}
                  </nav>
                  <div className="mt-auto rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
                    Keep your launch checklist updated before sharing it.
                  </div>
                </aside>
              );
            }
            """
            )
        ),
        encoding="utf-8",
    )

    (layout_dir / "topbar.tsx").write_text(
        dedent(
            """\
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
            """
        ),
        encoding="utf-8",
    )

    (layout_dir / "app-shell.tsx").write_text(
        dedent(
            """\
            import { Sidebar } from '@/components/layout/sidebar';

            export function AppShell({ children }: { children: React.ReactNode }) {
              return (
                <div className="min-h-screen bg-slate-50 text-slate-900">
                  <div className="flex">
                    <Sidebar />
                    <main className="flex-1">{children}</main>
                  </div>
                </div>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    app_dir = repo_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)

    (app_dir / "layout.tsx").write_text(
        _render(
            dedent(
                """\
            import './globals.css';
            import {{ Plus_Jakarta_Sans }} from 'next/font/google';
            import {{ ToastProvider }} from '@/components/ui/use-toast';
            import {{ Toaster }} from '@/components/ui/toaster';

            const sans = Plus_Jakarta_Sans({{ subsets: ['latin'], variable: '--font-sans' }});

            export const metadata = {{
              title: '__APP_NAME__',
              description: '__TAG_LINE__',
            }};

            export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
              return (
                <html lang="en">
                  <body className={{sans.variable}}>
                    <ToastProvider>
                      {{children}}
                      <Toaster />
                    </ToastProvider>
                  </body>
                </html>
              );
            }}
            """
            )
        ),
        encoding="utf-8",
    )

    (app_dir / "globals.css").write_text(
        dedent(
            """\
            @tailwind base;
            @tailwind components;
            @tailwind utilities;

            :root {
              color-scheme: light;
              --color-bg: #f8fafc;
              --color-surface: #ffffff;
              --color-text: #0f172a;
              --color-muted: #64748b;
              --color-border: #e2e8f0;
              --color-accent: #0ea5e9;
              --radius-sm: 10px;
              --radius-md: 14px;
              --radius-lg: 18px;
              --radius-xl: 24px;
              --space-2: 0.5rem;
              --space-4: 1rem;
              --space-6: 1.5rem;
              --space-8: 2rem;
              --space-12: 3rem;
              --shadow-soft: 0 12px 30px rgba(15, 23, 42, 0.08);
              --shadow-card: 0 8px 24px rgba(15, 23, 42, 0.08);
            }

            body {
              @apply bg-white text-slate-900 antialiased;
              font-family: var(--font-sans), ui-sans-serif, system-ui, sans-serif;
            }

            .shadow-soft {
              box-shadow: var(--shadow-soft);
            }

            .shadow-card {
              box-shadow: var(--shadow-card);
            }
            """
        ),
        encoding="utf-8",
    )

    section_order_literal = ", ".join(f"'{name}'" for name in section_order)
    page_template = _render(
        dedent(
            """\
            import Link from 'next/link';
            import { MotionConfig, motion, useReducedMotion } from 'framer-motion';
            import { Badge } from '@/components/ui/badge';
            import { Button } from '@/components/ui/button';
            import { Card, CardHeader, CardContent } from '@/components/ui/card';
            import { Section } from '@/components/ui/section';
            import { Rocket, Sparkles, ShieldCheck, TrendingUp, Shield, Zap, LineChart } from 'lucide-react';

            const sectionOrder = [<<SECTION_ORDER>>] as const;

            type LandingContent = {
              sections: readonly string[];
              hero: {
                badge: string;
                headline: string;
                subhead: string;
                support: string;
                signal: string;
                primaryCta: string;
                secondaryCta: string;
                previewTitle: string;
                previewSubtitle: string;
                previewItems: { label: string; detail: string }[];
              };
              features: { title: string; description: string; icon: typeof Sparkles }[];
              steps: { title: string; detail: string }[];
              testimonials: { quote: string; name: string; role: string }[];
              pricing: { name: string; price: string; summary: string; highlight?: boolean }[];
              faqs: { q: string; a: string }[];
            };

            const landing = composeLandingSections({
              appName: '__APP_NAME__',
              tagLine: '__TAG_LINE__',
              audience: '__AUDIENCE__',
              sectionOrder,
            });
            const heroMotion = {
              initial: { opacity: 0, y: 18 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 0.6, ease: 'easeOut' },
            };
            const ctaMotion = {
              initial: { opacity: 0, y: 12 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 0.5, ease: 'easeOut', delay: 0.1 },
            };

            function composeLandingSections({
              appName,
              tagLine,
              audience,
              sectionOrder,
            }: {
              appName: string;
              tagLine: string;
              audience: string;
              sectionOrder: readonly string[];
            }): LandingContent {
              const copy = buildHeroCopy({ appName, tagLine, audience });
              const iconMap = {
                proof: Shield,
                speed: Zap,
                insight: LineChart,
              };
              return {
                sections: sectionOrder,
                hero: {
                  badge: copy.badge,
                  headline: copy.headline,
                  subhead: copy.subhead,
                  support: copy.support,
                  signal: copy.signal,
                  primaryCta: copy.primaryCta,
                  secondaryCta: copy.secondaryCta,
                  previewTitle: copy.previewTitle,
                  previewSubtitle: copy.previewSubtitle,
                  previewItems: [
                    { label: 'Signal', detail: 'Clear value and pricing at a glance.' },
                    { label: 'Momentum', detail: 'Guided steps for first outreach.' },
                  ],
                },
                features: [
                  {
                    title: 'Clear value, fast',
                    description: copy.featureOne,
                    icon: iconMap.speed,
                  },
                  {
                    title: 'Confident rollout',
                    description: 'Know what to show before your first call.',
                    icon: Rocket,
                  },
                  {
                    title: 'Proof built in',
                    description: 'Highlight proof, pricing, and outcomes without clutter.',
                    icon: iconMap.proof,
                  },
                ],
                steps: [
                  { title: 'Frame the outcome', detail: 'Capture the result your customers want.' },
                  { title: 'Shape the flow', detail: 'Pick sections that build trust and momentum.' },
                  { title: 'Share the page', detail: 'Send a link you feel proud to share.' },
                ],
                testimonials: [
                  {
                    quote: 'We finally had a page that felt ready for real customers.',
                    name: 'Maya Lewis',
                    role: 'Founder, Signalpath',
                  },
                  {
                    quote: 'The story was clear after one short review.',
                    name: 'Ravi Patel',
                    role: 'Operator, Fieldline',
                  },
                  {
                    quote: 'Pricing and proof looked polished without extra work.',
                    name: 'Sarah Kim',
                    role: 'CEO, Loopframe',
                  },
                ],
                pricing: [
                  { name: 'Starter', price: '$0', summary: 'Launch a clean single page.' },
                  { name: 'Growth', price: '$48', summary: 'Add proof, pricing, and FAQs.', highlight: true },
                  { name: 'Scale', price: '$96', summary: 'Share a full launch-ready story.' },
                ],
                faqs: [
                  { q: 'Is this ready for real customers?', a: 'Yes. The layout is built for first calls.' },
                  { q: 'Can I customize the sections?', a: 'Every section is modular and easy to edit.' },
                  { q: 'Will it work on mobile?', a: 'The layout is responsive from the start.' },
                  { q: 'Does it include pricing?', a: 'You get a three-tier pricing preview.' },
                ],
              };
            }

            function buildHeroCopy({
              appName,
              tagLine,
              audience,
            }: {
              appName: string;
              tagLine: string;
              audience: string;
            }) {
              const outcome = extractOutcome(tagLine) || 'launch with clarity';
              const audienceTrimmed = trimCopy(audience, 48);
              const headline = trimCopy(`Launch a story ${audienceTrimmed} trust.`, 60);
              const subhead = trimCopy(tagLine, 120);
              const support = trimCopy(
                `Built for ${audienceTrimmed} who want ${outcome}.`,
                120
              );
              return {
                badge: 'Launch ready',
                headline,
                subhead,
                support,
                signal: 'Trusted by early teams before their first launch.',
                primaryCta: 'Start free',
                secondaryCta: 'View sample',
                previewTitle: 'Launch preview',
                previewSubtitle: `See how ${appName} shows up in minutes.`,
                featureOne: trimCopy(`Make ${appName} clear in one glance.`, 120),
              };
            }

            function extractOutcome(tagLine: string) {
              const match = tagLine.match(/helps?\\s+([^\\.]+)/i);
              if (!match) return '';
              return match[1].trim();
            }

            function trimCopy(value: string, limit: number) {
              const clean = value.replace(/\\s+/g, ' ').trim();
              if (clean.length <= limit) return clean;
              const sliced = clean.slice(0, limit - 1);
              const safe = sliced.includes(' ') ? sliced.slice(0, sliced.lastIndexOf(' ')) : sliced;
              return `${safe}...`;
            }

            export default function Page() {
              const reduceMotion = useReducedMotion();
              const heroAnim = reduceMotion ? {} : heroMotion;
              const ctaAnim = reduceMotion ? {} : ctaMotion;
              return (
                <MotionConfig reducedMotion="user">
                  <main className="bg-white" data-section-order={landing.sections.join(' > ')}>
                    <section
                      className="border-b border-slate-200 bg-gradient-to-br from-sky-50 via-white to-slate-50"
                      data-section="Hero"
                    >
                      <motion.div
                        {...heroAnim}
                        className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:flex-row lg:items-center"
                      >
                        <div className="flex-1 space-y-6">
                          <Badge>{landing.hero.badge}</Badge>
                          <h1 className="text-4xl font-semibold text-slate-900 md:text-5xl">
                            {landing.hero.headline}
                          </h1>
                          <p className="text-lg text-slate-700">{landing.hero.subhead}</p>
                          <p className="text-base text-slate-600">{landing.hero.support}</p>
                          <div className="flex flex-wrap gap-3">
                            <Button size="lg">{landing.hero.primaryCta}</Button>
                            <Button variant="secondary" size="lg">
                              {landing.hero.secondaryCta}
                            </Button>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-slate-600">
                            <TrendingUp className="h-4 w-4 text-sky-600" />
                            {landing.hero.signal}
                          </div>
                        </div>
                        <Card className="flex-1">
                          <CardHeader>
                            <p className="text-sm font-semibold text-slate-900">{landing.hero.previewTitle}</p>
                            <p className="text-sm text-slate-600">{landing.hero.previewSubtitle}</p>
                          </CardHeader>
                          <CardContent>
                            <div className="grid gap-4 sm:grid-cols-2">
                              {landing.hero.previewItems.map((item) => (
                                <div key={item.label} className="rounded-xl bg-slate-50 p-4">
                                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{item.label}</p>
                                  <p className="mt-2 text-sm text-slate-700">{item.detail}</p>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </section>

                    <Section
                      dataSection="Features"
                      title="Everything you need to look credible"
                      description="Polished sections that build trust before the first call."
                    >
                      <div className="grid gap-6 md:grid-cols-3">
                        {landing.features.map((feature) => (
                          <Card key={feature.title} className="h-full">
                            <CardHeader>
                              <feature.icon className="h-5 w-5 text-sky-600" />
                              <p className="text-lg font-semibold text-slate-900">{feature.title}</p>
                              <p className="text-sm text-slate-600">{feature.description}</p>
                            </CardHeader>
                          </Card>
                        ))}
                      </div>
                    </Section>

                    <Section title="How it works" className="bg-slate-50" dataSection="HowItWorks">
                      <div className="grid gap-6 md:grid-cols-3">
                        {landing.steps.map((step, index) => (
                          <Card key={step.title}>
                            <CardHeader>
                              <span className="text-xs font-semibold text-sky-700">Step {index + 1}</span>
                              <p className="text-lg font-semibold text-slate-900">{step.title}</p>
                              <p className="text-sm text-slate-600">{step.detail}</p>
                            </CardHeader>
                          </Card>
                        ))}
                      </div>
                    </Section>

                    <Section title="Founders trust the layout" dataSection="SocialProof">
                      <div className="grid gap-6 md:grid-cols-3">
                        {landing.testimonials.map((item) => (
                          <Card key={item.name}>
                            <CardHeader>
                              <p className="text-sm text-slate-600">"{item.quote}"</p>
                              <p className="text-sm font-semibold text-slate-900">{item.name}</p>
                              <p className="text-xs text-slate-500">{item.role}</p>
                            </CardHeader>
                          </Card>
                        ))}
                      </div>
                    </Section>

                    <Section
                      dataSection="Pricing"
                      title="Pricing preview"
                      description="Start free and scale when the story is ready."
                      className="bg-slate-50"
                    >
                      <div className="grid gap-6 md:grid-cols-3">
                        {landing.pricing.map((tier) => (
                          <Card
                            key={tier.name}
                            className={tier.highlight ? 'border-sky-200 shadow-soft' : ''}
                          >
                            <CardHeader>
                              <p className="text-sm font-semibold text-slate-900">{tier.name}</p>
                              <p className="text-3xl font-semibold text-slate-900">{tier.price}</p>
                              <p className="text-sm text-slate-600">{tier.summary}</p>
                              <Button className="mt-4" variant={tier.highlight ? 'primary' : 'secondary'}>
                                Choose {tier.name}
                              </Button>
                            </CardHeader>
                          </Card>
                        ))}
                      </div>
                    </Section>

                    <Section title="Frequently asked questions" dataSection="FAQ">
                      <div className="grid gap-6 md:grid-cols-2">
                        {landing.faqs.map((item) => (
                          <Card key={item.q}>
                            <CardHeader>
                              <p className="text-base font-semibold text-slate-900">{item.q}</p>
                              <p className="text-sm text-slate-600">{item.a}</p>
                            </CardHeader>
                          </Card>
                        ))}
                      </div>
                    </Section>

                    <Section className="bg-gradient-to-br from-sky-50 via-white to-slate-50" dataSection="CTA">
                      <motion.div {...ctaAnim} className="text-center">
                        <h2 className="text-3xl font-semibold text-slate-900">Ready to share a credible launch?</h2>
                        <p className="mt-3 text-base text-slate-600">
                          Start with a polished story and adjust once your first customers respond.
                        </p>
                        <div className="mt-8 flex justify-center gap-3">
                          <Button size="lg">Request early access</Button>
                          <Button size="lg" variant="secondary">
                            See example
                          </Button>
                        </div>
                      </motion.div>
                    </Section>

                    <footer className="border-t border-slate-200" data-section="Footer">
                      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 md:flex-row md:items-center md:justify-between">
                        <div>
                          <p className="text-sm font-semibold text-slate-900">__APP_NAME__</p>
                          <p className="text-sm text-slate-600">Launch-ready frontends for early teams.</p>
                        </div>
                        <div className="flex flex-wrap gap-6 text-sm text-slate-600">
                          <Link href="/app">Dashboard</Link>
                          <Link href="/app/marketplace">Marketplace</Link>
                          <Link href="/app/settings">Settings</Link>
                          <a href="#" className="text-slate-600">Privacy</a>
                        </div>
                      </div>
                    </footer>
                  </main>
                </MotionConfig>
              );
            }
            """
        )
    ).replace("<<SECTION_ORDER>>", section_order_literal)
    (app_dir / "page.tsx").write_text(page_template, encoding="utf-8")

    app_app_dir = app_dir / "app"
    (app_app_dir / "marketplace").mkdir(parents=True, exist_ok=True)
    (app_app_dir / "settings").mkdir(parents=True, exist_ok=True)

    (app_app_dir / "layout.tsx").write_text(
        dedent(
            """\
            import { AppShell } from '@/components/layout/app-shell';

            export default function AppLayout({ children }: { children: React.ReactNode }) {
              return <AppShell>{children}</AppShell>;
            }
            """
        ),
        encoding="utf-8",
    )

    (app_app_dir / "page.tsx").write_text(
        _render(
            dedent(
                """\
            import {{ Card, CardHeader, CardContent }} from '@/components/ui/card';
            import {{ Topbar }} from '@/components/layout/topbar';

            const stats = [
              {{ label: 'Active trials', value: '18' }},
              {{ label: 'Conversion rate', value: '12%' }},
              {{ label: 'Launch tasks', value: '7' }},
            ];

            const activity = [
              'Updated pricing copy for __APP_NAME__.',
              'Added a new testimonial to the landing page.',
              'Scheduled the next launch review.',
            ];

            export default function Dashboard() {{
              return (
                <div>
                  <Topbar title="Dashboard" />
                  <div className="mx-auto max-w-6xl space-y-8 px-6 py-10">
                    <div className="grid gap-6 md:grid-cols-3">
                      {{stats.map((stat) => (
                        <Card key={{stat.label}}>
                          <CardHeader>
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{{stat.label}}</p>
                            <p className="text-2xl font-semibold text-slate-900">{{stat.value}}</p>
                          </CardHeader>
                        </Card>
                      ))}}
                    </div>
                    <Card>
                      <CardHeader>
                        <p className="text-lg font-semibold text-slate-900">Recent activity</p>
                        <p className="text-sm text-slate-600">Keep your launch plan aligned.</p>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-3 text-sm text-slate-700">
                          {{activity.map((item) => (
                            <li key={{item}} className="rounded-xl bg-slate-50 p-3">{item}</li>
                          ))}}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              );
            }
            """
            )
        ),
        encoding="utf-8",
    )

    (app_app_dir / "marketplace" / "page.tsx").write_text(
        dedent(
            """\
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
            """
        ),
        encoding="utf-8",
    )

    (app_app_dir / "settings" / "page.tsx").write_text(
        _render(
            dedent(
                """\
            'use client';

            import {{ useState }} from 'react';
            import {{ Topbar }} from '@/components/layout/topbar';
            import {{ Button }} from '@/components/ui/button';
            import {{ Input }} from '@/components/ui/input';
            import {{ Label }} from '@/components/ui/label';
            import {{ useToast }} from '@/components/ui/use-toast';

            export default function Settings() {{
              const [name, setName] = useState('__APP_NAME__');
              const [email, setEmail] = useState('hello@__SLUG__.com');
              const [error, setError] = useState('');
              const {{ addToast }} = useToast();

              const handleSave = () => {{
                if (!name.trim()) {{
                  setError('Workspace name is required.');
                  return;
                }}
                if (!email.includes('@')) {{
                  setError('Enter a valid email address.');
                  return;
                }}
                setError('');
                addToast({{
                  title: 'Settings saved',
                  description: 'Your launch profile is up to date.',
                }});
              }};

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
            """
            )
        ),
        encoding="utf-8",
    )

    (app_app_dir / "loading.tsx").write_text(
        dedent(
            """\
            import { Skeleton } from '@/components/ui/skeleton';

            export default function Loading() {
              return (
                <div className="mx-auto max-w-6xl space-y-6 px-6 py-10">
                  <Skeleton className="h-10 w-48" />
                  <div className="grid gap-6 md:grid-cols-3">
                    <Skeleton className="h-28" />
                    <Skeleton className="h-28" />
                    <Skeleton className="h-28" />
                  </div>
                  <Skeleton className="h-40" />
                </div>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    (app_app_dir / "error.tsx").write_text(
        dedent(
            """\
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
            """
        ),
        encoding="utf-8",
    )

    (app_dir / "error.tsx").write_text(
        dedent(
            """\
            'use client';

            import { useEffect } from 'react';
            import { Button } from '@/components/ui/button';

            export default function Error({ error, reset }: { error: Error; reset: () => void }) {
              useEffect(() => {
                console.error(error);
              }, [error]);

              return (
                <div className="mx-auto max-w-3xl space-y-4 px-6 py-20 text-center">
                  <h1 className="text-3xl font-semibold text-slate-900">We hit a snag</h1>
                  <p className="text-sm text-slate-600">Refresh the page or try again.</p>
                  <Button onClick={() => reset()}>Try again</Button>
                </div>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    (app_dir / "global-error.tsx").write_text(
        dedent(
            """\
            'use client';

            import { useEffect } from 'react';
            import { Button } from '@/components/ui/button';

            export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
              useEffect(() => {
                console.error(error);
              }, [error]);

              return (
                <html lang="en">
                  <body>
                    <div className="mx-auto max-w-3xl space-y-4 px-6 py-20 text-center">
                      <h1 className="text-3xl font-semibold text-slate-900">We hit a snag</h1>
                      <p className="text-sm text-slate-600">Try again or reach out if the issue continues.</p>
                      <Button onClick={() => reset()}>Try again</Button>
                    </div>
                  </body>
                </html>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    (app_dir / "loading.tsx").write_text(
        dedent(
            """\
            import { Skeleton } from '@/components/ui/skeleton';

            export default function Loading() {
              return (
                <div className="mx-auto max-w-6xl space-y-6 px-6 py-12">
                  <Skeleton className="h-10 w-48" />
                  <div className="grid gap-6 md:grid-cols-3">
                    <Skeleton className="h-28" />
                    <Skeleton className="h-28" />
                    <Skeleton className="h-28" />
                  </div>
                  <Skeleton className="h-40" />
                </div>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    (app_dir / "not-found.tsx").write_text(
        dedent(
            """\
            import Link from 'next/link';
            import { Button } from '@/components/ui/button';

            export default function NotFound() {
              return (
                <div className="mx-auto max-w-3xl space-y-4 px-6 py-20 text-center">
                  <h1 className="text-3xl font-semibold text-slate-900">Page not found</h1>
                  <p className="text-sm text-slate-600">Return to the main experience to keep moving.</p>
                  <Button asChild>
                    <Link href="/">Back to home</Link>
                  </Button>
                </div>
              );
            }
            """
        ),
        encoding="utf-8",
    )

    lock_path = Path(__file__).parent / "lockfile.json"
    if lock_path.exists():
        (repo_dir / "frontend_kit.lock.json").write_text(
            lock_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
