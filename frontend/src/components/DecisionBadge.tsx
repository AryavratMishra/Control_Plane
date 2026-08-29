import React from 'react';
import { clsx } from 'clsx';

interface DecisionBadgeProps {
  action: string;
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
}

const ACTION_CONFIG: Record<string, { label: string; icon: string; classes: string; dot: string }> = {
  ALLOW: {
    label: 'ALLOW',
    icon: '✓',
    classes: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
    dot: 'bg-emerald-400',
  },
  REPAIR: {
    label: 'REPAIR',
    icon: '⚡',
    classes: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
    dot: 'bg-amber-400',
  },
  ESCALATE: {
    label: 'ESCALATE',
    icon: '↑',
    classes: 'bg-orange-500/15 text-orange-400 border border-orange-500/30',
    dot: 'bg-orange-400',
  },
  BLOCK: {
    label: 'BLOCK',
    icon: '✕',
    classes: 'bg-red-500/15 text-red-400 border border-red-500/30',
    dot: 'bg-red-400',
  },
};

const RISK_CONFIG: Record<string, { classes: string }> = {
  LOW: { classes: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' },
  MEDIUM: { classes: 'bg-amber-500/15 text-amber-400 border border-amber-500/30' },
  HIGH: { classes: 'bg-red-500/15 text-red-400 border border-red-500/30' },
  CRITICAL: { classes: 'bg-red-600/20 text-red-300 border border-red-600/50' },
  UNVERIFIED: { classes: 'bg-purple-500/15 text-purple-400 border border-purple-500/30' },
};

export function DecisionBadge({ action, size = 'md', animated = false }: DecisionBadgeProps) {
  const config = ACTION_CONFIG[action] || ACTION_CONFIG.ALLOW;
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-3 py-1 gap-1.5',
    lg: 'text-sm px-4 py-1.5 gap-2',
  }[size];

  return (
    <span className={clsx(
      'inline-flex items-center font-semibold rounded-full tracking-wide',
      config.classes,
      sizeClasses,
    )}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', config.dot, animated && action !== 'ALLOW' && 'animate-pulse')} />
      {config.icon} {config.label}
    </span>
  );
}

export function RiskBadge({ level }: { level: string }) {
  const config = RISK_CONFIG[level] || RISK_CONFIG.LOW;
  return (
    <span className={clsx(
      'inline-flex items-center text-xs font-semibold px-2.5 py-0.5 rounded-full tracking-wide',
      config.classes,
    )}>
      {level}
    </span>
  );
}
