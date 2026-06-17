import React, { useEffect, useState } from 'react';
import { fetchAnalytics } from '../../lib/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, LineChart, Line
} from 'recharts';
import { ChartLineUp, MapPinLine, Clock, CalendarBlank } from '@phosphor-icons/react';

// --- Mock Data Fallbacks ---

// Chart 1: Heatmap data (7 days x 24 hours)
const mockVolumeGrid = Array.from({ length: 7 }, () => 
    Array.from({ length: 24 }, (_, hour) => 
        Math.floor(Math.random() * (hour >= 8 && hour <= 20 ? 50 : 10))
    )
);

// Chart 2: Top 15 junctions
const mockJunctions = [
    { name: "Silk Board", count: 845 },
    { name: "Tin Factory", count: 632 },
    { name: "KR Puram", count: 590 },
    { name: "Hebbal", count: 541 },
    { name: "Madiwala", count: 480 },
    { name: "Marathahalli", count: 465 },
    { name: "Dairy Circle", count: 420 },
    { name: "Sony World", count: 395 },
    { name: "Iblur", count: 370 },
    { name: "Gorguntepalya", count: 350 },
    { name: "Majestic", count: 320 },
    { name: "Koramangala 80ft", count: 310 },
    { name: "Mekhri Circle", count: 290 },
    { name: "Yeshwanthpur", count: 280 },
    { name: "BTM Layout", count: 260 }
];

// Chart 3: Median resolution time by corridor
const mockCorridorTime = [
    { label: "Named Corridor", median_minutes: 45 },
    { label: "ORR Variant", median_minutes: 65 },
    { label: "Non-Corridor", median_minutes: 55 }
];

// Chart 4: Planned vs Unplanned over time (Monthly)
const mockMonthlyData = [
    { month: 'Jan', planned: 20, unplanned: 650 },
    { month: 'Feb', planned: 25, unplanned: 580 },
    { month: 'Mar', planned: 30, unplanned: 620 },
    { month: 'Apr', planned: 45, unplanned: 710 },
    { month: 'May', planned: 35, unplanned: 690 },
    { month: 'Jun', planned: 40, unplanned: 800 },
];

export default function AnalyticsView() {
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        const loadData = async () => {
            const analytics = await fetchAnalytics();
            if (analytics) {
                setData(analytics);
            } else {
                // fallback to mock
                setData({
                    volume_grid: mockVolumeGrid,
                    top_junctions: mockJunctions,
                    corridor_durations: mockCorridorTime,
                    planned_vs_unplanned: mockMonthlyData
                });
            }
        };
        loadData();
    }, []);

    if (!data) return (
        <div className="w-full h-full flex justify-center items-center font-mono font-bold uppercase">
            Loading Analytics...
        </div>
    );

    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    return (
        <div className="w-full p-8 overflow-y-auto bg-neo-bg">
            <h2 className="font-mono text-3xl font-bold uppercase mb-8 border-b-4 border-neo-border pb-4 flex items-center gap-4">
                <ChartLineUp size={36} weight="bold" />
                Historical Analytics
            </h2>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
                
                {/* Chart 1: Heatmap */}
                <div className="neo-brutal-box p-6 bg-white flex flex-col">
                    <h3 className="font-mono text-xl font-bold uppercase mb-4 flex items-center gap-2">
                        <CalendarBlank size={24} />
                        Incident Volume (Day vs Hour)
                    </h3>
                    <div className="flex-1 min-h-[300px]">
                        <div className="grid grid-cols-[auto_repeat(24,_1fr)] gap-1 text-xs font-mono h-full">
                            {/* Header row */}
                            <div className="col-start-2 col-end-[26] grid grid-cols-24 gap-1 border-b-2 border-neo-border pb-1">
                                {Array.from({length: 24}, (_, i) => (
                                    <div key={i} className="text-center">{i}</div>
                                ))}
                            </div>
                            
                            {/* Body */}
                            {days.map((day, dIdx) => (
                                <React.Fragment key={dIdx}>
                                    <div className="flex items-center font-bold pr-2 border-r-2 border-neo-border">{day}</div>
                                    <div className="col-start-2 col-end-[26] grid grid-cols-24 gap-1">
                                        {Array.from({length: 24}, (_, hIdx) => {
                                            const count = data.volume_grid && data.volume_grid[dIdx] ? data.volume_grid[dIdx][hIdx] : 0;
                                            // Max count is around 50 in mock, scale opacity
                                            const opacity = Math.min(count / 60, 1);
                                            return (
                                                <div 
                                                    key={`${dIdx}-${hIdx}`} 
                                                    className="w-full h-8 border border-neo-border/20 relative group"
                                                    style={{ backgroundColor: `rgba(239, 68, 68, ${opacity})` }} // Red shade
                                                >
                                                    <div className="absolute hidden group-hover:block z-10 bg-neo-text text-neo-bg p-1 -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap shadow-neo-sm">
                                                        {count} incidents
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </React.Fragment>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Chart 2: Top Junctions */}
                <div className="neo-brutal-box p-6 bg-white h-[450px] flex flex-col">
                    <h3 className="font-mono text-xl font-bold uppercase mb-4 flex items-center gap-2">
                        <MapPinLine size={24} />
                        Top 15 Problematic Junctions
                    </h3>
                    <div className="flex-1 w-full h-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                layout="vertical"
                                data={data.top_junctions}
                                margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#163300" opacity={0.2} horizontal={false} />
                                <XAxis type="number" tick={{ fontFamily: 'monospace', fontSize: 12, fill: '#163300' }} />
                                <YAxis dataKey="name" type="category" width={120} tick={{ fontFamily: 'monospace', fontSize: 11, fill: '#163300' }} />
                                <RechartsTooltip 
                                    contentStyle={{ backgroundColor: '#fff', border: '3px solid #163300', boxShadow: '4px 4px 0px #163300', borderRadius: 0, fontFamily: 'monospace' }}
                                />
                                <Bar dataKey="count" fill="#9FE870" stroke="#163300" strokeWidth={2} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Chart 3: Corridor Resolution Time */}
                <div className="neo-brutal-box p-6 bg-white h-[400px] flex flex-col">
                    <h3 className="font-mono text-xl font-bold uppercase mb-4 flex items-center gap-2">
                        <Clock size={24} />
                        Resolution Time by Corridor Type
                    </h3>
                    <div className="flex-1 w-full h-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={data.corridor_durations}
                                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#163300" opacity={0.2} vertical={false} />
                                <XAxis dataKey="label" tick={{ fontFamily: 'monospace', fontSize: 12, fill: '#163300' }} />
                                <YAxis tick={{ fontFamily: 'monospace', fontSize: 12, fill: '#163300' }} label={{ value: 'Minutes', angle: -90, position: 'insideLeft', fontFamily: 'monospace' }} />
                                <RechartsTooltip 
                                    contentStyle={{ backgroundColor: '#fff', border: '3px solid #163300', boxShadow: '4px 4px 0px #163300', borderRadius: 0, fontFamily: 'monospace' }}
                                />
                                <Bar dataKey="median_minutes" fill="#a0e1e1" stroke="#163300" strokeWidth={2} name="Median Minutes" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Chart 4: Planned vs Unplanned Volume */}
                <div className="neo-brutal-box p-6 bg-white h-[400px] flex flex-col">
                    <h3 className="font-mono text-xl font-bold uppercase mb-4 flex items-center gap-2">
                        <ChartLineUp size={24} />
                        Event Type Volume Over Time
                    </h3>
                    <div className="flex-1 w-full h-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                                data={data.planned_vs_unplanned}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#163300" opacity={0.2} />
                                <XAxis dataKey="month" tick={{ fontFamily: 'monospace', fontSize: 12, fill: '#163300' }} />
                                <YAxis tick={{ fontFamily: 'monospace', fontSize: 12, fill: '#163300' }} />
                                <RechartsTooltip 
                                    contentStyle={{ backgroundColor: '#fff', border: '3px solid #163300', boxShadow: '4px 4px 0px #163300', borderRadius: 0, fontFamily: 'monospace' }}
                                />
                                <Legend wrapperStyle={{ fontFamily: 'monospace', fontSize: 12, fontWeight: 'bold' }} />
                                <Line type="monotone" dataKey="unplanned" stroke="#ef4444" strokeWidth={4} activeDot={{ r: 8 }} name="Unplanned Incidents" />
                                <Line type="monotone" dataKey="planned" stroke="#3b82f6" strokeWidth={4} activeDot={{ r: 8 }} name="Planned Events" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

            </div>
        </div>
    );
}
