import React, { useEffect, useState, useCallback } from "react";
import {
  ResponsiveContainer, PieChart, Pie, Cell, Legend, Tooltip,
} from "recharts";
import { getDashboard } from "../services/api";
import { LiveEventStream } from "../components/LiveEventStream";
import { DemoPanel } from "../components/DemoPanel";
import { CustomEvalPanel } from "../components/CustomEvalPanel";
import { IncidentTable } from "../components/IncidentTable";
import { useWebSocket } from "../hooks/useWebSocket";
import { clsx } from "clsx";

interface InspectorResult {
  request_text?: string;
  original_response?: string;
  final_response?: string;
  decision?: string;
  reasons?: string[];
  risk?: {
    overall?: { score: number; level: string };
    performance?: { score: number; level: string };
    cost?: { score: number; level: string };
    responsibility?: { score: number; level: string };
  };
  pii_entities?: { type: string; text: string }[];
  evidence?: { source?: string; content?: string; score?: number }[];
  fast_screen_ms?: number;
  total_evaluation_ms?: number;
  is_live_response?: boolean;
  repair_applied?: boolean;
}

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

const BAR_GRADIENT: Record<string, string> = {
  LOW: "from-emerald-500 to-emerald-400",
  MEDIUM: "from-amber-500 to-amber-400",
  HIGH: "from-red-500 to-red-400",
  CRITICAL: "from-red-700 to-red-500",
  UNVERIFIED: "from-purple-500 to-purple-400",
};

const LEVEL_COLOR: Record<string, string> = {
  LOW: "text-emerald-400",
  MEDIUM: "text-amber-400",
  HIGH: "text-red-400",
  CRITICAL: "text-red-300",
  UNVERIFIED: "text-purple-400",
};

const DECISION_BADGE: Record<string, string> = {
  ALLOW: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  BLOCK: "bg-red-500/15 text-red-400 border-red-500/30",
  REPAIR: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  ESCALATE: "bg-orange-500/15 text-orange-400 border-orange-500/30",
};

function RiskBar({ label, score, level, icon }: { label: string; score: number; level: string; icon: string }) {
  const pct = Math.round(score * 100);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-sm">{icon}</span>
          <span className="text-[11px] font-semibold text-[#8b9bb4] uppercase tracking-wider">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={clsx("text-[10px] font-bold tracking-wider", LEVEL_COLOR[level] || "text-gray-400")}>{level}</span>
          <span className="text-sm font-bold text-[#e8edf5] tabular-nums w-7 text-right">{pct}</span>
        </div>
      </div>
      <div className="h-2 rounded-full bg-[#1a2235] overflow-hidden">
        <div
          className={clsx("h-full rounded-full bg-gradient-to-r transition-all duration-1000 ease-out", BAR_GRADIENT[level] || "from-gray-500 to-gray-400")}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function AIInspector({ result, scenarioName }: { result: InspectorResult; scenarioName: string }) {
  const decision = result.decision || "UNKNOWN";
  const overallPct = Math.round((result.risk?.overall?.score || 0) * 100);
  const overallLevel = result.risk?.overall?.level || "LOW";

  return (
    <div className="flex flex-col bg-[#080c14] border border-[#1e2d45] rounded-xl overflow-hidden shadow-xl shadow-black/30">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e2d45] bg-[#0d1421]">
        <div className="flex items-center gap-2.5">
          <span className="text-xl">🔍</span>
          <div>
            <h4 className="text-xs font-bold text-[#e8edf5]">Evaluation Trace</h4>
            <div className="text-[10px] text-[#4a5568]">Scenario: <span className="text-[#8b9bb4]">{scenarioName}</span></div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {result.is_live_response && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/20 text-[9px] font-bold text-blue-400 uppercase tracking-wider">
              <span className="w-1 h-1 rounded-full bg-blue-400 animate-pulse" />Live AI
            </span>
          )}
          <span className={clsx("px-2.5 py-0.5 rounded-full border text-[10px] font-bold tracking-wider", DECISION_BADGE[decision] || "bg-gray-500/10 text-gray-400 border-gray-500/30")}>
            {decision}
          </span>
        </div>
      </div>

      <div className="overflow-y-auto max-h-[520px] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[#1e2d45] [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-[#2a3f5f]">

        <div className="px-4 pt-4 pb-3 border-b border-[#1e2d45]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold text-[#4a5568] uppercase tracking-wider">Overall Risk Score</span>
            <span className="text-2xl font-bold text-[#e8edf5] tabular-nums">{overallPct}<span className="text-xs text-[#4a5568] ml-0.5">/100</span></span>
          </div>
          <div className="h-3 rounded-full bg-[#1a2235] overflow-hidden">
            <div className={clsx("h-full rounded-full bg-gradient-to-r transition-all duration-1000 ease-out", BAR_GRADIENT[overallLevel] || "from-gray-500 to-gray-400")} style={{ width: `${overallPct}%` }} />
          </div>
        </div>

        <div className="px-4 py-3 border-b border-[#1e2d45] space-y-3">
          <span className="text-[10px] font-bold text-[#4a5568] uppercase tracking-wider block">Risk Dimensions</span>
          <RiskBar label="Performance" score={result.risk?.performance?.score || 0} level={result.risk?.performance?.level || "LOW"} icon="🧠" />
          <RiskBar label="Responsibility" score={result.risk?.responsibility?.score || 0} level={result.risk?.responsibility?.level || "LOW"} icon="🔒" />
          <RiskBar label="Cost" score={result.risk?.cost?.score || 0} level={result.risk?.cost?.level || "LOW"} icon="💸" />
        </div>

        {result.request_text && (
          <div className="px-4 py-3 border-b border-[#1e2d45]">
            <div className="rounded-lg bg-sky-500/10 border border-sky-500/25 p-3">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-sky-400 uppercase tracking-wider mb-1.5">
                <span>👤</span>
                <span>User Request</span>
              </div>
              <p className="text-xs text-sky-100 font-medium leading-relaxed break-words bg-sky-950/40 p-2.5 rounded border border-sky-500/20">
                {result.request_text}
              </p>
            </div>
          </div>
        )}

        <div className="px-4 py-3 border-b border-[#1e2d45]">
          <div className="rounded-lg bg-indigo-500/10 border border-indigo-500/25 p-3">
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-indigo-400 uppercase tracking-wider mb-1.5">
              <span>🤖</span>
              <span>AI Response</span>
            </div>
            <p className="text-xs text-indigo-100 font-mono leading-relaxed whitespace-pre-wrap break-words bg-indigo-950/40 p-2.5 rounded border border-indigo-500/20">
              {result.original_response}
            </p>
          </div>
        </div>

        {result.repair_applied && result.final_response && result.final_response !== result.original_response && (
          <div className="px-4 py-3 border-b border-[#1e2d45]">
            <div className="rounded-lg bg-amber-500/10 border border-amber-500/25 p-3">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-amber-400 uppercase tracking-wider mb-1.5">
                <span>✦</span>
                <span>Repaired Response</span>
              </div>
              <p className="text-xs text-amber-100 font-mono leading-relaxed whitespace-pre-wrap break-words bg-amber-950/40 p-2.5 rounded border border-amber-500/20">
                {result.final_response}
              </p>
            </div>
          </div>
        )}

        {result.reasons && result.reasons.length > 0 && (
          <div className="px-4 py-3 border-b border-[#1e2d45]">
            <span className="text-[10px] font-bold text-red-400 uppercase tracking-wider block mb-2">📋 Why This Decision</span>
            <ul className="space-y-1.5">
              {result.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-[11px] text-[#8b9bb4] leading-relaxed">
                  <span className="text-[#4a5568] shrink-0 mt-0.5">›</span><span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.pii_entities && result.pii_entities.length > 0 && (
          <div className="px-4 py-3 border-b border-[#1e2d45]">
            <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider block mb-2">🔒 PII Detected</span>
            <div className="flex flex-wrap gap-1.5">
              {result.pii_entities.map((p, i) => (
                <span key={i} className="px-2 py-0.5 rounded-full bg-purple-500/15 border border-purple-500/30 text-purple-300 text-[10px] font-mono">
                  {p.type}: <span className="text-purple-400 font-bold">{p.text}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {result.evidence && result.evidence.length > 0 && (
          <div className="px-4 py-3 border-b border-[#1e2d45]">
            <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider block mb-2">🗂 Evidence ({result.evidence.length})</span>
            <div className="space-y-2">
              {result.evidence.slice(0, 3).map((ev, i) => (
                <div key={i} className="rounded-lg bg-blue-500/5 border border-blue-500/10 px-3 py-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-blue-400 font-semibold truncate">{ev.source || `Source ${i + 1}`}</span>
                    {ev.score !== undefined && <span className="text-[9px] text-blue-300 shrink-0 ml-2">{Math.round(ev.score * 100)}%</span>}
                  </div>
                  {ev.content && <p className="text-[10px] text-[#4a5568] leading-relaxed line-clamp-2">{ev.content}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="px-4 py-2.5 flex items-center gap-4 text-[10px] text-[#2d3748] bg-[#080c14]">
          <span>⏱ Fast screen: <span className="text-[#4a5568]">{result.fast_screen_ms ?? 0}ms</span></span>
          <span>Total eval: <span className="text-[#4a5568]">{result.total_evaluation_ms ?? 0}ms</span></span>
          <span className="ml-auto">{result.is_live_response ? "🟢 Live Gemini" : "⚪ Fallback"}</span>
        </div>
      </div>
    </div>
  );
}

const KPI_CONFIGS = [
  { key: "total_requests", label: "Total Requests", icon: "📊", color: "blue" },
  { key: "allowed", label: "Allowed", icon: "✓", color: "emerald" },
  { key: "repaired", label: "Repaired", icon: "⚡", color: "amber" },
  { key: "escalated", label: "Escalated", icon: "↑", color: "orange" },
  { key: "blocked", label: "Blocked", icon: "✕", color: "red" },
];

const COLOR_MAP: Record<string, string> = {
  blue: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  amber: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  orange: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  red: "text-red-400 bg-red-500/10 border-red-500/20",
};

const PIE_COLORS = ["#10b981", "#f59e0b", "#f97316", "#ef4444"];

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const { events, connected } = useWebSocket();
  const [inspectorResult, setInspectorResult] = useState<InspectorResult | null>(null);
  const [inspectorScenario, setInspectorScenario] = useState<string>("");

  const handleDemoResult = useCallback((scenario: string, result: any) => {
    setInspectorScenario(scenario);
    setInspectorResult(result?.result ?? result);
  }, []);

  const handleCustomEvalResult = useCallback((result: any) => {
    setInspectorScenario("Custom API Evaluation");
    setInspectorResult(result);
  }, []);

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
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    if (events.length > 0) loadData();
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
    { name: "Allowed", value: data?.allowed || 0 },
    { name: "Repaired", value: data?.repaired || 0 },
    { name: "Escalated", value: data?.escalated || 0 },
    { name: "Blocked", value: data?.blocked || 0 },
  ].filter(d => d.value > 0);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#e8edf5]">AI Control Room</h1>
          <p className="text-sm text-[#8b9bb4] mt-1">Real-time AI governance &amp; risk monitoring</p>
        </div>
        <div className={clsx("flex items-center gap-2 px-3 py-1.5 rounded-full text-xs border", connected ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-red-500/10 text-red-400 border-red-500/30")}>
          <span className={clsx("w-1.5 h-1.5 rounded-full", connected ? "bg-emerald-400 animate-pulse" : "bg-red-400")} />
          {connected ? "Live" : "Disconnected"}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {KPI_CONFIGS.map(({ key, label, icon, color }) => (
          <div key={key} className={clsx("rounded-xl p-5 border bg-[#0d1421] border-[#1e2d45] hover:border-[#243450] transition-all duration-300")}>
            <div className={clsx("inline-flex items-center justify-center w-8 h-8 rounded-lg border text-sm mb-3", COLOR_MAP[color])}>{icon}</div>
            <div className={clsx("text-2xl font-bold", ({ blue: "text-blue-400", emerald: "text-emerald-400", amber: "text-amber-400", orange: "text-orange-400", red: "text-red-400" } as Record<string,string>)[color])}>
              {(data?.[key as keyof DashboardData] as number || 0).toLocaleString()}
            </div>
            <div className="text-xs text-[#8b9bb4] mt-1 font-medium">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl p-5 border bg-[#0d1421] border-[#1e2d45]">
          <div className="text-xs text-[#8b9bb4] font-semibold uppercase tracking-wider mb-1">Cost Saved</div>
          <div className="text-2xl font-bold text-emerald-400">₹{(data?.estimated_cost_saved_inr || 0).toFixed(2)}</div>
          <div className="text-xs text-[#4a5568] mt-1">By intercepting cost anomalies</div>
        </div>
        <div className="rounded-xl p-5 border bg-[#0d1421] border-[#1e2d45]">
          <div className="text-xs text-[#8b9bb4] font-semibold uppercase tracking-wider mb-1">Avg. Evaluation Time</div>
          <div className="text-2xl font-bold text-blue-400">{Math.round(data?.average_evaluation_ms || 0)}ms</div>
          <div className="text-xs text-[#4a5568] mt-1">Fast path &lt;200ms</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[#e8edf5]">AI Interaction Inspector</h3>
            <span className="text-[10px] text-[#4a5568]">Click any demo scenario to inspect</span>
          </div>
          {inspectorResult ? (
            <AIInspector result={inspectorResult} scenarioName={inspectorScenario} />
          ) : (
            <div className="flex flex-col items-center justify-center h-48 gap-3 text-center">
              <div className="w-14 h-14 rounded-2xl border border-[#1e2d45] bg-[#080c14] flex items-center justify-center text-3xl">🔍</div>
              <div>
                <p className="text-sm text-[#4a5568]">No interaction yet</p>
                <p className="text-xs text-[#2d3748] mt-1">Run a demo scenario below to inspect the full AI evaluation</p>
              </div>
            </div>
          )}
        </div>

        <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <h3 className="text-sm font-semibold text-[#e8edf5] mb-4">Action Breakdown</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
                  {pieData.map((_, idx) => (<Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />))}
                </Pie>
                <Tooltip contentStyle={{ background: "#0d1421", border: "1px solid #1e2d45", borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 11, color: "#8b9bb4" }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-[#4a5568] text-sm">No data yet</div>
          )}
        </div>
      </div>

      {/* ── Custom API Evaluation ─────────────────────────────────────────── */}
      <CustomEvalPanel onResult={handleCustomEvalResult} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LiveEventStream events={events} connected={connected} />
        <DemoPanel onResult={handleDemoResult} />
      </div>

      <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] overflow-hidden">
        <div className="px-5 py-4 border-b border-[#1e2d45]">
          <h3 className="text-sm font-semibold text-[#e8edf5]">Recent Incidents</h3>
        </div>
        <IncidentTable incidents={(data?.recent_incidents || []) as Parameters<typeof IncidentTable>[0]["incidents"]} />
      </div>
    </div>
  );
}
