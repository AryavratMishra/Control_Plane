import React, { useEffect, useState } from 'react';
import { getIncidents } from '../services/api';
import { IncidentTable } from '../components/IncidentTable';

const FILTERS = [
  { label: 'All', value: '' },
  { label: 'Open', value: 'open' },
  { label: 'Under Review', value: 'under_review' },
  { label: 'Resolved', value: 'resolved' },
];

const TYPE_FILTERS = [
  { label: 'All Types', value: '' },
  { label: 'Hallucination', value: 'hallucination' },
  { label: 'PII Leakage', value: 'pii_leakage' },
  { label: 'Cost Anomaly', value: 'cost_anomaly' },
  { label: 'Escalation', value: 'escalation' },
];

export function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (typeFilter) params.incident_type = typeFilter;
      const data = await getIncidents(params);
      setIncidents(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [statusFilter, typeFilter]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#e8edf5]">Incidents</h1>
        <p className="text-sm text-[#8b9bb4] mt-1">All detected AI risk incidents with full forensic detail</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex gap-1 rounded-lg bg-[#0d1421] border border-[#1e2d45] p-1">
          {FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                statusFilter === f.value
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'text-[#8b9bb4] hover:text-[#e8edf5]'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="flex gap-1 rounded-lg bg-[#0d1421] border border-[#1e2d45] p-1">
          {TYPE_FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => setTypeFilter(f.value)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                typeFilter === f.value
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'text-[#8b9bb4] hover:text-[#e8edf5]'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <button
          onClick={load}
          className="ml-auto px-4 py-2 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-medium hover:bg-blue-500/20 transition-all"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Table */}
      <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <IncidentTable incidents={incidents} />
        )}
      </div>
    </div>
  );
}
