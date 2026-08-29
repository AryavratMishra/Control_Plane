import React from 'react';
import { useNavigate } from 'react-router-dom';
import { DecisionBadge, RiskBadge } from './DecisionBadge';
import { formatDistanceToNow } from 'date-fns';

interface Incident {
  id: string;
  incident_type: string;
  severity: string;
  action: string;
  status: string;
  reason: string;
  application_name: string;
  request_text: string;
  created_at: string;
}

interface IncidentTableProps {
  incidents: Incident[];
  onSelect?: (id: string) => void;
}

const TYPE_ICONS: Record<string, string> = {
  hallucination: '🧠',
  pii_leakage: '🔒',
  cost_anomaly: '💸',
  escalation: '↑',
  policy_violation: '⚠️',
  unknown: '❓',
};

const STATUS_CONFIG: Record<string, { label: string; classes: string }> = {
  open: { label: 'Open', classes: 'bg-orange-500/15 text-orange-400 border border-orange-500/30' },
  under_review: { label: 'Under Review', classes: 'bg-blue-500/15 text-blue-400 border border-blue-500/30' },
  resolved: { label: 'Resolved', classes: 'bg-[#1a2235] text-[#8b9bb4] border border-[#1e2d45]' },
};

export function IncidentTable({ incidents, onSelect }: IncidentTableProps) {
  const navigate = useNavigate();

  const handleClick = (id: string) => {
    if (onSelect) {
      onSelect(id);
    } else {
      navigate(`/incidents/${id}`);
    }
  };

  if (incidents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-[#4a5568]">
        <span className="text-5xl mb-4">🛡️</span>
        <p className="text-lg font-semibold text-[#8b9bb4]">No incidents found</p>
        <p className="text-sm mt-1">Run a demo scenario to generate incidents</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[#1e2d45]">
            <th className="text-left px-4 py-3 text-xs font-semibold text-[#4a5568] uppercase tracking-wider">Type</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-[#4a5568] uppercase tracking-wider">Application</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-[#4a5568] uppercase tracking-wider">Request</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-[#4a5568] uppercase tracking-wider">Severity</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-[#4a5568] uppercase tracking-wider">Decision</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-[#4a5568] uppercase tracking-wider">Status</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-[#4a5568] uppercase tracking-wider">Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1a2235]">
          {incidents.map((incident) => {
            const statusConfig = STATUS_CONFIG[incident.status] || STATUS_CONFIG.open;
            return (
              <tr
                key={incident.id}
                onClick={() => handleClick(incident.id)}
                className="hover:bg-[#111827] cursor-pointer transition-colors"
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{TYPE_ICONS[incident.incident_type] || '❓'}</span>
                    <span className="text-xs text-[#8b9bb4] capitalize">
                      {incident.incident_type?.replace('_', ' ')}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-[#8b9bb4] text-xs font-mono">{incident.application_name}</span>
                </td>
                <td className="px-4 py-3 max-w-xs">
                  <p className="text-[#e8edf5] text-xs truncate">{incident.request_text}</p>
                </td>
                <td className="px-4 py-3">
                  <RiskBadge level={incident.severity} />
                </td>
                <td className="px-4 py-3">
                  <DecisionBadge action={incident.action} size="sm" />
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex text-xs px-2 py-0.5 rounded-full ${statusConfig.classes}`}>
                    {statusConfig.label}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-[#4a5568] text-xs">
                    {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
