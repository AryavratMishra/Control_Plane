import React, { useEffect, useState } from 'react';
import { getPolicies } from '../services/api';

export function Policies() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    getPolicies().then(setPolicies).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#e8edf5]">Policies</h1>
        <p className="text-sm text-[#8b9bb4] mt-1">
          Configurable governance rules by use case and geography
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-4">
          {policies.map(policy => (
            <div
              key={policy.id}
              className="rounded-xl border bg-[#0d1421] border-[#1e2d45] overflow-hidden"
            >
              <button
                onClick={() => setExpanded(expanded === policy.id ? null : policy.id)}
                className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-[#111827] transition-colors"
              >
                <div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-[#e8edf5]">{policy.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {policy.use_case}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-[#1a2235] text-[#8b9bb4] border border-[#1e2d45]">
                      {policy.geography}
                    </span>
                  </div>
                  <p className="text-xs text-[#4a5568] mt-1">{policy.description}</p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-[#4a5568]">{policy.versions?.length || 0} version(s)</span>
                  <span className={`transition-transform duration-200 text-[#8b9bb4] ${expanded === policy.id ? 'rotate-180' : ''}`}>▾</span>
                </div>
              </button>

              {expanded === policy.id && policy.versions?.length > 0 && (
                <div className="border-t border-[#1e2d45] p-5">
                  {policy.versions.map((v: any) => (
                    <div key={v.version} className="mb-4">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-xs font-semibold text-blue-400">Version {v.version}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full border ${
                          v.status === 'active'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-[#1a2235] text-[#8b9bb4] border-[#1e2d45]'
                        }`}>
                          {v.status}
                        </span>
                        <span className="text-xs text-[#4a5568]">Since: {new Date(v.effective_from).toLocaleDateString()}</span>
                      </div>

                      {v.config?.rules && (
                        <div>
                          <p className="text-xs text-[#4a5568] font-semibold uppercase tracking-wider mb-2">Rules</p>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {Object.entries(v.config.rules).map(([rule, action]) => (
                              <div key={rule} className="flex items-center justify-between rounded-lg bg-[#111827] border border-[#1a2235] px-3 py-2">
                                <span className="text-xs text-[#8b9bb4] truncate mr-2">{rule.replace(/_/g, ' ')}</span>
                                <span className={`text-xs font-bold shrink-0 ${
                                  action === 'block' ? 'text-red-400' :
                                  action === 'escalate' ? 'text-orange-400' :
                                  action === 'repair' ? 'text-amber-400' :
                                  'text-emerald-400'
                                }`}>
                                  {String(action).toUpperCase()}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
