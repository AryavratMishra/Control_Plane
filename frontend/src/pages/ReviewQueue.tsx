import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getIncidents, reviewIncident } from '../services/api';
import { DecisionBadge, RiskBadge } from '../components/DecisionBadge';
import { formatDistanceToNow } from 'date-fns';

export function ReviewQueue() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState<string | null>(null);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const data = await getIncidents({ status: 'open' });
      setIncidents(data.filter((i: any) => i.action === 'ESCALATE'));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleReview = async (id: string, action: string) => {
    setReviewing(id);
    try {
      await reviewIncident(id, {
        action,
        comment: `Human reviewer: ${action}`,
        reviewer_name: 'Human Reviewer',
        was_correct: 'yes',
      });
      await load();
    } finally {
      setReviewing(null);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#e8edf5]">Review Queue</h1>
        <p className="text-sm text-[#8b9bb4] mt-1">
          Human review required for escalated incidents
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : incidents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-[#4a5568]">
          <span className="text-5xl mb-4">✓</span>
          <p className="text-lg font-semibold text-[#8b9bb4]">Queue is clear</p>
          <p className="text-sm mt-1">No incidents pending human review</p>
        </div>
      ) : (
        <div className="space-y-4">
          {incidents.map(incident => (
            <div
              key={incident.id}
              className="rounded-xl border border-orange-500/20 bg-[#0d1421] p-5 hover:border-orange-500/40 transition-all"
            >
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap mb-2">
                    <DecisionBadge action="ESCALATE" size="sm" animated />
                    <RiskBadge level={incident.severity} />
                    <span className="text-xs text-[#4a5568]">
                      {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-[#e8edf5] mb-1">{incident.request_text}</p>
                  <p className="text-xs text-[#8b9bb4]">{incident.reason}</p>
                  <p className="text-xs text-[#4a5568] mt-1">App: {incident.application_name}</p>
                </div>

                <div className="flex flex-col gap-2 shrink-0">
                  <button
                    onClick={() => navigate(`/incidents/${incident.id}`)}
                    className="px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1e2d45] text-[#8b9bb4] text-xs font-medium hover:text-[#e8edf5] transition-all"
                  >
                    View Details →
                  </button>
                  <button
                    onClick={() => handleReview(incident.id, 'approve')}
                    disabled={reviewing === incident.id}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium hover:bg-emerald-500/20 transition-all disabled:opacity-50"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => handleReview(incident.id, 'reject')}
                    disabled={reviewing === incident.id}
                    className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium hover:bg-red-500/20 transition-all disabled:opacity-50"
                  >
                    ✕ Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
