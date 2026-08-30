import React, { useState } from 'react';
import { clsx } from 'clsx';
import { evaluate } from '../services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface EvalResult {
  decision?: string;
  final_response?: string;
  risk?: {
    performance?: { score: number; level: string };
    cost?: { score: number; level: string };
    responsibility?: { score: number; level: string };
    overall?: { score: number; level: string };
  };
  reasons?: string[];
  incident_id?: string | null;
  pii_entities?: { type: string; text: string }[];
  request_text?: string;
  original_response?: string;
  repair_applied?: boolean;
  fast_screen_ms?: number;
  total_evaluation_ms?: number;
}

// ─── Style maps ───────────────────────────────────────────────────────────────

const DECISION_CONFIG: Record<string, {
  badge: string; glow: string; bg: string; icon: string; label: string; desc: string;
}> = {
  ALLOW: {
    badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50',
    glow:  'shadow-emerald-500/15',
    bg:    'from-emerald-500/10 to-transparent',
    icon:  '✓', label: 'ALLOW',
    desc:  'Response is safe to show the user',
  },
  BLOCK: {
    badge: 'bg-red-500/20 text-red-300 border-red-500/50',
    glow:  'shadow-red-500/15',
    bg:    'from-red-500/10 to-transparent',
    icon:  '✕', label: 'BLOCK',
    desc:  'Response blocked — too risky to deliver',
  },
  REPAIR: {
    badge: 'bg-amber-500/20 text-amber-300 border-amber-500/50',
    glow:  'shadow-amber-500/15',
    bg:    'from-amber-500/10 to-transparent',
    icon:  '⚡', label: 'REPAIR',
    desc:  'Response was modified before delivery',
  },
  ESCALATE: {
    badge: 'bg-orange-500/20 text-orange-300 border-orange-500/50',
    glow:  'shadow-orange-500/15',
    bg:    'from-orange-500/10 to-transparent',
    icon:  '↑', label: 'ESCALATE',
    desc:  'Needs human review before responding',
  },
};

const LEVEL_COLOR: Record<string, string> = {
  LOW:      'text-emerald-400',
  MEDIUM:   'text-amber-400',
  HIGH:     'text-red-400',
  CRITICAL: 'text-red-300',
};

const BAR_GRADIENT: Record<string, string> = {
  LOW:      'from-emerald-500 to-emerald-400',
  MEDIUM:   'from-amber-500 to-amber-400',
  HIGH:     'from-red-500 to-red-400',
  CRITICAL: 'from-red-700 to-red-500',
};

// ─── Shared input style ───────────────────────────────────────────────────────

const inputCls = [
  'w-full rounded-lg border border-[#1e2d45] bg-[#060a11] text-[#c8d5e8]',
  'text-sm px-3 py-2.5 outline-none transition-all duration-200',
  'focus:border-violet-500/60 focus:ring-1 focus:ring-violet-500/20',
  'placeholder:text-[#2d3748]',
  '[&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent',
  '[&::-webkit-scrollbar-thumb]:bg-[#1e2d45] [&::-webkit-scrollbar-thumb]:rounded-full',
].join(' ');

const labelCls = 'block text-[10px] font-bold text-[#8b9bb4] uppercase tracking-wider mb-1.5';

// ─── Risk bar sub-component ────────────────────────────────────────────────────

function RiskBar({
  label, icon, score, level,
}: { label: string; icon: string; score: number; level: string }) {
  const pct = Math.round(score * 100);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-sm">{icon}</span>
          <span className="text-[11px] font-semibold text-[#8b9bb4] uppercase tracking-wider">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={clsx('text-[10px] font-bold tracking-wider', LEVEL_COLOR[level] ?? 'text-gray-400')}>
            {level}
          </span>
          <span className="text-sm font-bold text-[#e8edf5] tabular-nums w-9 text-right">{pct}/100</span>
        </div>
      </div>
      <div className="h-2.5 rounded-full bg-[#111827] overflow-hidden">
        <div
          className={clsx(
            'h-full rounded-full bg-gradient-to-r transition-all duration-700 ease-out',
            BAR_GRADIENT[level] ?? 'from-gray-500 to-gray-400',
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Result card ──────────────────────────────────────────────────────────────

function ResultCard({ result }: { result: EvalResult }) {
  const decision = result.decision ?? 'UNKNOWN';
  const cfg = DECISION_CONFIG[decision] ?? {
    badge: 'bg-gray-500/20 text-gray-300 border-gray-500/50',
    glow: '',
    bg: 'from-gray-500/10 to-transparent',
    icon: '?',
    label: decision,
    desc: '',
  };
  const overallPct = Math.round((result.risk?.overall?.score ?? 0) * 100);
  const overallLevel = result.risk?.overall?.level ?? 'LOW';

  return (
    <div className={clsx('rounded-2xl border border-[#1e2d45] bg-[#080c14] overflow-hidden shadow-2xl', cfg.glow)}>

      {/* ── Decision hero ──────────────────────────────────────────────────── */}
      <div className={clsx('px-6 py-5 bg-gradient-to-br', cfg.bg)}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={clsx(
              'w-14 h-14 rounded-2xl border-2 flex items-center justify-center text-3xl font-bold shrink-0',
              cfg.badge,
            )}>
              {cfg.icon}
            </div>
            <div>
              <div className="text-[10px] font-bold text-[#4a5568] uppercase tracking-widest mb-0.5">
                ControlPlane Decision
              </div>
              <div className="text-2xl font-black text-[#e8edf5] tracking-tight">{cfg.label}</div>
              <div className="text-xs text-[#8b9bb4] mt-0.5">{cfg.desc}</div>
            </div>
          </div>

          <div className="text-right shrink-0">
            <div className="text-[10px] text-[#4a5568] uppercase tracking-wider mb-1">Overall Risk</div>
            <div className={clsx(
              'text-4xl font-black tabular-nums',
              LEVEL_COLOR[overallLevel] ?? 'text-gray-400',
            )}>
              {overallPct}
            </div>
            <div className="text-[10px] text-[#4a5568]">/100</div>
          </div>
        </div>

        {/* Overall risk bar */}
        <div className="mt-4">
          <div className="h-2 rounded-full bg-[#111827] overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full bg-gradient-to-r transition-all duration-700 ease-out',
                BAR_GRADIENT[overallLevel] ?? 'from-gray-500 to-gray-400',
              )}
              style={{ width: `${overallPct}%` }}
            />
          </div>
        </div>

        {result.incident_id && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-[10px] text-[#4a5568]">Incident:</span>
            <span className="px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/20 text-[9px] font-mono text-purple-400">
              {result.incident_id}
            </span>
          </div>
        )}
      </div>

      <div className="divide-y divide-[#1e2d45]">

        {/* ── Risk dimensions ────────────────────────────────────────────────── */}
        {result.risk && (
          <div className="px-6 py-4 space-y-3.5">
            <div className="text-[10px] font-bold text-[#4a5568] uppercase tracking-wider">Risk Dimensions</div>
            <RiskBar label="Performance" icon="🧠" score={result.risk.performance?.score ?? 0} level={result.risk.performance?.level ?? 'LOW'} />
            <RiskBar label="Responsibility" icon="🔒" score={result.risk.responsibility?.score ?? 0} level={result.risk.responsibility?.level ?? 'LOW'} />
            <RiskBar label="Cost" icon="💸" score={result.risk.cost?.score ?? 0} level={result.risk.cost?.level ?? 'LOW'} />
          </div>
        )}

        {/* ── Repaired / final response ──────────────────────────────────────── */}
        {result.final_response && (
          <div className="px-6 py-4">
            <div className={clsx(
              'flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider mb-2',
              result.repair_applied ? 'text-amber-400' : 'text-emerald-400',
            )}>
              <span>{result.repair_applied ? '⚡' : '✦'}</span>
              <span>{result.repair_applied ? 'Repaired Response (shown to user)' : 'Final Response'}</span>
            </div>
            <p className={clsx(
              'text-xs leading-relaxed whitespace-pre-wrap break-words p-3 rounded-lg border font-mono',
              result.repair_applied
                ? 'bg-amber-950/30 border-amber-500/20 text-amber-100'
                : 'bg-emerald-950/20 border-emerald-500/20 text-emerald-100',
            )}>
              {result.final_response}
            </p>
          </div>
        )}

        {/* ── Why this decision ──────────────────────────────────────────────── */}
        {result.reasons && result.reasons.length > 0 && (
          <div className="px-6 py-4">
            <div className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-2">📋 Why This Decision</div>
            <ul className="space-y-2">
              {result.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-[#8b9bb4] leading-relaxed">
                  <span className="text-[#4a5568] shrink-0 mt-0.5 font-bold">›</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ── PII detected ───────────────────────────────────────────────────── */}
        {result.pii_entities && result.pii_entities.length > 0 && (
          <div className="px-6 py-4">
            <div className="text-[10px] font-bold text-purple-400 uppercase tracking-wider mb-2">
              🔒 PII Detected ({result.pii_entities.length})
            </div>
            <div className="flex flex-wrap gap-2">
              {result.pii_entities.map((p, i) => (
                <span
                  key={i}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/25 text-[10px] font-mono"
                >
                  <span className="text-purple-400 font-semibold">{p.type}</span>
                  <span className="text-[#4a5568]">·</span>
                  <span className="text-purple-300">{p.text}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Timing footer ──────────────────────────────────────────────────── */}
        <div className="px-6 py-3 flex items-center gap-5 text-[10px] text-[#2d3748] bg-[#060a11]">
          <span>⏱ Fast screen: <span className="text-[#4a5568] font-mono">{result.fast_screen_ms ?? 0}ms</span></span>
          <span>Total eval: <span className="text-[#4a5568] font-mono">{result.total_evaluation_ms ?? 0}ms</span></span>
        </div>
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

interface CustomEvalPanelProps {
  onResult?: (result: EvalResult) => void;
}

const USE_CASES = [
  { value: 'customer_support', label: 'Customer Support' },
  { value: 'financial_advice', label: 'Financial Advice' },
  { value: 'healthcare',       label: 'Healthcare' },
  { value: 'hr_assistant',     label: 'HR Assistant' },
  { value: 'general',          label: 'General' },
];

const BUSINESS_IMPACTS = [
  { value: 'low',      label: 'Low' },
  { value: 'medium',   label: 'Medium' },
  { value: 'high',     label: 'High' },
  { value: 'critical', label: 'Critical' },
];

const COUNTRIES = [
  { value: 'IN', label: '🇮🇳 India' },
  { value: 'US', label: '🇺🇸 United States' },
  { value: 'EU', label: '🇪🇺 Europe' },
  { value: 'GB', label: '🇬🇧 United Kingdom' },
  { value: 'AU', label: '🇦🇺 Australia' },
];

const MODELS = [
  'gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo',
  'gemini-1.5-flash', 'gemini-1.5-pro',
  'claude-3-haiku', 'claude-3-sonnet',
];

export function CustomEvalPanel({ onResult }: CustomEvalPanelProps) {
  // Form state
  const [userPrompt,     setUserPrompt]     = useState('');
  const [aiResponse,     setAiResponse]     = useState('');
  const [useCase,        setUseCase]        = useState('customer_support');
  const [country,        setCountry]        = useState('IN');
  const [businessImpact, setBusinessImpact] = useState('high');
  const [model,          setModel]          = useState('gpt-4o-mini');
  const [showAdvanced,   setShowAdvanced]   = useState(false);
  // Telemetry state
  const [inputTokens,    setInputTokens]    = useState(100);
  const [outputTokens,   setOutputTokens]   = useState(80);
  const [llmCalls,       setLlmCalls]       = useState(1);
  const [toolCalls,      setToolCalls]      = useState(0);
  const [retries,        setRetries]        = useState(0);
  const [latencyMs,      setLatencyMs]      = useState(300);
  const [estimatedCost,  setEstimatedCost]  = useState(0.10);

  // Request state
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<EvalResult | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const canSubmit = userPrompt.trim().length > 0 && aiResponse.trim().length > 0;

  const handleClear = () => {
    setUserPrompt('');
    setAiResponse('');
    setResult(null);
    setApiError(null);
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setApiError(null);
    setResult(null);

    const payload = {
      application_id:  'dashboard-eval',
      conversation_id: `session-${Date.now()}`,
      request:  { text: userPrompt.trim() },
      response: { text: aiResponse.trim() },
      context: {
        country,
        use_case:        useCase,
        business_impact: businessImpact,
        trusted_data:    {},
      },
      telemetry: {
        model,
        input_tokens:   inputTokens,
        output_tokens:  outputTokens,
        llm_calls:      llmCalls,
        tool_calls:     toolCalls,
        retries:        retries,
        latency_ms:     latencyMs,
        estimated_cost: estimatedCost,
      },
    };

    try {
      const res = await evaluate(payload);
      const evalResult: EvalResult = res?.result ?? res;
      setResult(evalResult);
      onResult?.(evalResult);
    } catch (e: any) {
      setApiError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-[#1e2d45] bg-[#0d1421] overflow-hidden">

      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <div className="px-5 py-4 border-b border-[#1e2d45] bg-[#080c14] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-violet-500/15 border border-violet-500/30 flex items-center justify-center text-lg">
            🛡️
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#e8edf5]">Evaluate Any AI Interaction</h3>
            <p className="text-xs text-[#4a5568] mt-0.5">
              Paste a user prompt + AI response → get a full risk breakdown
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {(result || userPrompt || aiResponse) && (
            <button
              onClick={handleClear}
              className="px-3 py-1.5 rounded-lg border border-[#1e2d45] text-[11px] font-semibold text-[#8b9bb4] hover:border-[#2a3f5f] hover:text-[#e8edf5] transition-all duration-200"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 divide-y xl:divide-y-0 xl:divide-x divide-[#1e2d45]">

        {/* ── Left: form ─────────────────────────────────────────────────────── */}
        <div className="p-5 flex flex-col gap-5">

          {/* User prompt */}
          <div>
            <label className={labelCls} htmlFor="eval-user-prompt">
              👤 User Prompt
            </label>
            <textarea
              id="eval-user-prompt"
              value={userPrompt}
              onChange={e => setUserPrompt(e.target.value)}
              placeholder="What did the user ask? e.g. What&apos;s the status of my refund?"
              rows={4}
              className={clsx(inputCls, 'resize-none')}
            />
          </div>

          {/* AI response */}
          <div>
            <label className={labelCls} htmlFor="eval-ai-response">
              🤖 AI Response
            </label>
            <textarea
              id="eval-ai-response"
              value={aiResponse}
              onChange={e => setAiResponse(e.target.value)}
              placeholder="What did the AI reply? e.g. Your refund of ₹2,400 has been processed and will reflect in 2-3 days."
              rows={5}
              className={clsx(inputCls, 'resize-none')}
            />
          </div>

          {/* Context row */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className={labelCls} htmlFor="eval-use-case">Use Case</label>
              <select id="eval-use-case" value={useCase} onChange={e => setUseCase(e.target.value)} className={inputCls}>
                {USE_CASES.map(u => <option key={u.value} value={u.value}>{u.label}</option>)}
              </select>
            </div>
            <div>
              <label className={labelCls} htmlFor="eval-impact">Business Impact</label>
              <select id="eval-impact" value={businessImpact} onChange={e => setBusinessImpact(e.target.value)} className={inputCls}>
                {BUSINESS_IMPACTS.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
              </select>
            </div>
            <div>
              <label className={labelCls} htmlFor="eval-country">Country</label>
              <select id="eval-country" value={country} onChange={e => setCountry(e.target.value)} className={inputCls}>
                {COUNTRIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
          </div>

          {/* Advanced / Telemetry toggle */}
          <div>
            <button
              onClick={() => setShowAdvanced(v => !v)}
              className="text-[11px] text-[#4a5568] hover:text-[#8b9bb4] transition-colors flex items-center gap-1.5"
            >
              <span className={clsx('transition-transform duration-200 inline-block', showAdvanced && 'rotate-90')}>▶</span>
              Telemetry &amp; Model
            </button>
            {showAdvanced && (
              <div className="mt-4 rounded-xl border border-[#1e2d45] bg-[#080c14] p-4 space-y-4">
                <div className="text-[10px] font-bold text-[#8b9bb4] uppercase tracking-wider">📡 Telemetry</div>

                {/* Model */}
                <div>
                  <label className={labelCls} htmlFor="eval-model">Model</label>
                  <select id="eval-model" value={model} onChange={e => setModel(e.target.value)} className={inputCls}>
                    {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>

                {/* Token counts */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelCls} htmlFor="eval-input-tokens">Input Tokens</label>
                    <input
                      id="eval-input-tokens"
                      type="number" min={0}
                      value={inputTokens}
                      onChange={e => setInputTokens(Number(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div>
                    <label className={labelCls} htmlFor="eval-output-tokens">Output Tokens</label>
                    <input
                      id="eval-output-tokens"
                      type="number" min={0}
                      value={outputTokens}
                      onChange={e => setOutputTokens(Number(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                </div>

                {/* Call counts */}
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={labelCls} htmlFor="eval-llm-calls">LLM Calls</label>
                    <input
                      id="eval-llm-calls"
                      type="number" min={0}
                      value={llmCalls}
                      onChange={e => setLlmCalls(Number(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div>
                    <label className={labelCls} htmlFor="eval-tool-calls">Tool Calls</label>
                    <input
                      id="eval-tool-calls"
                      type="number" min={0}
                      value={toolCalls}
                      onChange={e => setToolCalls(Number(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div>
                    <label className={labelCls} htmlFor="eval-retries">Retries</label>
                    <input
                      id="eval-retries"
                      type="number" min={0}
                      value={retries}
                      onChange={e => setRetries(Number(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                </div>

                {/* Perf + cost */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelCls} htmlFor="eval-latency">Latency (ms)</label>
                    <input
                      id="eval-latency"
                      type="number" min={0}
                      value={latencyMs}
                      onChange={e => setLatencyMs(Number(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div>
                    <label className={labelCls} htmlFor="eval-cost">Est. Cost ($)</label>
                    <input
                      id="eval-cost"
                      type="number" min={0} step={0.001}
                      value={estimatedCost}
                      onChange={e => setEstimatedCost(Number(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                </div>

                {/* Live preview chips */}
                <div className="flex flex-wrap gap-1.5 pt-1 border-t border-[#1e2d45]">
                  {[
                    { k: 'model',           v: model },
                    { k: 'input_tokens',    v: inputTokens },
                    { k: 'output_tokens',   v: outputTokens },
                    { k: 'llm_calls',       v: llmCalls },
                    { k: 'tool_calls',      v: toolCalls },
                    { k: 'retries',         v: retries },
                    { k: 'latency_ms',      v: `${latencyMs}ms` },
                    { k: 'estimated_cost',  v: `$${estimatedCost}` },
                  ].map(({ k, v }) => (
                    <span key={k} className="px-2 py-0.5 rounded bg-[#111827] border border-[#1e2d45] text-[9px] font-mono text-[#4a5568]">
                      <span className="text-violet-400">{k}</span>: <span className="text-[#8b9bb4]">{String(v)}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Submit button */}
          <button
            id="eval-submit-btn"
            onClick={handleSubmit}
            disabled={loading || !canSubmit}
            className={clsx(
              'w-full py-3 rounded-xl text-sm font-bold tracking-wide transition-all duration-200 flex items-center justify-center gap-2.5',
              loading || !canSubmit
                ? 'bg-[#111827] border border-[#1e2d45] text-[#4a5568] cursor-not-allowed'
                : 'bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400 text-white shadow-lg shadow-violet-500/25 cursor-pointer hover:shadow-violet-500/40 hover:-translate-y-px',
            )}
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Evaluating response…
              </>
            ) : (
              <>
                <span>🛡️</span>
                Evaluate with ControlPlane
              </>
            )}
          </button>

          {!canSubmit && !loading && (
            <p className="text-[10px] text-center text-[#2d3748] -mt-3">
              Fill in both the user prompt and AI response to evaluate
            </p>
          )}
        </div>

        {/* ── Right: result ──────────────────────────────────────────────────── */}
        <div className="p-5 flex flex-col gap-4">
          <span className="text-[10px] font-bold text-[#8b9bb4] uppercase tracking-wider">
            Evaluation Result
          </span>

          {/* Error */}
          {apiError && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4">
              <p className="text-sm font-bold text-red-400 mb-1">Request Failed</p>
              <p className="text-xs text-red-300/80 font-mono break-all leading-relaxed">{apiError}</p>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex flex-col items-center justify-center flex-1 min-h-[340px] gap-4">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 rounded-full border-4 border-violet-500/20" />
                <div className="absolute inset-0 rounded-full border-4 border-violet-500 border-t-transparent animate-spin" />
                <div className="absolute inset-3 rounded-full border-2 border-violet-400/30 border-b-violet-400 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '0.8s' }} />
              </div>
              <div className="text-center">
                <p className="text-sm font-semibold text-[#e8edf5]">Evaluating…</p>
                <p className="text-xs text-[#4a5568] mt-1">Running risk analysis through the gateway</p>
              </div>
            </div>
          )}

          {/* Result card */}
          {result && !loading && <ResultCard result={result} />}

          {/* Empty state */}
          {!result && !loading && !apiError && (
            <div className="flex flex-col items-center justify-center flex-1 min-h-[340px] gap-4 text-center">
              <div className="w-20 h-20 rounded-3xl border border-[#1e2d45] bg-[#080c14] flex items-center justify-center text-4xl">
                🛡️
              </div>
              <div>
                <p className="text-sm font-semibold text-[#4a5568]">Ready to evaluate</p>
                <p className="text-xs text-[#2d3748] mt-1.5 max-w-[220px] leading-relaxed">
                  Enter a user prompt and AI response on the left, then hit Evaluate
                </p>
              </div>
              <div className="flex flex-col gap-2 mt-2 w-full max-w-[280px]">
                {['ALLOW — safe response passes through', 'REPAIR — response modified before delivery', 'BLOCK — response stopped', 'ESCALATE — human review required'].map((t, i) => (
                  <div key={i} className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-[#080c14] border border-[#1e2d45]">
                    <span className={clsx('w-2 h-2 rounded-full shrink-0', ['bg-emerald-400', 'bg-amber-400', 'bg-red-400', 'bg-orange-400'][i])} />
                    <span className="text-[10px] text-[#4a5568]">{t}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
