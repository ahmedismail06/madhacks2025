"use client";

import React, {useState} from 'react';
import {SITE_BACKGROUND_COLOR, SITE_NAME, SITE_PRIMARY_COLOR, SITE_SECONDARY_COLOR, SITE_TEXT_COLOR} from "@/lib/config";
import Link from "next/link";
import Image from "next/image";

export default function Navbar() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const navLinks = [
        { href: "/", text: "Home" },
        { href: "/demo", text: "Demo" },
    ];

    return (
        <nav className="w-full border-b border-b-foreground/10 h-18 sticky md:static top-0 z-50 bg-siteBackgroundColor">
            <div className="max-w-7xl mx-auto flex justify-between items-center h-full px-4">
                {/* Site Logo */}
                <Link href="/" className="font-bold text-3xl" style={{ color: SITE_PRIMARY_COLOR }}>
                    <div className="h-[30px]">
                      <Image
                      src="/logo.png"
                      alt={SITE_NAME}
                      width={542}
                      height={100}
                      priority
                      className="h-full w-auto"
                    />
                    </div>
                </Link>

                {/* Desktop Navigation */}
                <div className="hidden md:flex items-center gap-6">
                    {navLinks.map((link) => (
                        <Link key={link.href} href={link.href} className="text-2xl font-medium hover:underline transition-colors duration-300" style={{color:SITE_PRIMARY_COLOR}}>
                            {link.text}
                        </Link>
                    ))}
                    {/*<LogoutButton />*/}

                    {/* GitHub link (desktop only) */}
                    <a
                        href="https://github.com/ahmedismail06/madhacks2025"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hidden md:inline-flex items-center justify-center p-1 rounded hover:opacity-90"
                        aria-label="View project on GitHub"
                        title="View project on GitHub"
                        style={{ color: SITE_PRIMARY_COLOR }}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32" fill="none" aria-hidden>
                            <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.09 3.29 9.4 7.86 10.92.58.11.79-.25.79-.56 0-.28-.01-1.02-.02-2-3.2.7-3.88-1.38-3.88-1.38-.53-1.36-1.3-1.72-1.3-1.72-1.06-.72.08-.71.08-.71 1.17.08 1.79 1.2 1.79 1.2 1.04 1.78 2.72 1.27 3.38.97.11-.76.41-1.27.75-1.56-2.55-.29-5.24-1.28-5.24-5.71 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.48.11-3.09 0 0 .97-.31 3.18 1.18a11 11 0 0 1 2.9-.39c.98 0 1.97.13 2.9.39 2.2-1.49 3.17-1.18 3.17-1.18.63 1.61.23 2.8.11 3.09.74.81 1.19 1.84 1.19 3.1 0 4.45-2.7 5.41-5.27 5.69.42.36.79 1.08.79 2.18 0 1.57-.01 2.84-.01 3.23 0 .31.21.68.8.56C20.71 21.4 24 17.09 24 12 24 5.65 18.35.5 12 .5z" fill={SITE_PRIMARY_COLOR} />
                        </svg>
                    </a>
                </div>

                {/* Mobile Menu Button */}
                <div className="md:hidden flex items-center">
                    <button
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        className="focus:outline-none"
                        aria-label="Toggle menu"
                        style={{color:SITE_PRIMARY_COLOR}}
                    >
                        {isMenuOpen ? (
                            // Close Icon (X)
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        ) : (
                            // Hamburger Icon
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16m-7 6h7" />
                            </svg>
                        )}
                    </button>
                </div>
            </div>

            {/* Mobile Menu - Dropdown */}
            <div
                className={`md:hidden absolute top-16 left-0 w-full bg-siteBackgroundColor shadow-lg transition-all duration-300 ease-in-out ${
                    isMenuOpen
                        ? 'opacity-100 translate-y-0 visible'
                        : 'opacity-0 -translate-y-4 invisible'
                }`}
            >
                <div className="flex flex-col items-center gap-4 p-4">
                    {navLinks.map((link) => (
                        <Link
                            key={link.href}
                            href={link.href}
                            className="text-2xl font-medium text-sitePrimaryColor hover:text-sitePrimaryColor w-full text-center py-2"
                            onClick={() => setIsMenuOpen(false)}
                        >
                            {link.text}
                        </Link>
                    ))}
                    <div className="mt-2 px-4 mx-auto">
                         {/*<LogoutButton />*/}
                    </div>
                </div>
            </div>
        </nav>
    );
}