import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getIncident, reviewIncident } from '../services/api';
import { DecisionBadge, RiskBadge } from '../components/DecisionBadge';
import { RiskScoreCard } from '../components/RiskScoreCard';
import { clsx } from 'clsx';

export function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [incident, setIncident] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const [comment, setComment] = useState('');
  const [reviewDone, setReviewDone] = useState(false);

  useEffect(() => {
    if (!id) return;
    getIncident(id).then(setIncident).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  const handleReview = async (action: string) => {
    if (!id) return;
    setReviewing(true);
    try {
      await reviewIncident(id, {
        action,
        comment,
        reviewer_name: 'Human Reviewer',
        was_correct: action === 'approve' ? 'yes' : 'false_positive',
      });
      setReviewDone(true);
      // Reload incident
      const updated = await getIncident(id);
      setIncident(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setReviewing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="flex items-center justify-center h-full text-[#8b9bb4]">
        Incident not found
      </div>
    );
  }

  const ra = incident.risk_assessment;
  const evidence = incident.evidence || {};
  const pii = evidence.pii_entities || [];
  const evidenceChunks = evidence.evidence_chunks || [];
  const reasons = evidence.reasons || [incident.reason];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="text-[#8b9bb4] hover:text-[#e8edf5] text-sm transition-colors"
        >
          ← Back
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-bold text-[#e8edf5]">Incident</h1>
            <span className="font-mono text-xs text-[#4a5568]">#{incident.id?.slice(0, 8)}</span>
            <DecisionBadge action={incident.action} size="md" animated />
            <RiskBadge level={incident.severity} />
            <span className={clsx(
              'text-xs px-2 py-0.5 rounded-full border',
              incident.status === 'open'
                ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                : 'bg-[#1a2235] text-[#8b9bb4] border-[#1e2d45]',
            )}>
              {incident.status}
            </span>
          </div>
          <p className="text-sm text-[#8b9bb4] mt-1">{incident.application_name} · {incident.incident_type?.replace('_', ' ')}</p>
        </div>
      </div>

      {/* Risk Score Cards */}
      {ra && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <RiskScoreCard
            label="Performance"
            score={ra.performance_score || 0}
            level={incident.severity || 'LOW'}
            reasons={reasons.filter((r: string) => r.toLowerCase().includes('contradiction') || r.toLowerCase().includes('ground'))}
            icon="🧠"
          />
          <RiskScoreCard
            label="Cost"
            score={ra.cost_score || 0}
            level={ra.cost_score >= 0.5 ? 'HIGH' : ra.cost_score >= 0.25 ? 'MEDIUM' : 'LOW'}
            reasons={reasons.filter((r: string) => r.toLowerCase().includes('cost') || r.toLowerCase().includes('tool'))}
            icon="💸"
          />
          <RiskScoreCard
            label="Responsibility"
            score={ra.responsibility_score || 0}
            level={ra.responsibility_score >= 0.75 ? 'CRITICAL' : ra.responsibility_score >= 0.5 ? 'HIGH' : ra.responsibility_score >= 0.25 ? 'MEDIUM' : 'LOW'}
            reasons={reasons.filter((r: string) => r.toLowerCase().includes('pii') || r.toLowerCase().includes('policy'))}
            icon="🔒"
          />
        </div>
      )}

      {/* Latency info */}
      {ra && (
        <div className="flex gap-4 text-xs text-[#4a5568]">
          <span>Fast screen: <span className="text-blue-400 font-mono">{ra.fast_screen_ms}ms</span></span>
          <span>Total evaluation: <span className="text-blue-400 font-mono">{ra.total_evaluation_ms}ms</span></span>
        </div>
      )}

      {/* 4-Column Forensic View */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* User Request */}
        <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <h3 className="text-xs font-semibold text-[#8b9bb4] uppercase tracking-wider mb-3">User Request</h3>
          <p className="text-sm text-[#e8edf5] leading-relaxed">{incident.request_text}</p>
        </div>

        {/* AI Response */}
        <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <h3 className="text-xs font-semibold text-[#8b9bb4] uppercase tracking-wider mb-3 flex items-center gap-2">
            Original AI Response
            {incident.action !== 'ALLOW' && (
              <span className="text-red-400 text-xs">⚠ Not Delivered</span>
            )}
          </h3>
          <p className="text-sm text-[#e8edf5] leading-relaxed">{incident.response_text}</p>
        </div>

        {/* Evidence & Findings */}
        <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <h3 className="text-xs font-semibold text-[#8b9bb4] uppercase tracking-wider mb-3">Evidence & Findings</h3>

          {reasons.length > 0 && (
            <div className="mb-4 space-y-2">
              <p className="text-xs text-[#4a5568] font-semibold">Reasons:</p>
              {reasons.map((r: string, i: number) => (
                <div key={i} className="flex items-start gap-2 text-xs text-[#e8edf5]">
                  <span className="text-red-400 mt-0.5 shrink-0">›</span>
                  {r}
                </div>
              ))}
            </div>
          )}

          {pii.length > 0 && (
            <div className="mb-4">
              <p className="text-xs text-[#4a5568] font-semibold mb-2">PII Detected:</p>
              <div className="flex flex-wrap gap-2">
                {pii.map((entity: any, i: number) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded bg-red-500/10 border border-red-500/20 text-red-400">
                    {entity.type}
                  </span>
                ))}
              </div>
            </div>
          )}

          {evidenceChunks.length > 0 && (
            <div>
              <p className="text-xs text-[#4a5568] font-semibold mb-2">Evidence Sources:</p>
              {evidenceChunks.slice(0, 2).map((chunk: any, i: number) => (
                <div key={i} className="text-xs text-[#8b9bb4] bg-[#111827] rounded p-2 mb-2">
                  <span className="text-blue-400 font-semibold">[{chunk.source}]</span>{' '}
                  {chunk.content?.slice(0, 150)}...
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Decision */}
        <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <h3 className="text-xs font-semibold text-[#8b9bb4] uppercase tracking-wider mb-3">ControlPlane Decision</h3>

          <div className="flex items-center gap-3 mb-4">
            <DecisionBadge action={incident.action} size="lg" animated />
          </div>

          {incident.repaired_response_text && (
            <div className="mt-3 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
              <p className="text-xs text-emerald-400 font-semibold mb-2">✓ Repaired Response (Delivered):</p>
              <p className="text-xs text-[#e8edf5] leading-relaxed">{incident.repaired_response_text}</p>
            </div>
          )}
        </div>
      </div>

      {/* Human Review Panel */}
      {incident.action === 'ESCALATE' && incident.status === 'open' && !reviewDone && (
        <div className="rounded-xl border border-orange-500/30 bg-orange-500/5 p-5">
          <h3 className="text-sm font-semibold text-orange-400 mb-2">Human Review Required</h3>
          <p className="text-xs text-[#8b9bb4] mb-4">
            This incident requires human review. Examine the evidence above and take action.
          </p>
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Add review comment..."
            rows={2}
            className="w-full rounded-lg bg-[#111827] border border-[#1e2d45] text-sm text-[#e8edf5] p-3 mb-4 focus:outline-none focus:border-blue-500/50"
          />
          <div className="flex gap-3">
            <button
              onClick={() => handleReview('approve')}
              disabled={reviewing}
              className="px-4 py-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-sm font-medium hover:bg-emerald-500/25 transition-all disabled:opacity-50"
            >
              {reviewing ? 'Processing...' : '✓ Approve & Allow'}
            </button>
            <button
              onClick={() => handleReview('reject')}
              disabled={reviewing}
              className="px-4 py-2 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-sm font-medium hover:bg-red-500/25 transition-all disabled:opacity-50"
            >
              ✕ Reject & Block
            </button>
            <button
              onClick={() => handleReview('override')}
              disabled={reviewing}
              className="px-4 py-2 rounded-lg bg-[#111827] border border-[#1e2d45] text-[#8b9bb4] text-sm font-medium hover:text-[#e8edf5] transition-all disabled:opacity-50"
            >
              ⚡ Override & Repair
            </button>
          </div>
        </div>
      )}

      {/* Review History */}
      {incident.human_reviews?.length > 0 && (
        <div className="rounded-xl border bg-[#0d1421] border-[#1e2d45] p-5">
          <h3 className="text-xs font-semibold text-[#8b9bb4] uppercase tracking-wider mb-3">Review History</h3>
          {incident.human_reviews.map((r: any, i: number) => (
            <div key={i} className="flex items-start gap-3 text-sm">
              <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-xs text-blue-400 shrink-0 mt-0.5">
                {r.reviewer_name?.[0] || 'R'}
              </div>
              <div>
                <span className="text-[#e8edf5] font-medium">{r.reviewer_name}</span>
                <span className="text-[#4a5568] mx-2">·</span>
                <span className="text-xs font-bold uppercase">{r.action}</span>
                {r.comment && <p className="text-xs text-[#8b9bb4] mt-1">{r.comment}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
