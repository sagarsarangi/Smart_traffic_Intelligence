import "./globals.css";
import type { Metadata } from "next";
import { Space_Grotesk, Space_Mono } from "next/font/google";
import ClientLayout from "../components/ClientLayout";

// Font for headings
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

// Font for body/code
const spaceMono = Space_Mono({
  weight: ["400", "700"],
  subsets: ["latin"],
  variable: "--font-space-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Smart Traffic Intelligence // Bengaluru",
    template: "%s // Smart Traffic Intelligence",
  },
  description: "Agentic AI platform for predictive traffic management in Bengaluru — 4 autonomous agents analyzing 8,173 real incidents for priority classification, anomaly detection, and automated response planning.",
  icons: {
    icon: "/favicon.ico",
  },
};

import NextTopLoader from 'nextjs-toploader';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${spaceGrotesk.variable} ${spaceMono.variable} font-display bg-neo-bg text-neo-text`}
      >
        <NextTopLoader color="#163300" height={4} showSpinner={false} shadow="none" />
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
