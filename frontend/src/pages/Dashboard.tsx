import React, { useEffect, useState, useCallback } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import { getDashboard } from '../services/api';
import { LiveEventStream } from '../components/LiveEventStream';
import { DemoPanel } from '../components/DemoPanel';
import { IncidentTable } from '../components/IncidentTable';
import { useWebSocket } from '../hooks/useWebSocket';
import { clsx } from 'clsx';

interface DashboardData {
  total_requests: number;
  allowed: number;
  repaired: number;
  escalated: number;
  blocked: number;
  estimated_cost_saved_inr: number;
  average_evaluation_ms: number;
  performance_risk_rate: number;
  cost_risk_rate: number;
  responsibility_risk_rate: number;
  intervention_rate: number;
  recent_incidents: unknown[];
  risk_trend: unknown[];
  action_breakdown: Record<string, number>;
}

const KPI_CONFIGS = [
  { key: 'total_requests', label: 'Total Requests', icon: '📊', color: 'blue' },
  { key: 'allowed', label: 'Allowed', icon: '✓', color: 'emerald' },
  { key: 'repaired', label: 'Repaired', icon: '⚡', color: 'amber' },
  { key: 'escalated', label: 'Escalated', icon: '↑', color: 'orange' },
  { key: 'blocked', label: 'Blocked', icon: '✕', color: 'red' },
];

const COLOR_MAP: Record<string, string> = {
  blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  orange: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  red: 'text-red-400 bg-red-500/10 border-red-500/20',
};

const PIE_COLORS = ['#10b981', '#f59e0b', '#f97316', '#ef4444'];

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const { events, connected } = useWebSocket();

  const loadData = useCallback(async () => {
    try {
      const d = await getDashboard();
      setData(d);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, [loadData]);

  // Refresh when a new WS event comes in
  useEffect(() => {
    if (events.length > 0) {
      loadData();
    }
  }, [events.length]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#8b9bb4]">Loading Control Room...</p>
        </div>
      </div>
    );
  }

  const pieData = [
    { name: 'Allowed', value: data?.allowed || 0 },
    { name: 'Repaired', value: data?.repaired || 0 },
    { name: 'Escalated', value: data?.escalated || 0 },
    { name: 'Blocked', value: data?.blocked || 0 },
  ].filter(d => d.value > 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#e8edf5]">
            AI Control Room
          </h1>
          <p className="text-sm text-[#8b9bb4] mt-1">
            Real-time AI governance & risk monitoring
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className={clsx(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs border',
            connected
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-red-500/10 text-red-400 border-red-500/30',
          )}>
            <span className={clsx('w-1.5 h-1.5 rounded-full', connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400')} />
            {connected ? 'Live' : 'Disconnected'}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {KPI_CONFIGS.map(({ key, label, icon, color }) => (
          <div
            key={key}
            className={clsx(
              'rounded-xl p-5 border',
              'bg-[#0d1421] border-[#1e2d45]',
              'hover:border-[#243450] transition-all duration-300',
            )}
          >
            <div className={clsx('inline-flex items-center justify-center w-8 h-8 rounded-lg border text-sm mb-3', COLOR_MAP[color])}>
              {icon}
            </div>
            <div className={clsx('text-2xl font-bold', {
              blue: 'text-blue-400',
              emerald: 'text-emerald-400',
              amber: 'text-amber-400',
              orange: 'text-orange-400',
              red: 'text-red-400',
            }[color])}>
              {(data?.[key as keyof DashboardData] as number || 0).toLocaleString()}
            </div>
            <div className="text-xs text-[#8b9bb4] mt-1 font-medium">{label}</div>
          </div>
        ))}
      </div>

      {/* Cost Saved + Latency */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl p-5 border bg-[#0d1421] border-[#1e2d45]">
          <div className="text-xs text-[#8b9bb4] font-semibold uppercase tracking-wider mb-1">Cost Saved</div>
          <div className="text-2xl font-bold text-emerald-400">
            ₹{(data?.estimated_cost_saved_inr || 0).toFixed(2)}
          </div>
          <div className="text-xs text-[#4a5568] mt-1">By intercepting cost anomalies</div>
        </div>
        <div className="rounded-xl p-5 border bg-[#0d1421] border-[#1e2d45]">
          <div className="text-xs text-[#8b9bb4] font-semibold uppercase tracking-wider mb-1">Avg. Evaluation Time</div>
          <div className="text-2xl font-bold text-blue-400">
            {Math.round(data?.average_evaluation_ms || 0)}ms
          </div>
          <div className="text-xs text-[#4a5568] mt-1">Fast path &lt;200ms · Deep path varies</div>
        </div>
      </div>

      {/* Charts + Live Stream + Demo */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Trend Chart */}
        <div className="lg:col-span-2 rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <h3 className="text-sm font-semibold text-[#e8edf5] mb-4">Risk Trend (24h)</h3>
          {(data?.risk_trend?.length || 0) > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={data?.risk_trend || []}>
                <defs>
                  <linearGradient id="blocked" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="repaired" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a2235" />
                <XAxis dataKey="hour" tick={{ fill: '#4a5568', fontSize: 10 }} />
                <YAxis tick={{ fill: '#4a5568', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ background: '#0d1421', border: '1px solid #1e2d45', borderRadius: 8 }}
                  labelStyle={{ color: '#8b9bb4', fontSize: 11 }}
                />
                <Area type="monotone" dataKey="blocked" stroke="#ef4444" fill="url(#blocked)" strokeWidth={2} />
                <Area type="monotone" dataKey="repaired" stroke="#f59e0b" fill="url(#repaired)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-[#4a5568]">
              <div className="text-center">
                <p className="text-sm">No trend data yet</p>
                <p className="text-xs mt-1">Run demo scenarios to generate data</p>
              </div>
            </div>
          )}
        </div>

        {/* Action Breakdown */}
        <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <h3 className="text-sm font-semibold text-[#e8edf5] mb-4">Action Breakdown</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((_, idx) => (
                    <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#0d1421', border: '1px solid #1e2d45', borderRadius: 8 }}
                />
                <Legend
                  wrapperStyle={{ fontSize: 11, color: '#8b9bb4' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-[#4a5568] text-sm">
              No data yet
            </div>
          )}
        </div>
      </div>

      {/* Live Stream + Demo Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LiveEventStream events={events} connected={connected} />
        <DemoPanel />
      </div>

      {/* Recent Incidents */}
      <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] overflow-hidden">
        <div className="px-5 py-4 border-b border-[#1e2d45]">
          <h3 className="text-sm font-semibold text-[#e8edf5]">Recent Incidents</h3>
        </div>
        <IncidentTable incidents={(data?.recent_incidents || []) as Parameters<typeof IncidentTable>[0]['incidents']} />
      </div>
    </div>
  );
}
