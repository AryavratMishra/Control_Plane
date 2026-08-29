import React from 'react';
import { clsx } from 'clsx';
import { DecisionBadge } from './DecisionBadge';
import type { RiskEvent } from '../hooks/useWebSocket';

const ACTION_ICONS: Record<string, string> = {
  ALLOW: '✓',
  REPAIR: '⚡',
  ESCALATE: '↑',
  BLOCK: '🚫',
};

const APP_ICONS: Record<string, string> = {
  'customer-support': '💬',
  'finance-assistant': '💰',
  'internal-knowledge': '📚',
};

interface LiveEventStreamProps {
  events: RiskEvent[];
  connected: boolean;
}

export function LiveEventStream({ events, connected }: LiveEventStreamProps) {
  return (
    <div className="rounded-xl border border-[#1e2d45] bg-[#0d1421] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#1e2d45]">
        <div className="flex items-center gap-3">
          <div className={clsx(
            'w-2 h-2 rounded-full',
            connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
          )} />
          <h3 className="text-sm font-semibold text-[#e8edf5]">Live Risk Stream</h3>
        </div>
        <span className={clsx(
          'text-xs px-2 py-0.5 rounded-full',
          connected
            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
            : 'bg-red-500/15 text-red-400 border border-red-500/30'
        )}>
          {connected ? 'LIVE' : 'DISCONNECTED'}
        </span>
      </div>

      {/* Events */}
      <div className="divide-y divide-[#1a2235] max-h-80 overflow-y-auto">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-[#4a5568]">
            <span className="text-3xl mb-3">📡</span>
            <p className="text-sm">Waiting for events...</p>
            <p className="text-xs mt-1">Run a demo scenario to see live events</p>
          </div>
        ) : (
          events.map((event, idx) => (
            <div
              key={idx}
              className={clsx(
                'flex items-center gap-4 px-5 py-3 transition-colors hover:bg-[#111827]',
                idx === 0 && 'animate-fade-in',
              )}
            >
              <span className="text-xs text-[#4a5568] font-mono w-20 shrink-0">
                {event.timestamp
                  ? new Date(event.timestamp).toLocaleTimeString('en-IN', { hour12: false })
                  : '--:--:--'
                }
              </span>
              <span className="text-base w-6 text-center">
                {APP_ICONS[event.application || ''] || '🤖'}
              </span>
              <span className="text-sm text-[#8b9bb4] flex-1 min-w-0 truncate">
                {event.application || 'AI App'}
              </span>
              <DecisionBadge action={event.action || 'ALLOW'} size="sm" animated />
              {event.scores && (
                <span className="text-xs text-[#4a5568] font-mono w-16 text-right shrink-0">
                  {Math.round((event.scores.overall || 0) * 100)}%
                </span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
