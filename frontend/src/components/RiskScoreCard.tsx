import React from 'react';
import { clsx } from 'clsx';

interface RiskScoreCardProps {
  label: string;
  score: number;
  level: string;
  reasons?: string[];
  icon?: React.ReactNode;
}

function getBarColor(level: string) {
  return {
    LOW: 'from-emerald-500 to-emerald-400',
    MEDIUM: 'from-amber-500 to-amber-400',
    HIGH: 'from-red-500 to-red-400',
    CRITICAL: 'from-red-700 to-red-500',
    UNVERIFIED: 'from-purple-500 to-purple-400',
  }[level] || 'from-gray-500 to-gray-400';
}

function getLevelColor(level: string) {
  return {
    LOW: 'text-emerald-400',
    MEDIUM: 'text-amber-400',
    HIGH: 'text-red-400',
    CRITICAL: 'text-red-300',
    UNVERIFIED: 'text-purple-400',
  }[level] || 'text-gray-400';
}

export function RiskScoreCard({ label, score, level, reasons = [], icon }: RiskScoreCardProps) {
  const pct = Math.round(score * 100);
  const barColor = getBarColor(level);
  const levelColor = getLevelColor(level);

  return (
    <div className={clsx(
      'rounded-xl p-5 border transition-all duration-300',
      'bg-[#0d1421] border-[#1e2d45]',
      'hover:border-[#243450] hover:shadow-lg hover:shadow-blue-500/5',
    )}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {icon && <span className="text-blue-400">{icon}</span>}
          <span className="text-sm font-semibold text-[#8b9bb4] uppercase tracking-wider">{label}</span>
        </div>
        <span className={clsx('text-sm font-bold tracking-wide', levelColor)}>{level}</span>
      </div>

      <div className="mb-3">
        <div className="flex items-end gap-2 mb-2">
          <span className="text-3xl font-bold text-[#e8edf5]">{pct}</span>
          <span className="text-sm text-[#8b9bb4] mb-1">/ 100</span>
        </div>
        <div className="h-2 rounded-full bg-[#1a2235] overflow-hidden">
          <div
            className={clsx('h-full rounded-full bg-gradient-to-r transition-all duration-1000', barColor)}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {reasons.length > 0 && (
        <div className="mt-3 space-y-1">
          {reasons.slice(0, 2).map((r, i) => (
            <p key={i} className="text-xs text-[#8b9bb4] leading-relaxed flex items-start gap-1.5">
              <span className="mt-0.5 text-[#4a5568]">›</span>
              {r}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
