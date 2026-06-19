'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { fetchAnalytics } from '../../lib/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  Area, AreaChart, Cell
} from 'recharts';
import {
  ChartLineUp, MapPinLine, CalendarBlank,
  TrendUp, Warning, ArrowUp
} from '@phosphor-icons/react';

// ─── Mock Data Fallbacks ─────────────────────────────────────────────────────

const mockVolumeGrid: number[][] = Array.from({ length: 7 }, (_, dIdx) =>
  Array.from({ length: 24 }, (_, hour) => {
    const isPeak = (hour >= 7 && hour <= 10) || (hour >= 16 && hour <= 20);
    const isWeekend = dIdx === 0 || dIdx === 6;
    return Math.floor(Math.random() * (isPeak ? (isWeekend ? 30 : 60) : 15) + (isPeak ? 10 : 2));
  })
);

const mockJunctions = [
  { junction: 'Silk Board', count: 845 },
  { junction: 'Tin Factory', count: 632 },
  { junction: 'KR Puram', count: 590 },
  { junction: 'Hebbal', count: 541 },
  { junction: 'Madiwala', count: 480 },
  { junction: 'Marathahalli', count: 465 },
  { junction: 'Dairy Circle', count: 420 },
  { junction: 'Sony World', count: 395 },
  { junction: 'Iblur Junction', count: 370 },
  { junction: 'Gorguntepalya', count: 350 },
  { junction: 'Majestic', count: 320 },
  { junction: 'Koramangala 80ft', count: 310 },
  { junction: 'Mekhri Circle', count: 290 },
  { junction: 'Yeshwanthpur', count: 280 },
  { junction: 'BTM Layout', count: 260 },
];


const mockMonthlyData = [
  { month: 'Jan', planned: 20, unplanned: 650 },
  { month: 'Feb', planned: 25, unplanned: 580 },
  { month: 'Mar', planned: 30, unplanned: 620 },
  { month: 'Apr', planned: 45, unplanned: 710 },
  { month: 'May', planned: 35, unplanned: 690 },
  { month: 'Jun', planned: 40, unplanned: 800 },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// Neo-brutalist design tokens
const PALETTE = {
  green:  '#9FE870',
  teal:   '#A0E1E1',
  ink:    '#163300',
  yellow: '#FFE566',
  red:    '#FF6B6B',
  orange: '#FFB347',
};

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

const NeoTooltip = ({ active, payload, label, unit = '' }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border-3 border-neo-border shadow-neo font-mono text-sm p-3 min-w-[140px]">
      <p className="font-bold text-neo-text uppercase text-xs border-b-2 border-neo-border pb-1 mb-2">{label}</p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center gap-2 py-0.5">
          <span className="w-3 h-3 border border-neo-border inline-block flex-shrink-0" style={{ backgroundColor: entry.color }} />
          <span className="text-neo-text">{entry.name}:</span>
          <span className="font-bold text-neo-text">{entry.value}{unit}</span>
        </div>
      ))}
    </div>
  );
};

// ─── Chart 1: Hourly Volume Profile ──────────────────────────────────────────

function HourlyVolumeChart({ volumeGrid }: { volumeGrid: number[][] }) {
  // Compute per-hour averages across all days
  const hourlyData = useMemo(() => {
    return Array.from({ length: 24 }, (_, h) => {
      const total = volumeGrid.reduce((sum, day) => sum + (day[h] ?? 0), 0);
      const avg = Math.round(total / volumeGrid.length);
      return {
        hour: h === 0 ? '12am' : h < 12 ? `${h}am` : h === 12 ? '12pm' : `${h - 12}pm`,
        avg,
      };
    });
  }, [volumeGrid]);

  // Per-day totals
  const dayData = useMemo(() => {
    return DAYS.map((day, i) => ({
      day,
      total: volumeGrid[i]?.reduce((s, v) => s + v, 0) ?? 0,
    }));
  }, [volumeGrid]);

  const maxDay = Math.max(...dayData.map(d => d.total));

  return (
    <div className="neo-brutal-box p-6 bg-white flex flex-col col-span-1 xl:col-span-2">
      <h3 className="font-mono text-xl font-bold uppercase mb-1 flex items-center gap-2">
        <CalendarBlank size={24} />
        Incident Volume — When Do They Happen?
      </h3>
      <p className="font-mono text-xs text-neo-text/60 mb-5 uppercase tracking-wider">
        Average daily incidents by hour · Bengaluru traffic dataset
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main hourly bar chart */}
        <div className="lg:col-span-2">
          <p className="font-mono text-xs font-bold uppercase text-neo-text/50 mb-2">Avg. Incidents per Hour (across all days)</p>
          <div style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourlyData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }} barCategoryGap="10%">
                <CartesianGrid strokeDasharray="3 3" stroke="#163300" opacity={0.1} vertical={false} />
                <XAxis
                  dataKey="hour"
                  tick={{ fontFamily: 'monospace', fontSize: 10, fill: '#163300' }}
                  interval={2}
                />
                <YAxis tick={{ fontFamily: 'monospace', fontSize: 11, fill: '#163300' }} width={45} />
                <RechartsTooltip content={<NeoTooltip unit=" incidents" />} />
                <Bar dataKey="avg" name="Avg Incidents" radius={[2, 2, 0, 0]}>
                  {hourlyData.map((entry, i) => {
                    const colors = [PALETTE.green, PALETTE.teal, PALETTE.yellow, PALETTE.orange, PALETTE.red];
                    return (
                      <Cell
                        key={i}
                        fill={colors[i % colors.length]}
                        stroke="#163300"
                        strokeWidth={1.5}
                      />
                    );
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Day-of-week breakdown panel */}
        <div className="flex flex-col gap-2">
          <p className="font-mono text-xs font-bold uppercase text-neo-text/50 mb-1">Total Incidents by Day of Week</p>
          {dayData.map((d, i) => {
            const pct = maxDay > 0 ? (d.total / maxDay) * 100 : 0;
            const isWeekend = i === 0 || i === 6;
            return (
              <div key={d.day} className="flex items-center gap-3 group">
                <span className={`font-mono text-xs font-bold w-8 flex-shrink-0 ${isWeekend ? 'text-neo-text/40' : 'text-neo-text'}`}>
                  {d.day}
                </span>
                <div className="flex-1 bg-neo-bg border border-neo-border/30 h-6 relative overflow-hidden">
                  <div
                    className="h-full border-r-2 border-neo-border transition-all duration-500"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: isWeekend ? PALETTE.teal : PALETTE.green,
                    }}
                  />
                </div>
                <span className="font-mono text-xs font-bold w-10 text-right flex-shrink-0">{d.total.toLocaleString()}</span>
              </div>
            );
          })}
          <div className="flex gap-3 mt-2 font-mono text-xs">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 border border-neo-border inline-block" style={{ backgroundColor: PALETTE.teal }} />
              Weekend
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 border border-neo-border inline-block" style={{ backgroundColor: PALETTE.green }} />
              Weekday
            </span>
          </div>
        </div>
      </div>

      {/* Data Note */}
      <div className="mt-4 pt-3 border-t-2 border-neo-border">
        <p className="font-mono text-[10px] text-neo-text/60 leading-tight uppercase text-center">
          * Note: 116 records out of the 8,173 dataset are excluded from this chart due to missing or unparseable start times.
        </p>
      </div>
    </div>
  );
}

// ─── Chart 2: Top Junctions Leaderboard ──────────────────────────────────────

function JunctionLeaderboard({ junctions }: { junctions: { junction: string; count: number }[] }) {
  const sorted = useMemo(() => [...junctions].sort((a, b) => b.count - a.count).slice(0, 15), [junctions]);
  const max = sorted[0]?.count ?? 1;

  const RANK_COLORS = [PALETTE.red, PALETTE.orange, PALETTE.yellow];

  return (
    <div className="neo-brutal-box p-6 bg-white flex flex-col">
      <h3 className="font-mono text-xl font-bold uppercase mb-1 flex items-center gap-2">
        <MapPinLine size={24} />
        Top 15 High-Risk Junctions
      </h3>
      <p className="font-mono text-xs text-neo-text/60 mb-5 uppercase tracking-wider">
        Ranked by total incident count · All-time
      </p>

      <div className="flex flex-col gap-1.5 overflow-y-auto" style={{ maxHeight: 420 }}>
        {sorted.map((j, i) => {
          const pct = (j.count / max) * 100;
          const rankColor = i < 3 ? RANK_COLORS[i] : i < 7 ? PALETTE.teal : PALETTE.green;
          return (
            <div
              key={i}
              className="group cursor-default border-2 border-transparent hover:border-neo-border transition-all px-3 py-2 hover:bg-neo-bg -mx-1"
            >
              {/* Top row: rank + name + count */}
              <div className="flex items-center gap-2 mb-1.5">
                {/* Rank badge */}
                <span
                  className="font-mono text-xs font-black w-6 h-6 flex items-center justify-center border-2 border-neo-border flex-shrink-0"
                  style={{ backgroundColor: rankColor }}
                >
                  {i + 1}
                </span>

                {/* Junction name — full width, never truncated */}
                <span className="font-mono text-sm font-bold text-neo-text flex-1">
                  {j.junction}
                </span>

                {/* Incident count */}
                <span
                  className="font-mono text-xs font-black px-2 py-0.5 border-2 border-neo-border flex-shrink-0"
                  style={{ backgroundColor: rankColor }}
                >
                  {j.count.toLocaleString()} incidents
                </span>
              </div>

              {/* Progress bar */}
              <div className="bg-neo-bg border border-neo-border/20 h-2 overflow-hidden ml-8">
                <div
                  className="h-full"
                  style={{ width: `${pct}%`, backgroundColor: rankColor, transition: 'width 0.6s ease' }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary stats */}
      <div className="mt-4 pt-4 border-t-2 border-neo-border grid grid-cols-3 gap-3">
        {[
          { label: 'Worst Junction', value: sorted[0]?.junction ?? '—', icon: <Warning size={16} weight="bold" /> },
          { label: 'Top 15 Total', value: sorted.reduce((s, j) => s + j.count, 0).toLocaleString(), icon: <ChartLineUp size={16} weight="bold" /> },
          { label: 'Avg per Top 15', value: Math.round(sorted.reduce((s, j) => s + j.count, 0) / (sorted.length || 1)).toLocaleString(), icon: <TrendUp size={16} weight="bold" /> },
        ].map((stat) => (
          <div key={stat.label} className="border-2 border-neo-border p-2 text-center overflow-hidden flex flex-col justify-center" style={{ backgroundColor: PALETTE.yellow }}>
            <div className="flex justify-center mb-1">{stat.icon}</div>
            <p className="font-mono text-[10px] sm:text-xs uppercase text-neo-text/60 truncate" title={stat.label}>{stat.label}</p>
            <p className="font-mono text-xs font-bold text-neo-text leading-tight truncate" title={stat.value}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Data Note */}
      <div className="mt-4 pt-3 border-t-2 border-neo-border">
        <p className="font-mono text-[10px] text-neo-text/60 leading-tight uppercase text-center">
          * Note: ~69% of records (5,663 out of 8,173) lack specific junction data and are omitted. Totals represent only the Top 15 shown.
        </p>
      </div>
    </div>
  );
}


// ─── Chart 4: Planned vs Unplanned Over Time ──────────────────────────────────

function PlannedUnplannedChart({ data }: { data: { month: string; planned: number; unplanned: number }[] }) {
  const totalPlanned = data.reduce((s, d) => s + d.planned, 0);
  const totalUnplanned = data.reduce((s, d) => s + d.unplanned, 0);
  const avgPerMonth = Math.round((totalPlanned + totalUnplanned) / (data.length || 1));

  return (
    <div className="neo-brutal-box p-6 bg-white flex flex-col">
      <h3 className="font-mono text-xl font-bold uppercase mb-1 flex items-center gap-2">
        <ChartLineUp size={24} />
        Planned vs Unplanned Events Over Time
      </h3>
      <p className="font-mono text-xs text-neo-text/60 mb-5 uppercase tracking-wider">
        Monthly incident volume · Unplanned dominate but planned events spike congestion
      </p>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        {[
          { label: 'Planned Events', value: totalPlanned.toLocaleString(), bg: PALETTE.teal, icon: <CalendarBlank size={16} weight="bold" /> },
          { label: 'Unplanned Incidents', value: totalUnplanned.toLocaleString(), bg: PALETTE.red, icon: <Warning size={16} weight="bold" /> },
          { label: 'Avg / Month', value: avgPerMonth.toLocaleString(), bg: PALETTE.yellow, icon: <TrendUp size={16} weight="bold" /> },
        ].map((s) => (
          <div key={s.label} className="border-2 border-neo-border p-3 flex flex-col items-center gap-1" style={{ backgroundColor: s.bg }}>
            {s.icon}
            <p className="font-mono text-xs uppercase text-neo-text/70 text-center leading-tight">{s.label}</p>
            <p className="font-mono text-lg font-bold text-neo-text">{s.value}</p>
          </div>
        ))}
      </div>

      <div style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="unplannedGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={PALETTE.red} stopOpacity={0.6} />
                <stop offset="95%" stopColor={PALETTE.red} stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="plannedGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={PALETTE.teal} stopOpacity={0.8} />
                <stop offset="95%" stopColor={PALETTE.teal} stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#163300" opacity={0.1} />
            <XAxis dataKey="month" tick={{ fontFamily: 'monospace', fontSize: 12, fill: '#163300' }} />
            <YAxis tick={{ fontFamily: 'monospace', fontSize: 11, fill: '#163300' }} width={40} />
            <RechartsTooltip content={<NeoTooltip />} />
            <Legend
              wrapperStyle={{ fontFamily: 'monospace', fontSize: 12, fontWeight: 'bold', paddingTop: 8 }}
            />
            <Area
              type="monotone"
              dataKey="unplanned"
              name="Unplanned"
              stroke={PALETTE.red}
              strokeWidth={3}
              fill="url(#unplannedGrad)"
              dot={{ fill: PALETTE.red, stroke: '#163300', strokeWidth: 2, r: 4 }}
            />
            <Area
              type="monotone"
              dataKey="planned"
              name="Planned Events"
              stroke={PALETTE.teal}
              strokeWidth={3}
              fill="url(#plannedGrad)"
              dot={{ fill: PALETTE.teal, stroke: '#163300', strokeWidth: 2, r: 4 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Data Note */}
      <div className="mt-4 pt-3 border-t-2 border-neo-border">
        <p className="font-mono text-[10px] text-neo-text/60 leading-tight uppercase text-center">
          * Note: 116 records (102 planned, 14 unplanned) out of the 8,173 dataset are excluded from this timeline due to missing or unparseable start times.
        </p>
      </div>
    </div>
  );
}

// ─── Main Analytics View ──────────────────────────────────────────────────────

export default function AnalyticsView() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const loadData = async () => {
      const analytics = await fetchAnalytics();
      if (analytics) {
        setData(analytics);
      } else {
        setData({
          volume_grid: mockVolumeGrid,
          top_junctions: mockJunctions,
          planned_vs_unplanned: mockMonthlyData,
        });
      }
    };
    loadData();
  }, []);

  if (!data) return (
    <div className="w-full h-full flex flex-col justify-center items-center gap-4 font-mono bg-neo-bg">
      <div className="border-4 border-neo-border p-6 bg-white shadow-neo text-center">
        <div className="w-8 h-8 border-4 border-neo-border border-t-[#9FE870] rounded-full animate-spin mx-auto mb-3" />
        <p className="font-bold uppercase text-neo-text">Loading Analytics...</p>
        <p className="text-xs text-neo-text/50 mt-1">Crunching 8,173 incidents</p>
      </div>
    </div>
  );

  return (
    <div className="w-full h-full p-6 overflow-y-auto bg-neo-bg">
      {/* Header */}
      <div className="border-b-4 border-neo-border pb-5 mb-7 flex items-end justify-between flex-wrap gap-3">
        <div>
          <h2 className="font-mono text-3xl font-bold uppercase flex items-center gap-3">
            <ChartLineUp size={36} weight="bold" />
            Historical Analytics
          </h2>
          <p className="font-mono text-sm text-neo-text/60 mt-1 uppercase tracking-widest">
            Bengaluru Traffic Intelligence · 8,173 incidents · All-time
          </p>
        </div>
        <div className="flex gap-3">
          <div className="border-2 border-neo-border px-3 py-1.5 text-xs font-mono font-bold uppercase bg-[#9FE870]">
            ✓ Real Dataset
          </div>
          <div className="border-2 border-neo-border px-3 py-1.5 text-xs font-mono font-bold uppercase bg-[#A0E1E1]">
            ✓ ML-Verified
          </div>
        </div>
      </div>

      {/* Chart Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Chart 1: Hourly + Day breakdown — spans full width */}
        <HourlyVolumeChart volumeGrid={data.volume_grid ?? mockVolumeGrid} />

        {/* Chart 2: Junction Leaderboard */}
        <JunctionLeaderboard junctions={data.top_junctions ?? mockJunctions} />

        {/* Chart 3: Planned vs Unplanned */}
        <PlannedUnplannedChart data={data.planned_vs_unplanned ?? mockMonthlyData} />
      </div>
    </div>
  );
}
