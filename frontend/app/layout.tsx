import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Spotter AI - Fuel Routing Optimization',
  description: 'Production-grade fuel routing optimization system with intelligent fuel stop planning',
  keywords: ['fuel routing', 'route optimization', 'fuel stops', 'logistics', 'fleet management'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
