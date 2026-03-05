import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Tech Aggregator',
  description: 'Discover, compare, and get expert advice on AI/ML technologies',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
