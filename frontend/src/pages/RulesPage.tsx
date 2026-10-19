import React, { useState, useEffect } from 'react';
import {
  Plus,
  RefreshCw,
  Power,
  Trash2,
  AlertCircle,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { DetectionRule, RuleType, ServiceItem } from '../types';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { useAuth } from '../context/AuthContext';

export const RulesPage: React.FC = () => {
  const { hasRole } = useAuth();
  const isAdmin = hasRole(['super_admin']);

  const [rules, setRules] = useState<DetectionRule[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [ruleType, setRuleType] = useState<RuleType>('error_threshold');
  const [severity, setSeverity] = useState('HIGH');
  const [threshold, setThreshold] = useState('5');
  const [timeWindowSeconds, setTimeWindowSeconds] = useState('300');
  const [cooldownSeconds, setCooldownSeconds] = useState('600');
  const [errorSignaturePattern, setErrorSignaturePattern] = useState('');
  const [selectedServiceId, setSelectedServiceId] = useState('');

  const fetchRules = async () => {
    setLoading(true);
    try {
      const data = await api.get<DetectionRule[]>('/rules');
      setRules(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchServices = async () => {
    try {
      const data = await api.get<ServiceItem[]>('/services');
      setServices(data);
    } catch (err) {
      console.error('Failed to load services for rules:', err);
    }
  };

  useEffect(() => {
    fetchRules();
    fetchServices();
  }, []);

  const handleToggleRule = async (rule: DetectionRule) => {
    if (!isAdmin) return;
    try {
      await api.patch(`/rules/${rule.id}`, { is_enabled: !rule.is_enabled });
      setRules((prev) =>
        prev.map((r) => (r.id === rule.id ? { ...r, is_enabled: !r.is_enabled } : r))
      );
    } catch (err: any) {
      alert(err?.message || 'Failed to update rule');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!isAdmin || !confirm('Are you sure you want to delete or disable this detection rule?')) return;
    try {
      await api.delete(`/rules/${ruleId}`);
      await fetchRules();
    } catch (err: any) {
      alert(err?.message || 'Failed to delete rule');
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await api.post('/rules', {
        name: name.trim(),
        description: description.trim() || undefined,
        rule_type: ruleType,
        severity,
        threshold: parseFloat(threshold),
        time_window_seconds: parseInt(timeWindowSeconds, 10),
        cooldown_seconds: parseInt(cooldownSeconds, 10),
        error_signature_pattern: errorSignaturePattern.trim() || undefined,
        service_id: selectedServiceId || undefined,
        is_enabled: true,
      });

      setIsModalOpen(false);
      setName('');
      setDescription('');
      setErrorSignaturePattern('');
      await fetchRules();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create detection rule');
    }
  };

  const formatRuleType = (type: string) => {
    return type.replace('_', ' ').toUpperCase();
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Detection Rules Engine</h1>
          <p className="text-xs text-slate-400">
            Real-time automated incident detection policies and anomaly triggers
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchRules}
            className="flex items-center space-x-2 px-3 py-1.5 bg-navy-900 hover:bg-slate-800 border border-charcoal-700 rounded-lg text-xs font-medium text-slate-200 transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          {isAdmin && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center space-x-2 px-3.5 py-1.5 bg-brand-600 hover:bg-brand-500 rounded-lg text-xs font-medium text-white transition shadow-sm cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Create Rule</span>
            </button>
          )}
        </div>
      </div>

      {/* Rules Grid */}
      {loading ? (
        <LoadingSkeleton rows={4} height="h-28" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className={`bg-navy-900 border rounded-2xl p-5 shadow-sm transition flex flex-col justify-between ${
                rule.is_enabled ? 'border-charcoal-700' : 'border-slate-800/60 opacity-60'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 uppercase tracking-wider">
                      {formatRuleType(rule.rule_type)}
                    </span>
                    <SeverityBadge severity={rule.severity} size="sm" />
                  </div>
                  {isAdmin && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleToggleRule(rule)}
                        className={`p-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                          rule.is_enabled
                            ? 'text-emerald-400 bg-emerald-950/40 hover:bg-emerald-900/60'
                            : 'text-slate-500 bg-slate-800/40 hover:bg-slate-800'
                        }`}
                        title={rule.is_enabled ? 'Disable Rule' : 'Enable Rule'}
                      >
                        <Power className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteRule(rule.id)}
                        className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-950/40 rounded-lg transition cursor-pointer"
                        title="Delete/Disable Rule"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>

                <h3 className="text-base font-bold text-white mb-1">{rule.name}</h3>
                <p className="text-xs text-slate-400 mb-4 leading-relaxed">{rule.description || 'No description provided.'}</p>
              </div>

              {/* Parameters & Scope */}
              <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-[11px] text-slate-400 gap-2">
                <div className="flex items-center space-x-3">
                  <span>
                    Threshold: <strong className="text-slate-200">{rule.threshold}</strong>
                  </span>
                  <span>
                    Window: <strong className="text-slate-200">{rule.time_window_seconds}s</strong>
                  </span>
                  <span>
                    Cooldown: <strong className="text-slate-200">{rule.cooldown_seconds}s</strong>
                  </span>
                </div>
                {rule.error_signature_pattern && (
                  <span className="font-mono text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
                    pattern: "{rule.error_signature_pattern}"
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Rule Modal Dialog */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-navy-900 border border-charcoal-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Create Incident Detection Rule</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-red-950 border border-red-800 rounded-xl text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateRule} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Critical Gateway Outage Alert"
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Explains when and why this rule triggers an incident..."
                  rows={2}
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Rule Type</label>
                  <select
                    value={ruleType}
                    onChange={(e) => setRuleType(e.target.value as RuleType)}
                    className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                  >
                    <option value="error_threshold">Error Threshold</option>
                    <option value="critical_log">Critical Log</option>
                    <option value="repeated_failure">Repeated Failure</option>
                    <option value="error_rate">Service Error Rate</option>
                    <option value="service_inactivity">Service Inactivity</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Incident Severity</label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Threshold</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Window (sec)</label>
                  <input
                    type="number"
                    required
                    value={timeWindowSeconds}
                    onChange={(e) => setTimeWindowSeconds(e.target.value)}
                    className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Cooldown (sec)</label>
                  <input
                    type="number"
                    required
                    value={cooldownSeconds}
                    onChange={(e) => setCooldownSeconds(e.target.value)}
                    className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              {ruleType === 'repeated_failure' && (
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Error Signature Pattern (substring match)
                  </label>
                  <input
                    type="text"
                    value={errorSignaturePattern}
                    onChange={(e) => setErrorSignaturePattern(e.target.value)}
                    placeholder="e.g. connection pool exhausted"
                    className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500 font-mono"
                  />
                </div>
              )}

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Service Scope (Optional)
                </label>
                <select
                  value={selectedServiceId}
                  onChange={(e) => setSelectedServiceId(e.target.value)}
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                >
                  <option value="">Global (Applies across all services)</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.environment})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-medium cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-medium cursor-pointer"
                >
                  Save Detection Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
