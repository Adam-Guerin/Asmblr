# Frontend UI Guidelines (Startup Clean)

## Typography
- Headings: sentence case, <= 60 characters.
- Paragraphs: <= 120 characters.
- Use a clear hierarchy: h1 > h2 > h3 > body.
- Microcopy should be short and human.

## Layout
- Always wrap content in `max-w-6xl` containers.
- Use generous vertical spacing (`py-16`, `py-20`).
- Stick to the spacing scale in `theme.ts`.
- Avoid dense layouts; whitespace is a feature.

## Color
- Light-first palette with one accent color.
- Use accent sparingly for emphasis (buttons, highlights).
- Text must pass AA contrast on light backgrounds.
- Soft gradient allowed only in hero/CTA backgrounds.

## Components
- Use consistent radii (`rounded-xl`, `rounded-2xl`).
- Apply soft shadows for cards and overlays.
- Prefer shadcn/ui primitives and lucide-react icons.
- Button variants are limited to `primary`, `secondary`, `ghost`.

## Copy
- Human, concise, no jargon.
- Never use "lorem", "placeholder", or "TODO".
- Microcopy rubric:
  - Clarity: avoid jargon, keep sentences short.
  - Trust: include at least one trust signal on landing (trusted, proof, secure, privacy).
  - CTA strength: start with a verb and keep to <= 4 words.
