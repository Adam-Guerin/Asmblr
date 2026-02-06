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
