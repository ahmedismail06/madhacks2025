"use client";

import React from 'react';
import Image from "next/image";

export default function Navbar() {
    return (
        <nav className="w-full border-b border-b-foreground/10 sticky md:static top-0 z-50 bg-siteBackgroundColor">
            <div className="max-w-7xl mx-auto flex justify-between items-center h-full px-4 py-5">
                {/* Site Logo */}
                <div className="h-[30px]">
                    <Image
                        src="/logo.png"
                        alt="Logo"
                        width={542}
                        height={100}
                        priority
                        className="h-full w-auto"
                    />
                </div>

                {/* Title */}
                <h1 className="text-3xl font-bold" style={{ color: 'var(--color-sitePrimaryColor)' }}>
                    Fiber-optic Optimization Simulation
                </h1>
            </div>
        </nav>
    );
}
