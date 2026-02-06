from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Callable

from loguru import logger

from app.core.config import Settings
from app.core.llm import LLMClient, check_ollama
from app.core.run_manager import RunManager
from app.mvp_cycles import MVPProgression, MVPProgressionError
from app.mvp.frontend_kit.scaffold import write_frontend_scaffold
from app.mvp.verifier import MVPVerifier


@dataclass
class StackConfig:
    frontend_stack: str
    backend_stack: str
    backend_platform: str
    database: str
    summary: str


@dataclass
class BuildResult:
    run_id: str
    run_dir: Path
    success: bool
    error: str | None
    cycles: list[dict]
    data_source: dict


class MVPBuilderError(Exception):
    """Raised for issues while orchestrating the MVP build."""


class StackSelector:
    DEFAULT_FRONTEND = "Next.js + Tailwind CSS + shadcn/ui + TypeScript"

    def select(self, topic: str | None, brief: str | None) -> StackConfig:
        context = " ".join(filter(None, [topic, brief])).strip().lower()
        has_async = any(
            keyword in context for keyword in ("async", "ml", "ai", "automation", "pipeline")
        )
        if has_async:
            backend_stack = "FastAPI + SQLite (async flow ready)"
            backend_platform = "fastapi"
        else:
            backend_stack = "Next.js API routes + Prisma + SQLite"
            backend_platform = "nextjs"
        summary = (
            f"Frontend: {self.DEFAULT_FRONTEND}. "
            f"Backend: {backend_stack}. "
            f"Primary database: SQLite. Context: {context or 'core MVP flows'}."
        )
        return StackConfig(
            frontend_stack=self.DEFAULT_FRONTEND,
            backend_stack=backend_stack,
            backend_platform=backend_platform,
            database="SQLite",
            summary=summary,
        )


class TemplateGenerator:
    def __init__(
        self,
        repo_dir: Path,
        stack: StackConfig,
        app_name: str,
        topic: str | None = None,
        brief: str | None = None,
        frontend_style: str | None = None,
        frontend_brief: str | None = None,
        frontend_audience: str | None = None,
    ) -> None:
        self.repo_dir = repo_dir
        self.stack = stack
        self.app_name = app_name.strip() or "Launchpad"
        self.topic = topic
        self.brief = brief
        self.frontend_style = frontend_style
        self.frontend_brief = frontend_brief
        self.frontend_audience = frontend_audience
        self.template_root = Path(__file__).resolve().parents[2] / "templates"
        self.llm_client = LLMClient(
            Settings().ollama_base_url, 
            Settings().general_model
        )

    def generate(self) -> None:
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        self._write_gitignore()
        self._write_stack_descriptor()
        self._write_seed_data()
        self._write_package()
        self._write_tsconfig()
        self._write_next_config()
        self._write_next_env()
        self._write_postcss()
        self._write_tailwind()
        self._write_frontend_scaffold()
        self._write_api_route()
        self._write_health_route()
        self._write_prisma()
        self._write_smoke_script()
        if self.stack.backend_platform == "fastapi":
            self._write_fastapi_backend()
        self._write_readme()

    def _write_seed_data(self) -> None:
        data_dir = self.repo_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        seed_payload = {
            "entities": [
                {
                    "id": "seed_1",
                    "type": "sample",
                    "name": f"{self.app_name} Seed Item",
                    "status": "draft",
                    "notes": "Replace with real records after validation.",
                }
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }
        (data_dir / "seed.json").write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")
        (data_dir / "seed.md").write_text(
            "# Seed Data\n\n"
            "- This file is a placeholder for mocked records.\n"
            "- Update `data/seed.json` once real data is available.\n",
            encoding="utf-8",
        )

    def _write_gitignore(self) -> None:
        content = """\\.next
node_modules
.DS_Store
.env
.env.local
.env.development
.env.production
"""
        self._write_from_template(".gitignore", content)
        env_example = (
            "APP_ENV=development\n"
            "PORT=3000\n"
            "DATABASE_URL=file:./dev.db\n"
        )
        self._write_from_template("env.example", env_example)

    def _write_stack_descriptor(self) -> None:
        payload = {
            "app_name": self.app_name,
            "topic": self.topic,
            "brief": self.brief,
            "stack": {
                "frontend": self.stack.frontend_stack,
                "backend": self.stack.backend_stack,
                "database": self.stack.database,
            },
            "rationale": self.stack.summary,
            "generated_at": datetime.utcnow().isoformat(),
        }
        (self.repo_dir / "mvp_stack.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (self.repo_dir / "stack.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_package(self) -> None:
        slug = self._slug_name()
        payload = {
            "name": slug,
            "private": True,
            "version": "0.1.0",
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
                "test": "node scripts/smoke.mjs",
            },
            "dependencies": {
                "@radix-ui/react-label": "^2.0.2",
                "@radix-ui/react-slot": "^1.0.0",
                "@radix-ui/react-toast": "^1.1.5",
                "@tanstack/react-query": "^5.0.0",
                "@hookform/resolvers": "^3.3.0",
                "class-variance-authority": "^0.7.0",
                "clsx": "^2.0.0",
                "framer-motion": "^10.16.0",
                "lucide-react": "^0.294.0",
                "next": "14.2.35",
                "react": "18.2.0",
                "react-dom": "18.2.0",
                "react-hook-form": "^7.47.0",
                "tailwind-merge": "^2.0.0",
                "zustand": "^4.4.0",
                "zod": "^3.22.0",
            },
            "devDependencies": {
                "@types/node": "25.1.0",
                "autoprefixer": "^10.4.0",
                "postcss": "^8.4.0",
                "prisma": "7.3.0",
                "tailwindcss": "^3.4.0",
                "typescript": "^5.3.3",
            },
        }
        self._write_from_template("package.json", json.dumps(payload, indent=2))

    def _write_tsconfig(self) -> None:
        payload = {
            "compilerOptions": {
                "target": "esnext",
                "module": "esnext",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "esModuleInterop": True,
                "allowSyntheticDefaultImports": True,
                "strict": True,
                "noEmit": True,
                "forceConsistentCasingInFileNames": True,
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "baseUrl": ".",
                "paths": {
                    "@/*": ["./*"],
                },
                "plugins": [
                    {"name": "next"},
                ],
            },
            "include": ["next-env.d.ts", ".next/types/**/*.ts", "**/*.ts", "**/*.tsx"],
            "exclude": ["node_modules"],
        }
        self._write_from_template("tsconfig.json", json.dumps(payload, indent=2))

    def _write_next_config(self) -> None:
        content = dedent(
            """\
            const nextConfig = {
              reactStrictMode: true,
            };

            export default nextConfig;
            """
        )
        self._write_from_template("next.config.mjs", content)

    def _write_next_env(self) -> None:
        self._write_from_template(
            "next-env.d.ts",
            '/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n',
        )

    def _write_postcss(self) -> None:
        content = dedent(
            """\
            module.exports = {
              plugins: {
                tailwindcss: {},
                autoprefixer: {},
              },
            };
            """
        )
        self._write_from_template("postcss.config.js", content)

    def _write_tailwind(self) -> None:
        content = dedent(
            """\
            import type { Config } from 'tailwindcss';

            const config: Config = {
              content: [
                './app/**/*.{ts,tsx}',
                './components/**/*.{ts,tsx}',
                './lib/**/*.{ts,tsx}',
              ],
              theme: {
                extend: {
                  fontFamily: {
                    sans: ['var(--font-sans)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
                  },
                  boxShadow: {
                    soft: '0 12px 30px rgba(15, 23, 42, 0.08)',
                    card: '0 8px 24px rgba(15, 23, 42, 0.08)',
                  },
                },
              },
              plugins: [],
            };

            export default config;
            """
        )
        self._write_from_template("tailwind.config.ts", content)

    def _write_frontend_scaffold(self) -> None:
        brief = self.frontend_brief or self.brief or self.topic or f"{self.app_name} helps teams launch."
        write_frontend_scaffold(
            self.repo_dir,
            self.app_name,
            brief=brief,
            audience=self.frontend_audience,
            style=self.frontend_style,
        )

    def _write_globals(self) -> None:
        css_dir = self.repo_dir / "app"
        css_dir.mkdir(parents=True, exist_ok=True)
        content = dedent(
            """\
            @tailwind base;
            @tailwind components;
            @tailwind utilities;
            
            :root {
              color-scheme: dark;
            }
            
            body {
              @apply bg-slate-950 text-slate-100 min-h-screen font-sans;
            }
            """
        )
        self._write_from_template("app/globals.css", content)

    def _write_layout(self) -> None:
        css_dir = self.repo_dir / "app"
        content = dedent(
            f"""\
            'use client';

            import './globals.css';
            import {{ QueryClientProvider }} from '@tanstack/react-query';
            import {{ queryClient }} from '@/lib/api';

            export const metadata = {{
              title: '{self.app_name}',
              description: 'Production-ready MVP built with AI generation',
            }};

            export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
              return (
                <html lang="en">
                  <body>
                    <QueryClientProvider client={{queryClient}}>
                      {{children}}
                    </QueryClientProvider>
                  </body>
                </html>
              );
            }}
            """
        )
        self._write_from_template("app/layout.tsx", content)

    def _write_page(self) -> None:
        page_dir = self.repo_dir / "app"
        stack_cards = [
            "Prototype ready for fast validation",
            f"Frontend: {self.stack.frontend_stack}",
            f"Backend: {self.stack.backend_stack}",
        ]
        cards_literal = ",\n  ".join(json.dumps(card) for card in stack_cards)
        template = dedent(
            """\
            'use client';

            import { Button } from '@/components/ui/button';
            import { useEffect, useState } from 'react';

            const stackCards = [
              <<STACK_CARDS>>
            ];

            const metrics = [
              { label: 'Flows', value: '3 ready' },
              { label: 'API', value: 'status + data' },
              { label: 'Focus', value: 'Prototype built' },
            ];

            export default function Page() {
              const [apiStatus, setApiStatus] = useState<string>('loading');
              const [apiTimestamp, setApiTimestamp] = useState<string>('');

              useEffect(() => {
                const fetchStatus = async () => {
                  try {
                    const res = await fetch('/api/status');
                    if (!res.ok) {
                      setApiStatus('error');
                      return;
                    }
                    const payload = await res.json();
                    setApiStatus(payload?.status || 'unknown');
                    setApiTimestamp(payload?.timestamp || '');
                  } catch {
                    setApiStatus('error');
                  }
                };
                fetchStatus();
              }, []);

              return (
                <main className="max-w-5xl mx-auto p-6 space-y-10">
                  <section className="space-y-4">
                    <p className="text-sm uppercase tracking-[0.3em] text-slate-400"><<APP_NAME>></p>
                    <h1 className="text-4xl font-semibold text-white">Prototype launched</h1>
                    <p className="text-lg text-slate-300">
                      <<BRIEF>>
                    </p>
                    <div className="rounded-2xl border border-slate-800 bg-white/5 p-4 text-slate-200">
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">API status</p>
                      <p className="text-lg font-semibold">{apiStatus}</p>
                      {apiTimestamp ? (
                        <p className="text-sm text-slate-400">Last update: {apiTimestamp}</p>
                      ) : null}
                    </div>
                    <div className="flex gap-3 flex-wrap">
                      <Button>Launch prototype</Button>
                      <Button variant="ghost">View docs</Button>
                    </div>
                  </section>
                  <section>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {metrics.map((metric) => (
                        <article
                          key={metric.label}
                          className="rounded-2xl border border-slate-800 bg-white/5 p-4 space-y-2"
                        >
                          <p className="text-sm uppercase tracking-[0.4em] text-slate-400">{metric.label}</p>
                          <p className="text-2xl font-semibold text-white">{metric.value}</p>
                        </article>
                      ))}
                    </div>
                  </section>
                  <section>
                    <h2 className="text-2xl font-semibold text-white">Stack highlights</h2>
                    <ul className="mt-4 list-disc list-inside space-y-2 text-slate-200">
                      {stackCards.map((card) => (
                        <li key={card}>{card}</li>
                      ))}
                    </ul>
                  </section>
                </main>
              );
            }
            """
        )
        rendered = (
            template.replace("<<STACK_CARDS>>", cards_literal)
            .replace("<<APP_NAME>>", self.app_name)
            .replace(
                "<<BRIEF>>",
                self.brief
                or "A focused experience built independently of the market loop.",
            )
        )
        self._write_from_template("app/page.tsx", rendered)

    def _write_button(self) -> None:
        btn_dir = self.repo_dir / "components" / "ui"
        btn_dir.mkdir(parents=True, exist_ok=True)
        content = dedent(
            """\
            'use client';

            import React from 'react';

            interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
              variant?: 'primary' | 'ghost';
            }

            const baseStyles =
              'inline-flex items-center justify-center rounded-full border border-transparent px-6 py-2 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2';

            const variantStyles = {
              primary: 'bg-gradient-to-r from-violet-500 via-purple-500 to-indigo-500 text-white shadow-lg',
              ghost: 'bg-white/10 text-white hover:bg-white/20',
            };

            export function Button({
              variant = 'primary',
              className = '',
              ...props
            }: ButtonProps) {
              return (
                <button className={`${baseStyles} ${variantStyles[variant]} ${className}`} {...props} />
              );
            }
            """
        )
        self._write_from_template("components/ui/button.tsx", content)

    def _write_api_route(self) -> None:
        api_dir = self.repo_dir / "app" / "api" / "status"
        api_dir.mkdir(parents=True, exist_ok=True)
        content = dedent(
            """\
            import { NextResponse } from 'next/server';

            export function GET(request: Request) {
              try {
                const apiKey = process.env.API_KEY;
                const providedKey = request.headers.get('x-api-key');
                if (apiKey && providedKey !== apiKey) {
                  return NextResponse.json(
                    { status: 'unauthorized', timestamp: new Date().toISOString() },
                    { status: 401 }
                  );
                }
                return NextResponse.json({
                  status: 'prototype built',
                  stack: 'Next.js + Tailwind + SQLite',
                  timestamp: new Date().toISOString(),
                });
              } catch (error) {
                console.error('status route failed', error);
                return NextResponse.json(
                  { status: 'error', stack: 'Next.js + Tailwind + SQLite', timestamp: new Date().toISOString() },
                  { status: 500 }
                );
              }
            }
            """
        )
        self._write_from_template("app/api/status/route.ts", content)

    def _write_health_route(self) -> None:
        api_dir = self.repo_dir / "app" / "api" / "health"
        api_dir.mkdir(parents=True, exist_ok=True)
        content = dedent(
            """\
            import { NextResponse } from 'next/server';

            export function GET() {
              try {
                return NextResponse.json({
                  status: 'ok',
                  timestamp: new Date().toISOString(),
                });
              } catch (error) {
                console.error('health route failed', error);
                return NextResponse.json({ status: 'error', timestamp: new Date().toISOString() }, { status: 500 });
              }
            }
            """
        )
        self._write_from_template("app/api/health/route.ts", content)

    def _write_prisma(self) -> None:
        prisma_dir = self.repo_dir / "prisma"
        prisma_dir.mkdir(parents=True, exist_ok=True)
        schema = dedent(
            """\
            datasource db {
              provider = 'sqlite'
              url      = 'file:./dev.db'
            }

            generator client {
              provider = 'prisma-client-js'
            }

            model Signal {
              id        Int     @id @default(autoincrement())
              name      String
              status    String
              payload   Json?
              createdAt DateTime @default(now())
            }
            """
        )
        self._write_from_template("prisma/schema.prisma", schema)

    def _write_smoke_script(self) -> None:
        scripts_dir = self.repo_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        content = dedent(
            """\
            import { spawn } from 'node:child_process';
            import net from 'node:net';
            import { setTimeout as delay } from 'node:timers/promises';

            const preferredPort = Number(process.env.SMOKE_PORT || 3100);
            const getAvailablePort = (startPort) =>
              new Promise((resolve) => {
                const tester = net.createServer();
                tester.unref();
                tester.on('error', () => {
                  const fallback = net.createServer();
                  fallback.unref();
                  fallback.listen(0, () => {
                    const { port } = fallback.address();
                    fallback.close(() => resolve(port));
                  });
                });
                tester.listen(startPort, () => {
                  const { port } = tester.address();
                  tester.close(() => resolve(port));
                });
              });

            const port = await getAvailablePort(preferredPort);
            const baseUrl = `http://127.0.0.1:${port}`;
            const nextBin =
              process.platform === 'win32' ? 'node_modules\\\\.bin\\\\next.cmd' : 'node_modules/.bin/next';

            const server = spawn(nextBin, ['start', '-p', port], {
              stdio: ['ignore', 'pipe', 'pipe'],
              shell: process.platform === 'win32',
            });

            server.stdout.on('data', (data) => process.stdout.write(data));
            server.stderr.on('data', (data) => process.stderr.write(data));
            server.on('error', (error) => {
              console.error('Smoke: failed to start server.', error);
            });

            const hardTimeout = setTimeout(() => {
              console.error('Smoke: timeout exceeded.');
              process.exitCode = 1;
              shutdown();
            }, 45000);

            const killTree = () => {
              if (!server.killed) {
                server.kill();
                if (process.platform === 'win32' && server.pid) {
                  spawn('taskkill', ['/PID', String(server.pid), '/T', '/F'], {
                    stdio: 'ignore',
                    shell: true,
                  });
                }
              }
            };

            const shutdown = () => {
              clearTimeout(hardTimeout);
              if (!server.killed) {
                killTree();
              }
            };

            process.on('exit', shutdown);
            process.on('SIGINT', shutdown);
            process.on('SIGTERM', shutdown);

            const fetchWithTimeout = async (url, timeoutMs = 4000) => {
              const controller = new AbortController();
              const timeout = setTimeout(() => controller.abort(), timeoutMs);
              try {
                return await fetch(url, { signal: controller.signal });
              } finally {
                clearTimeout(timeout);
              }
            };

            const waitForServer = async () => {
              const deadline = Date.now() + 30000;
              while (Date.now() < deadline) {
                try {
                  const res = await fetchWithTimeout(`${baseUrl}/`);
                  if (res.ok) return true;
                } catch {
                  // retry until deadline
                }
                await delay(500);
              }
              return false;
            };

            const assertOk = async (label, url, predicate) => {
              const res = await fetchWithTimeout(url);
              const body = await res.text();
              if (!res.ok) {
                throw new Error(`${label} failed: ${res.status}`);
              }
              if (!(await predicate(body))) {
                throw new Error(`${label} failed validation`);
              }
              return body;
            };

            const run = async () => {
              const ready = await waitForServer();
              if (!ready) {
                throw new Error('Smoke: server did not respond on /');
              }
              await assertOk('Page', `${baseUrl}/`, async (body) => body.length > 200);
              await assertOk('API', `${baseUrl}/api/status`, async (body) => {
                try {
                  const payload = JSON.parse(body);
                  return Boolean(payload?.status) && Boolean(payload?.timestamp);
                } catch {
                  return false;
                }
              });
              await assertOk('Health', `${baseUrl}/api/health`, async (body) => {
                try {
                  const payload = JSON.parse(body);
                  return payload?.status === 'ok' && Boolean(payload?.timestamp);
                } catch {
                  return false;
                }
              });
              console.log('Smoke: page and API responded successfully.');
            };

            run()
              .catch((error) => {
                console.error(error);
                process.exitCode = 1;
              })
              .finally(() => {
                shutdown();
                setTimeout(() => {
                  process.exit(process.exitCode || 0);
                }, 200);
              });
            """
        )
        self._write_from_template("scripts/smoke.mjs", content)

    def _write_fastapi_backend(self) -> None:
        backend_dir = self.repo_dir / "backend"
        backend_dir.mkdir(parents=True, exist_ok=True)
        (backend_dir / "auth.py").write_text(
            dedent(
                """\
                from fastapi import Header, HTTPException
                import os

                def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
                    expected = os.getenv("API_KEY", "")
                    if expected and x_api_key != expected:
                        raise HTTPException(status_code=401, detail="Unauthorized")
                """
            ),
            encoding="utf-8",
        )
        (backend_dir / "db.py").write_text(
            dedent(
                """\
                import sqlite3
                from pathlib import Path

                DB_PATH = Path(__file__).resolve().parent / "app.db"

                def init_db() -> None:
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        conn.execute(
                            \"\"\"
                            CREATE TABLE IF NOT EXISTS signals (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL,
                                status TEXT NOT NULL,
                                created_at TEXT DEFAULT CURRENT_TIMESTAMP
                            )
                            \"\"\"
                        )
                        conn.commit()
                    finally:
                        conn.close()
                """
            ),
            encoding="utf-8",
        )
        main_py = dedent(
            """\
            from fastapi import FastAPI
            from pydantic import BaseModel
            from .auth import require_api_key
            from .db import init_db

            app = FastAPI(title='Prototype backend')

            class Health(BaseModel):
              status: str
              stack: str

            @app.on_event('startup')
            def _startup():
              init_db()

            @app.get('/')
            def root():
              return {'status': 'prototype built', 'stack': 'FastAPI + SQLite'}

            @app.get('/health')
            def health() -> Health:
              return Health(status='ok', stack='FastAPI + SQLite')

            @app.get('/signals')
            def signals():
              require_api_key()
              return {'items': [], 'status': 'ok'}
            """
        )
        self._write_from_template("backend/main.py", main_py)
        self._write_from_template(
            "backend/requirements.txt",
            dedent(
                """\
                fastapi
                pydantic
                uvicorn
                """
            ),
        )

    def _write_readme(self) -> None:
        body = dedent(
            f"""\
            # {self.app_name} MVP

            ## Stack
            - Frontend: {self.stack.frontend_stack}
            - Backend: {self.stack.backend_stack}
            - Database: {self.stack.database}

            ## Getting started
            ```bash
            cd mvp_repo
            npm install
            npm run build
            npm run dev
            ```

            Smoke checks (API + page availability):
            ```bash
            npm test
            ```

            Use `npm run build` to verify the prototype can orchestrate the Next.js + SQLite stack without LLMs. The FastAPI backend (if present) can be started via `uvicorn backend.main:app --reload`.
            """
        )
        self._write_from_template("README.md", body)
        self._write_from_template("docs/README_RUNBOOK.md", self._runbook_template())
        self._write_from_template("docs/QUALITY_CHECKLIST.md", self._quality_checklist_template())
        self._write_from_template("docs/CHANGELOG.md", self._changelog_template())
        self._write_from_template("docs/OPERATIONS.md", self._operations_template())
        self._write_from_template("docs/ARCHITECTURE.md", self._architecture_template())

    def _slug_name(self) -> str:
        sanitized = re.sub(r"[^a-z0-9-]", "-", self.app_name.lower())
        sanitized = re.sub(r"-+", "-", sanitized).strip("-")
        return sanitized or "asmblr-mvp"

    def _runbook_template(self) -> str:
        return dedent(
            """\
            # Runbook

            ## Start locally
            ```bash
            npm install
            npm run build
            npm run dev
            ```

            ## Smoke checks
            ```bash
            npm test
            ```

            ## Common issues
            - If the UI is blank, check `app/page.tsx` for errors.
            - If API routes fail, inspect `app/api/status` and `app/api/health`.
            """
        )

    def _quality_checklist_template(self) -> str:
        return dedent(
            """\
            # Quality Checklist

            ## Foundation
            - [ ] `npm run build` succeeds
            - [ ] `/` returns HTTP 200
            - [ ] `/api/status` returns HTTP 200
            - [ ] `/api/health` returns HTTP 200
            - [ ] Error boundary renders
            - [ ] Not-found page renders
            - [ ] No crashes in console

            ## UX
            - [ ] Typography scale consistent
            - [ ] Spacing scale consistent
            - [ ] Reusable components used in main page

            ## Polish
            - [ ] Loading state present
            - [ ] Empty state present
            - [ ] Microcopy present
            - [ ] Subtle animations with reduced-motion support
            """
        )

    def _changelog_template(self) -> str:
        return dedent(
            """\
            # Changelog

            ## [Unreleased]
            - Initial scaffold.
            """
        )

    def _operations_template(self) -> str:
        return dedent(
            """\
            # Operations

            ## Run
            - `npm run dev`
            - `npm run build`
            - `npm test`

            ## Environment
            - No secrets should be committed.
            """
        )

    def _architecture_template(self) -> str:
        return dedent(
            f"""\
            # Architecture

            ## Stack
            - Frontend: {self.stack.frontend_stack}
            - Backend: {self.stack.backend_stack}
            - Database: {self.stack.database}

            ## Layout
            - `app/` for UI and API routes
            - `components/ui/` for reusable UI primitives
            - `prisma/` for the schema
            """
        )

    def _write_from_template(self, rel_path: str, content: str) -> None:
        """Write content directly since we're no longer using static templates."""
        target = self.repo_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


class MVPBuilder:
    DEFAULT_CYCLES = ["foundation", "ux", "polish"]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.manager = RunManager(settings.runs_dir, settings.data_dir)
        self.selector = StackSelector()

    def build_from_run(
        self,
        run_id: str,
        cycle_keys: list[str] | None = None,
        max_fix_iter: int = 5,
        force: bool = False,
        frontend_style: str | None = None,
        build_runner: Callable[[str, Path, int], tuple[bool, str]] | None = None,
        test_runner: Callable[[str, Path, int], tuple[bool, str]] | None = None,
    ) -> BuildResult:
        run = self.manager.get_run(run_id)
        if not run:
            run_dir = self.settings.runs_dir / run_id
            if not run_dir.exists():
                raise MVPBuilderError(f"Run {run_id} not found.")
            topic = None
            run_status = None
        else:
            run_dir = Path(run["output_dir"])
            run_dir.mkdir(parents=True, exist_ok=True)
            topic = run.get("topic")
            run_status = run.get("status")
        return self._build(
            run_id=run_id,
            run_dir=run_dir,
            topic=topic,
            brief=None,
            cycle_keys=cycle_keys,
            max_fix_iter=max_fix_iter,
            force=force,
            run_status=run_status,
            frontend_style=frontend_style,
            build_runner=build_runner,
            test_runner=test_runner,
        )

    def build_from_brief(
        self,
        brief: str,
        output_dir: Path,
        cycle_keys: list[str] | None = None,
        max_fix_iter: int = 5,
        force: bool = False,
        frontend_style: str = "startup_clean",
        build_runner: Callable[[str, Path, int], tuple[bool, str]] | None = None,
        test_runner: Callable[[str, Path, int], tuple[bool, str]] | None = None,
    ) -> BuildResult:
        run_dir = output_dir
        run_dir.mkdir(parents=True, exist_ok=True)
        run_id = run_dir.name
        return self._build(
            run_id=run_id,
            run_dir=run_dir,
            topic=brief,
            brief=brief,
            cycle_keys=cycle_keys,
            max_fix_iter=max_fix_iter,
            force=force,
            run_status=None,
            frontend_style=frontend_style,
            build_runner=build_runner,
            test_runner=test_runner,
        )

    def _build(
        self,
        run_id: str,
        run_dir: Path,
        topic: str | None,
        brief: str | None,
        cycle_keys: list[str] | None,
        max_fix_iter: int,
        force: bool,
        run_status: str | None,
        frontend_style: str | None,
        build_runner: Callable[[str, Path, int], tuple[bool, str]] | None,
        test_runner: Callable[[str, Path, int], tuple[bool, str]] | None,
    ) -> BuildResult:
        logger.info("Building MVP for run %s in %s", run_id, run_dir)
        self._ensure_within_runs(run_dir)
        frontend_style = (frontend_style or getattr(self.settings, "frontend_style", "startup_clean")).strip()
        if frontend_style != "startup_clean":
            raise MVPBuilderError(f"Unsupported frontend style: {frontend_style}")
        if (run_dir / ".env").exists():
            raise MVPBuilderError("Detected .env in run directory; builder refuses to operate.")
        self._prepare_target(run_dir, force)
        self._ensure_cycle_root(run_dir)
        stack = self.selector.select(topic, brief)
        repo_dir = run_dir / "mvp_repo"
        app_name, frontend_brief, frontend_audience = self._resolve_frontend_inputs(
            run_dir, run_id, topic, brief
        )
        TemplateGenerator(
            repo_dir,
            stack,
            app_name,
            topic,
            brief,
            frontend_style=frontend_style,
            frontend_brief=frontend_brief,
            frontend_audience=frontend_audience,
        ).generate()
        allowed_cycles = self._normalize_cycles(cycle_keys)
        data_source_tag = self._resolve_data_source_tag(run_status, brief)
        self._write_scope(
            run_dir,
            run_id,
            topic,
            brief,
            stack,
            allowed_cycles,
            data_source_tag,
            frontend_style,
        )
        data_source = self._compose_data_source(run_id, run_status, brief, topic, data_source_tag)
        success = False
        error: str | None = None
        progression: MVPProgression | None = None
        cycles: list[dict] = []
        llm_client = LLMClient(self.settings.ollama_base_url, self.settings.code_model)
        llm_enabled = not self.settings.mvp_disable_llm
        try:
            try:
                tags = check_ollama(
                    self.settings.ollama_base_url,
                    [self.settings.general_model, self.settings.code_model],
                )
                if not tags:
                    llm_enabled = False
                models = {m.get("name") for m in tags.get("models", []) if isinstance(m, dict)}
                required = {self.settings.general_model, self.settings.code_model}
                if not required.issubset(models):
                    llm_enabled = False
            except Exception as exc:
                logger.warning("Ollama check failed for MVP build: {}", exc)
                llm_enabled = False
            use_command_runner = bool(
                self.settings.mvp_build_command or self.settings.mvp_test_command
            )
            if not use_command_runner and (build_runner is None or test_runner is None):
                verifier = MVPVerifier(
                    repo_dir,
                    install_timeout=self.settings.mvp_install_timeout,
                    build_timeout=self.settings.mvp_build_timeout,
                    test_timeout=self.settings.mvp_test_timeout,
                )
                if build_runner is None:
                    build_runner = self._runner_from_verifier(verifier, "build")
                if test_runner is None:
                    test_runner = self._runner_from_verifier(verifier, "test")
            progression = MVPProgression(
                run_id=run_id,
                run_dir=run_dir,
                settings=self.settings,
                llm_client=llm_client,
                llm_enabled=llm_enabled,
                build_runner=build_runner,
                test_runner=test_runner,
                max_auto_fixes=max_fix_iter,
                cycle_keys=allowed_cycles,
            )
            progression.run()
            success = True
        except MVPProgressionError as exc:
            logger.error("Cycle execution failed: {}", exc)
            error = str(exc)
        except Exception as exc:
            logger.error("Build-mvp precheck failed: {}", exc)
            error = str(exc)
        finally:
            if progression:
                cycles = progression.cycle_results
            self._write_summary(
                run_dir,
                stack,
                success,
                cycles,
                data_source_tag,
                run_status,
                error,
            )
            self._write_data_source(run_dir, data_source)
        return BuildResult(run_id, run_dir, success, error, cycles, data_source)

    def _normalize_cycles(self, requested: list[str] | None) -> list[str]:
        available = [key for key, *_ in MVPProgression.CYCLES]
        if not requested:
            return available
        filtered = [key for key in requested if key in available]
        if not filtered:
            raise MVPBuilderError(f"No valid cycle names found in {requested}")
        return filtered

    def _resolve_frontend_inputs(
        self,
        run_dir: Path,
        run_id: str,
        topic: str | None,
        brief: str | None,
    ) -> tuple[str, str | None, str | None]:
        app_name = (topic or brief or run_id).strip() or "Launchpad"
        audience = None
        front_brief = None
        top_name = None
        rationale = None

        top_path = run_dir / "top_idea.md"
        if top_path.exists():
            try:
                lines = [line.strip() for line in top_path.read_text(encoding="utf-8").splitlines()]
                for idx, line in enumerate(lines):
                    if line.lower().startswith("# top idea"):
                        for next_line in lines[idx + 1 :]:
                            if next_line and not next_line.lower().startswith("score:") and not next_line.lower().startswith("data source"):
                                top_name = next_line
                                break
                        break
                for idx, line in enumerate(lines):
                    if line.lower().startswith("score:"):
                        rationale = " ".join([part for part in lines[idx + 1 :] if part])
                        break
            except Exception:
                top_name = None

        opp_path = run_dir / "opportunities.json"
        if opp_path.exists():
            try:
                payload = json.loads(opp_path.read_text(encoding="utf-8"))
                for item in payload.get("items", []):
                    idea = item.get("idea") or {}
                    if top_name and idea.get("name") != top_name:
                        continue
                    if not top_name:
                        top_name = idea.get("name") or top_name
                    audience = idea.get("target_user") or audience
                    front_brief = idea.get("one_liner") or idea.get("solution") or idea.get("problem") or front_brief
                    break
            except Exception:
                pass

        prd_path = run_dir / "prd.md"
        if prd_path.exists() and not audience:
            icp = self._extract_icp_from_prd(prd_path.read_text(encoding="utf-8", errors="ignore"))
            if icp:
                audience = icp

        if top_name:
            app_name = top_name
        if len(app_name) > 40:
            app_name = " ".join(app_name.split()[:4]) or app_name[:40]

        if not front_brief:
            front_brief = self._first_sentence(rationale) or brief or topic

        if front_brief:
            front_brief = self._trim_copy(front_brief, limit=80)

        if audience:
            audience = self._trim_copy(audience, limit=60)

        return app_name, front_brief, audience

    def _extract_icp_from_prd(self, text: str) -> str | None:
        candidates = []
        for line in text.splitlines():
            stripped = line.strip().strip("-").strip("*").strip()
            if not stripped:
                continue
            lowered = stripped.lower()
            if lowered.startswith("icp") or "ideal customer" in lowered or lowered.startswith("target user"):
                if ":" in stripped:
                    candidates.append(stripped.split(":", 1)[1].strip())
                else:
                    candidates.append(stripped.replace("ICP", "").strip())
        return next((c for c in candidates if c), None)

    def _first_sentence(self, text: str | None) -> str | None:
        if not text:
            return None
        clean = " ".join(text.split())
        if "." in clean:
            return clean.split(".", 1)[0].strip() + "."
        return clean

    def _trim_copy(self, text: str, limit: int) -> str:
        clean = " ".join(text.split())
        if len(clean) <= limit:
            return clean
        truncated = clean[: limit - 1].rstrip()
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0]
        return truncated.rstrip() + "..."

    def _runner_from_verifier(self, verifier: MVPVerifier, flavor: str) -> Callable[[str, Path, int], tuple[bool, str]]:
        def runner(cycle_key: str, cycle_dir: Path, attempt: int) -> tuple[bool, str]:
            if flavor == "build":
                ok, log = verifier.run_build(attempt=attempt)
            else:
                ok, log = verifier.run_test(attempt=attempt)
            header = f"[{cycle_key}] {log}"
            return ok, header

        return runner

    def _ensure_within_runs(self, run_dir: Path) -> None:
        try:
            run_dir.resolve().relative_to(self.settings.runs_dir.resolve())
        except ValueError:
            raise MVPBuilderError("Target directory must live inside the configured runs directory.")

    def _prepare_target(self, run_dir: Path, force: bool) -> None:
        for child in ("mvp_repo", "mvp_cycles"):
            target = run_dir / child
            if target.exists():
                if force:
                    shutil.rmtree(target)
                else:
                    raise MVPBuilderError(
                        f"{child} already exists for {run_dir}. Use --force to overwrite."
                    )

    def _ensure_cycle_root(self, run_dir: Path) -> None:
        (run_dir / "mvp_cycles").mkdir(parents=True, exist_ok=True)

    def _write_scope(
        self,
        run_dir: Path,
        run_id: str,
        topic: str | None,
        brief: str | None,
        stack: StackConfig,
        cycles: list[str],
        data_source: str,
        frontend_style: str,
    ) -> None:
        payload = {
            "run_id": run_id,
            "topic": topic,
            "brief": brief,
            "frontend_style": frontend_style,
            "stack": {
                "frontend": stack.frontend_stack,
                "backend": stack.backend_stack,
                "database": stack.database,
            },
            "cycle_plan": cycles,
            "data_source": data_source,
            "generated_at": datetime.utcnow().isoformat(),
        }
        (run_dir / "mvp_scope.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_summary(
        self,
        run_dir: Path,
        stack: StackConfig,
        success: bool,
        cycles: list[dict],
        data_source_tag: str,
        run_status: str | None,
        error: str | None,
    ) -> None:
        status_line = "Prototype built" if success else "Prototype incomplete"
        lines = [
            "# MVP Build Summary",
            "",
            f"Status: {status_line}",
            f"Stack: {stack.frontend_stack} / {stack.backend_stack}",
            f"Data source tag: {data_source_tag}",
            f"Run status: {run_status or 'seed/brief'}",
            "",
            "## Cycle results",
        ]
        if cycles:
            for cycle in cycles:
                attempts = cycle.get("attempts", 1)
                lines.append(f"- {cycle['cycle']}: {cycle['status']} ({attempts} attempt(s))")
        else:
            lines.append("- no cycles were executed yet.")
        if error:
            lines.extend(["", "### Errors", error])
        lines.append("")
        lines.append("Prototype built = internal prototype, not market validated.")
        (run_dir / "mvp_build_summary.md").write_text("\n".join(lines), encoding="utf-8")
        self._write_build_info(run_dir, stack, success, cycles, data_source_tag, run_status, error)

    def _write_build_info(
        self,
        run_dir: Path,
        stack: StackConfig,
        success: bool,
        cycles: list[dict],
        data_source_tag: str,
        run_status: str | None,
        error: str | None,
    ) -> None:
        payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "status": "success" if success else "failed",
            "run_status": run_status,
            "data_source": data_source_tag,
            "stack": {
                "frontend": stack.frontend_stack,
                "backend": stack.backend_stack,
                "database": stack.database,
            },
            "cycle_plan": [item.get("cycle") for item in cycles] if cycles else [],
            "cycle_results": cycles,
            "commands": {
                "install": self.settings.mvp_install_command,
                "build": self.settings.mvp_build_command,
                "test": self.settings.mvp_test_command,
                "dev": self.settings.mvp_dev_command,
            },
            "timeouts": {
                "install_s": self.settings.mvp_install_timeout,
                "build_s": self.settings.mvp_build_timeout,
                "test_s": self.settings.mvp_test_timeout,
            },
            "error": error,
        }
        (run_dir / "build_info.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _compose_data_source(
        self,
        run_id: str,
        run_status: str | None,
        brief: str | None,
        topic: str | None,
        tag: str,
    ) -> dict:
        return {
            "run_id": run_id,
            "topic": topic,
            "brief": brief,
            "run_status": run_status,
            "data_source": tag,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _write_data_source(self, run_dir: Path, payload: dict) -> None:
        (run_dir / "mvp_data_source.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _resolve_data_source_tag(self, run_status: str | None, brief: str | None) -> str:
        if brief and not run_status:
            return "seed/brief"
        if run_status == "ABORT":
            return "seed/abort"
        if run_status:
            return "run"
        return "seed/brief"
