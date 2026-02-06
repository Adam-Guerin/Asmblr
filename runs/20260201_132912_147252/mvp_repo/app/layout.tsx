import './globals.css';

export const metadata = {
  title: 'Audit MVP pass run',
  description: 'Prototype built from Next.js + Tailwind CSS + shadcn-inspired UI + TypeScript and Next.js API routes + Prisma + SQLite',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
