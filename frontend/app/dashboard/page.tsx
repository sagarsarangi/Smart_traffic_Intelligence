'use client';

import React, { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import SubmitIncidentView from '../../components/dashboard/SubmitIncidentView';
import AnalyticsView from '../../components/dashboard/AnalyticsView';
import IncidentPanel from '../../components/dashboard/IncidentPanel';
import { MapTrifold, Plus, ChartBar, WarningCircle, ArrowsClockwise } from '@phosphor-icons/react';
import { checkBackendHealth, fetchHeatmap } from '../../lib/api';
import type { IncidentPin } from '../../types/index';

// Leaflet map needs to be dynamically imported with ssr: false
const MapView = dynamic(() => import('../../components/dashboard/MapView'), {
    ssr: false,
    loading: () => (
        <div className="w-full h-full flex items-center justify-center bg-neo-bg">
            <div className="font-mono text-neo-text font-bold uppercase text-xl border-4 border-neo-border p-4 bg-neo-secondary shadow-neo">
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
    const [isBackendActive, setIsBackendActive] = useState<boolean>(true);
    const [isDataLoaded, setIsDataLoaded] = useState<boolean>(false);
    const [initialHeatmap, setInitialHeatmap] = useState<Array<[number, number, number]>>([]);

    const isDataLoadedRef = useRef(false);

    useEffect(() => {
        let isMounted = true;
        const pollHealth = async () => {
            const isHealthy = await checkBackendHealth();
            if (isHealthy) {
                if (!isDataLoadedRef.current) {
                    const heatRes = await fetchHeatmap();
                    if (heatRes !== null && isMounted) {
                        setInitialHeatmap(heatRes.map((h: any) => [h.lat, h.lng, h.weight]));
                        isDataLoadedRef.current = true;
                        setIsDataLoaded(true);
                    }
                }
                if (isMounted) setIsBackendActive(true);
            } else {
                if (isMounted) setIsBackendActive(false);
            }
        };
        pollHealth();
        const interval = setInterval(pollHealth, 3000);
        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    // ── Incident pins — shared between SubmitIncidentView and MapView ──────────
    // Accumulated over the session; survive view switches but reset on page refresh.
    const [incidentPins, setIncidentPins] = useState<IncidentPin[]>([]);

    const addIncidentPin = (pin: { lat: number; lng: number; zone: string }) => {
        setIncidentPins(prev => [
            ...prev,
            { ...pin, id: `pin-${Date.now()}-${Math.random().toString(36).slice(2)}` },
        ]);
    };

    const openPanelWithData = (data: any) => {
        setPanelData(data);
        setIsPanelOpen(true);
    };

    const closePanel = () => {
        setIsPanelOpen(false);
    };

    if (!isBackendActive || !isDataLoaded) {
        return (
            <div className="flex flex-col h-[calc(100vh-80px)] w-full overflow-hidden bg-neo-bg relative items-center justify-center">
                <div className="absolute inset-0 z-[3000] bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
                    <div className="bg-neo-bg border-4 border-neo-border p-8 shadow-[8px_8px_0_0_rgba(22,51,0,1)] max-w-md w-full flex flex-col items-center text-center">
                        {(!isBackendActive) ? (
                            <>
                                <WarningCircle size={64} className="text-red-500 mb-4" weight="bold" />
                                <h2 className="text-2xl font-black uppercase tracking-tighter mb-2">Backend Offline</h2>
                                <p className="font-mono text-sm text-gray-600 mb-6">
                                    Cannot connect to the server. Waiting for it to come online...
                                </p>
                            </>
                        ) : (
                            <>
                                <div className="animate-spin mb-4">
                                    <ArrowsClockwise size={64} className="text-neo-primary" weight="bold" />
                                </div>
                                <h2 className="text-2xl font-black uppercase tracking-tighter mb-2">Loading City Data</h2>
                                <p className="font-mono text-sm text-gray-600 mb-6">
                                    Backend is online. Retrieving ML models and map datasets...
                                </p>
                            </>
                        )}
                        <div className="w-full h-3 border-2 border-neo-border bg-white overflow-hidden p-0.5">
                            <div className="h-full bg-primary w-full"></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-[calc(100vh-80px)] w-full overflow-hidden bg-neo-bg relative">
            {/* Dashboard Sub-navigation */}
            <div className="flex border-b-3 border-neo-border bg-white z-20 shadow-neo-sm relative overflow-x-auto">
                <button
                    onClick={() => setActiveView('map')}
                    className={`flex items-center gap-2 px-4 md:px-6 py-3 md:py-4 font-mono text-sm md:text-base font-bold uppercase border-r-3 border-neo-border transition-all whitespace-nowrap flex-shrink-0 ${activeView === 'map' ? 'bg-neo-primary text-neo-text border-b-4 border-b-neo-text' : 'bg-white hover:bg-neo-secondary'}`}
                >
                    <MapTrifold size={22} weight="bold" className="flex-shrink-0" />
                    City Map
                    {incidentPins.length > 0 && (
                        <span className="ml-1 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full border-2 border-neo-border">
                            {incidentPins.length}
                        </span>
                    )}
                </button>
                <button
                    onClick={() => setActiveView('submit')}
                    className={`flex items-center gap-2 px-4 md:px-6 py-3 md:py-4 font-mono text-sm md:text-base font-bold uppercase border-r-3 border-neo-border transition-all whitespace-nowrap flex-shrink-0 ${activeView === 'submit' ? 'bg-neo-primary text-neo-text border-b-4 border-b-neo-text' : 'bg-white hover:bg-neo-secondary'}`}
                >
                    <Plus size={22} weight="bold" className="flex-shrink-0" />
                    Submit Incident
                </button>
                <button
                    onClick={() => setActiveView('analytics')}
                    className={`flex items-center gap-2 px-4 md:px-6 py-3 md:py-4 font-mono text-sm md:text-base font-bold uppercase border-r-3 border-neo-border transition-all whitespace-nowrap flex-shrink-0 ${activeView === 'analytics' ? 'bg-neo-primary text-neo-text border-b-4 border-b-neo-text' : 'bg-white hover:bg-neo-secondary'}`}
                >
                    <ChartBar size={22} weight="bold" className="flex-shrink-0" />
                    Analytics
                </button>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 relative flex overflow-hidden">
                <div className="flex-1 bg-grid relative flex flex-col overflow-hidden">
                    <div className={`absolute inset-0 z-10 ${activeView === 'map' ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
                        <MapView
                            onOpenPanel={openPanelWithData}
                            incidentPins={incidentPins}
                            onNewIncident={() => setActiveView('submit')}
                            initialHeatmap={initialHeatmap}
                        />
                    </div>
                    <div className={`absolute inset-0 z-10 ${activeView === 'submit' ? 'block' : 'hidden'}`}>
                        <SubmitIncidentView
                            onOpenPanel={openPanelWithData}
                            onPinDropped={addIncidentPin}
                        />
                    </div>
                    <div className={`absolute inset-0 z-10 ${activeView === 'analytics' ? 'block' : 'hidden'}`}>
                        <AnalyticsView />
                    </div>
                </div>

                {/* Incident Panel Drawer */}
                <div
                    className={`absolute top-0 right-0 h-full w-full md:w-[500px] bg-white border-l-4 border-neo-border transform transition-transform duration-300 z-50 shadow-[-8px_0_0_0_rgba(22,51,0,1)] ${isPanelOpen ? 'translate-x-0' : 'translate-x-full'}`}
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
                        className="absolute inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
                        onClick={closePanel}
                    />
                )}
            </div>
        </div>
    );
}
