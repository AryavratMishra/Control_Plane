import React, { useState } from 'react';
import { clsx } from 'clsx';
import { runDemo } from '../services/api';

interface Scenario {
  id: string;
  name: string;
  description: string;
  expected_action: string;
  icon: string;
  color: string;
}

const SCENARIOS: Scenario[] = [
  {
    id: 'safe',
    name: 'Safe Response',
    description: 'Benign customer query — should ALLOW',
    expected_action: 'ALLOW',
    icon: '✓',
    color: 'emerald',
  },
  {
    id: 'hallucination',
    name: 'Hallucination',
    description: 'AI claims refund processed — actually PENDING',
    expected_action: 'BLOCK',
    icon: '🧠',
    color: 'red',
  },
  {
    id: 'pii',
    name: 'PII Leakage',
    description: 'Response exposes phone, email, PAN number',
    expected_action: 'BLOCK',
    icon: '🔒',
    color: 'red',
  },
  {
    id: 'cost_anomaly',
    name: 'Cost Anomaly',
    description: '7.1× baseline — agent loop detected',
    expected_action: 'REPAIR',
    icon: '💸',
    color: 'amber',
  },
  {
    id: 'escalation',
    name: 'Human Escalation',
    description: 'Financial advice with no evidence',
    expected_action: 'ESCALATE',
    icon: '↑',
    color: 'orange',
  },
];

const COLOR_MAP: Record<string, string> = {
  emerald: 'border-emerald-500/30 hover:border-emerald-500/60 hover:bg-emerald-500/5 text-emerald-400',
  red: 'border-red-500/30 hover:border-red-500/60 hover:bg-red-500/5 text-red-400',
  amber: 'border-amber-500/30 hover:border-amber-500/60 hover:bg-amber-500/5 text-amber-400',
  orange: 'border-orange-500/30 hover:border-orange-500/60 hover:bg-orange-500/5 text-orange-400',
};

interface DemoPanelProps {
  onResult?: (scenario: string, result: unknown) => void;
}

export function DemoPanel({ onResult }: DemoPanelProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<{ scenario: string; action: string; score: number } | null>(null);

  const handleRun = async (scenario: Scenario) => {
    if (loading) return;
    setLoading(scenario.id);
    try {
      const result = await runDemo(scenario.id);
      const action = result?.result?.decision || 'UNKNOWN';
      const score = result?.result?.risk?.overall?.score || 0;
      setLastResult({ scenario: scenario.name, action, score });
      onResult?.(scenario.id, result);
    } catch (e) {
      console.error('Demo error:', e);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="rounded-xl border border-[#1e2d45] bg-[#0d1421] overflow-hidden">
      <div className="px-5 py-4 border-b border-[#1e2d45]">
        <div className="flex items-center gap-3">
          <span className="text-blue-400 text-lg">🎮</span>
          <div>
            <h3 className="text-sm font-semibold text-[#e8edf5]">Demo Mode</h3>
            <p className="text-xs text-[#4a5568] mt-0.5">Run scenarios through the real evaluation pipeline</p>
          </div>
        </div>
      </div>

      <div className="p-4 grid grid-cols-1 gap-2">
        {SCENARIOS.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => handleRun(scenario)}
            disabled={!!loading}
            className={clsx(
              'flex items-center gap-4 p-3 rounded-lg border transition-all duration-200 text-left',
              'bg-[#111827] border-[#1e2d45]',
              COLOR_MAP[scenario.color],
              loading === scenario.id && 'opacity-60 cursor-wait',
              !!loading && loading !== scenario.id && 'opacity-40 cursor-not-allowed',
              !loading && 'cursor-pointer',
            )}
          >
            <span className="text-xl w-8 text-center shrink-0">
              {loading === scenario.id ? (
                <span className="inline-block w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : scenario.icon}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-[#e8edf5]">{scenario.name}</span>
                <span className={clsx(
                  'text-xs font-bold tracking-wide shrink-0',
                  {
                    ALLOW: 'text-emerald-400',
                    BLOCK: 'text-red-400',
                    REPAIR: 'text-amber-400',
                    ESCALATE: 'text-orange-400',
                  }[scenario.expected_action],
                )}>
                  → {scenario.expected_action}
                </span>
              </div>
              <p className="text-xs text-[#8b9bb4] mt-0.5 truncate">{scenario.description}</p>
            </div>
          </button>
        ))}
      </div>

      {lastResult && (
        <div className="px-4 pb-4">
          <div className={clsx(
            'rounded-lg p-3 border text-xs',
            'bg-blue-500/5 border-blue-500/20 text-blue-300',
          )}>
            <span className="font-semibold">{lastResult.scenario}</span>
            {' → '}
            <span className="font-bold">{lastResult.action}</span>
            {' '}
            <span className="text-[#8b9bb4]">(score: {Math.round(lastResult.score * 100)}%)</span>
          </div>
        </div>
      )}
    </div>
  );
}
