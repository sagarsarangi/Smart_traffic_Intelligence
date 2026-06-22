'use client';

import { usePathname } from 'next/navigation';
import NeoNavbar from './NeoNavbar';
import NeoFooter from './NeoFooter';
import { useEffect } from 'react';

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  // Silent wake-up ping for Render cold starts
  useEffect(() => {
    // Fire and forget: this will wake up the backend if it's sleeping
    fetch(process.env.NEXT_PUBLIC_API_URL + '/ping').catch(() => {});
  }, []);

  return (
    <>
      <NeoNavbar />
      <main id="main-content" className="w-full min-h-screen bg-neo-bg overflow-x-hidden">
        <div key={pathname} className="route-fade">
          {children}
        </div>
      </main>
      <NeoFooter />
    </>
  );
}
