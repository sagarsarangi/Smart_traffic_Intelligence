'use client';

import React from 'react';

// Smart Traffic Intelligence ticker facts
const TICKER_FACTS = [
    "SMART TRAFFIC INTELLIGENCE // BENGALURU",
    "4 AUTONOMOUS AI AGENTS",
    "8,173 REAL INCIDENTS ANALYZED",
    "XGBOOST CLASSIFICATION ENGINE",
    "ISOLATION FOREST ANOMALY DETECTION",
    "GROQ INFERENCE NLP PARSING",
    "REAL-TIME ZONE MONITORING",
    "SSE-STREAMED ACTION PLANS",
    "MULTILINGUAL INCIDENT PARSING",
    "PREDICTIVE TRAFFIC MANAGEMENT",
];

export default function NeoFooter() {
    const currentYear = new Date().getFullYear();
    return (
        <footer className="mt-auto border-t-4 border-neo-border bg-white overflow-hidden">
            {/* Hazard Tape Ticker */}
            <div className="bg-primary border-b-4 border-neo-border py-3 overflow-hidden">
                <div className="flex items-center">
                    <div className="flex-1 overflow-hidden">
                        <div className="ticker-scroll flex gap-10 animate-[scroll_30s_linear_infinite] whitespace-nowrap">
                            {[...TICKER_FACTS, ...TICKER_FACTS].map((fact, i) => (
                                <span key={i} className="font-mono text-sm font-bold text-black uppercase tracking-wider flex items-center gap-3">
                                    <span className="w-2 h-2 bg-black rotate-45" />
                                    {fact}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 pb-12 pt-6">
                <div className="mt-12 pt-8 border-t-3 border-neo-border flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="font-mono text-xs font-bold uppercase tracking-tighter">
                        © {currentYear} SMART TRAFFIC INTELLIGENCE // ALL RIGHTS RESERVED
                    </div>
                    <div className="flex items-center gap-4 font-mono text-[10px] font-bold text-neo-text/60 uppercase">
                        <span>Agentic AI for Bengaluru Traffic</span>
                        <div className="flex gap-1">
                            <div className="w-2 h-2 bg-primary animate-pulse" />
                            <div className="w-2 h-2 bg-black animate-pulse delay-75" />
                            <div className="w-2 h-2 bg-primary animate-pulse delay-150" />
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    );
}
