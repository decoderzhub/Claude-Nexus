import type { Metadata } from 'next';
import { JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { NexusProvider } from '@/components/providers/NexusProvider';

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: 'Claude Nexus',
  description: 'A persistent self-reflective environment for Claude',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={jetbrainsMono.variable}>
      <body className="bg-nexus-dark min-h-screen">
        <NexusProvider>{children}</NexusProvider>
      </body>
    </html>
  );
}
