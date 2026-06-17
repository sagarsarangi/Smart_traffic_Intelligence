'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import SubmitIncidentView from '../../components/dashboard/SubmitIncidentView';
import AnalyticsView from '../../components/dashboard/AnalyticsView';
import IncidentPanel from '../../components/dashboard/IncidentPanel';
import { MapTrifold, Plus, ChartBar } from '@phosphor-icons/react';

// Leaflet map needs to be dynamically imported with ssr: false
const MapView = dynamic(() => import('../../components/dashboard/MapView'), {
    ssr: false,
    loading: () => (
        <div className="w-full h-full flex items-center justify-center bg-neo-bg">
            <div className="font-mono text-neo-text font-bold uppercase animate-pulse text-xl border-4 border-neo-border p-4 bg-neo-secondary shadow-neo">
                Loading Map Data...
            </div>
        </div>
    )
});

type ViewState = 'map' | 'submit' | 'analytics';

export default function DashboardPage() {
    const [activeView, setActiveView] = useState<ViewState>('map');
    const [panelData, setPanelData] = useState<any>(null);
    const [isPanelOpen, setIsPanelOpen] = useState(false);

    const openPanelWithData = (data: any) => {
        setPanelData(data);
        setIsPanelOpen(true);
    };

    const closePanel = () => {
        setIsPanelOpen(false);
    };

    return (
        <div className="flex flex-col h-[calc(100vh-80px)] w-full overflow-hidden bg-neo-bg relative">
            {/* Dashboard Sub-navigation */}
            <div className="flex border-b-3 border-neo-border bg-white z-20 shadow-neo-sm relative">
                <button
                    onClick={() => setActiveView('map')}
                    className={`flex items-center gap-2 px-6 py-4 font-mono font-bold uppercase border-r-3 border-neo-border transition-all ${activeView === 'map' ? 'bg-neo-primary text-neo-text border-b-4 border-b-neo-text' : 'bg-white hover:bg-neo-secondary'}`}
                >
                    <MapTrifold size={24} weight="bold" />
                    City Map
                </button>
                <button
                    onClick={() => setActiveView('submit')}
                    className={`flex items-center gap-2 px-6 py-4 font-mono font-bold uppercase border-r-3 border-neo-border transition-all ${activeView === 'submit' ? 'bg-neo-primary text-neo-text border-b-4 border-b-neo-text' : 'bg-white hover:bg-neo-secondary'}`}
                >
                    <Plus size={24} weight="bold" />
                    Submit Incident
                </button>
                <button
                    onClick={() => setActiveView('analytics')}
                    className={`flex items-center gap-2 px-6 py-4 font-mono font-bold uppercase border-r-3 border-neo-border transition-all ${activeView === 'analytics' ? 'bg-neo-primary text-neo-text border-b-4 border-b-neo-text' : 'bg-white hover:bg-neo-secondary'}`}
                >
                    <ChartBar size={24} weight="bold" />
                    Analytics
                </button>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 relative flex overflow-hidden">
                <div className="flex-1 overflow-y-auto bg-grid relative">
                    {activeView === 'map' && <MapView onOpenPanel={openPanelWithData} />}
                    {activeView === 'submit' && <SubmitIncidentView onOpenPanel={openPanelWithData} />}
                    {activeView === 'analytics' && <AnalyticsView />}
                </div>

                {/* Incident Panel Drawer */}
                <div 
                    className={`absolute top-0 right-0 h-full w-full md:w-[500px] bg-white border-l-4 border-neo-border transform transition-transform duration-300 z-30 shadow-[-8px_0_0_0_rgba(22,51,0,1)] ${isPanelOpen ? 'translate-x-0' : 'translate-x-full'}`}
                >
                    <IncidentPanel 
                        isOpen={isPanelOpen} 
                        onClose={closePanel} 
                        data={panelData} 
                    />
                </div>
                
                {/* Overlay for mobile panel */}
                {isPanelOpen && (
                    <div 
                        className="absolute inset-0 bg-black/50 z-20 md:hidden backdrop-blur-sm"
                        onClick={closePanel}
                    />
                )}
            </div>
        </div>
    );
}
