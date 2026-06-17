import React, { useState } from 'react';
import Link from 'next/link';
import { List as Menu, X } from '@phosphor-icons/react';

export default function NeoNavbar() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <nav className="sticky top-0 z-50 w-full bg-white border-b-3 border-neo-border">
            <div className="max-w-7xl mx-auto px-4 md:px-6 w-full relative">
                <div className="flex items-center justify-between h-16 md:h-20 relative">

                    {/* Left Section: Hamburger (mobile/tablet) */}
                    <div className="flex items-center gap-3 relative z-10">
                        {/* Hamburger Menu - Mobile & Tablet, on left */}
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="lg:hidden w-12 h-12 border-3 border-neo-border bg-white flex items-center justify-center shadow-neo-sm hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none hover:bg-secondary transition-all"
                            aria-label="Toggle menu"
                        >
                            {isMenuOpen ? <X weight="bold" className="w-6 h-6" /> : <Menu weight="bold" className="w-6 h-6" />}
                        </button>
                    </div>

                    {/* Desktop Navigation - Absolutely Centered - Visible only on LG+ */}
                    <div className="hidden lg:flex items-center gap-1 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
                        <Link href="/" className="px-4 py-2 group cursor-pointer">
                            <div className="w-14 h-10 border-3 border-neo-border bg-primary flex items-center justify-center shadow-neo-sm group-hover:translate-x-[2px] group-hover:translate-y-[2px] group-hover:shadow-none transition-all">
                                <span className="font-mono font-bold text-xl text-black uppercase">NEO</span>
                            </div>
                        </Link>
                        <Link
                            href="/about"
                            className="px-4 py-2 font-mono text-sm font-bold border-2 border-transparent hover:border-neo-border hover:bg-secondary text-black transition-all uppercase tracking-tight"
                        >
                            About
                        </Link>
                        <Link
                            href="/projects"
                            className="px-4 py-2 font-mono text-sm font-bold border-2 border-transparent hover:border-neo-border hover:bg-secondary text-black transition-all uppercase tracking-tight"
                        >
                            Selected Works
                        </Link>
                        <Link
                            href="/dashboard"
                            className="px-4 py-2 font-mono text-sm font-bold border-2 border-transparent hover:border-neo-border hover:bg-secondary text-black transition-all uppercase tracking-tight"
                        >
                            Dashboard
                        </Link>
                        <Link
                            href="/journey"
                            className="px-4 py-2 font-mono text-sm font-bold border-2 border-transparent hover:border-neo-border hover:bg-secondary text-black transition-all uppercase tracking-tight"
                        >
                            Journey
                        </Link>
                        <Link
                            href="/contact"
                            className="px-4 py-2 font-mono text-sm font-bold border-2 border-transparent hover:border-neo-border hover:bg-secondary text-black transition-all uppercase tracking-tight"
                        >
                            Contact
                        </Link>
                    </div>

                    {/* Right Section: Hidden or Empty for now to maintain layout */}
                    <div className="flex items-center gap-3 relative z-10 lg:w-[150px] justify-end">
                        {/* AI Button Removed */}
                    </div>
                </div>
            </div>

            {/* Mobile Menu */}
            {isMenuOpen && (
                <div className="lg:hidden absolute top-full left-0 w-full bg-white border-b-3 border-neo-border p-4 flex flex-col gap-4 shadow-neo">
                    <Link
                        href="/"
                        onClick={() => setIsMenuOpen(false)}
                        className="block w-full py-3 px-4 text-center font-mono font-bold uppercase border-2 border-transparent hover:bg-secondary hover:border-neo-border"
                    >
                        NEO
                    </Link>
                    <Link
                        href="/about"
                        onClick={() => setIsMenuOpen(false)}
                        className="block w-full py-3 px-4 text-center font-mono font-bold uppercase border-2 border-transparent hover:bg-secondary hover:border-neo-border"
                    >
                        About
                    </Link>
                    <Link
                        href="/projects"
                        onClick={() => setIsMenuOpen(false)}
                        className="block w-full py-3 px-4 text-center font-mono font-bold uppercase border-2 border-transparent hover:bg-secondary hover:border-neo-border"
                    >
                        Selected Works
                    </Link>
                    <Link
                        href="/dashboard"
                        onClick={() => setIsMenuOpen(false)}
                        className="block w-full py-3 px-4 text-center font-mono font-bold uppercase border-2 border-transparent hover:bg-secondary hover:border-neo-border"
                    >
                        Dashboard
                    </Link>
                    <Link
                        href="/journey"
                        onClick={() => setIsMenuOpen(false)}
                        className="block w-full py-3 px-4 text-center font-mono font-bold uppercase border-2 border-transparent hover:bg-secondary hover:border-neo-border"
                    >
                        Journey
                    </Link>
                    <Link
                        href="/contact"
                        onClick={() => setIsMenuOpen(false)}
                        className="block w-full py-3 px-4 text-center font-mono font-bold uppercase border-2 border-transparent hover:bg-secondary hover:border-neo-border"
                    >
                        Contact
                    </Link>
                </div>
            )}
        </nav>
    );
}
