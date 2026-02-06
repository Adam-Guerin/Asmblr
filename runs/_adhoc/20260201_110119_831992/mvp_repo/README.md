# Audit-ready MVP MVP

## Stack
- Frontend: Next.js + Tailwind CSS + shadcn-inspired UI + TypeScript
- Backend: Next.js API routes + Prisma + SQLite
- Database: SQLite

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
