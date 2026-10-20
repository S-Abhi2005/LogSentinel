import React, { useState, useEffect } from 'react';
import {
  Server,
  Plus,
  Key,
  X,
  AlertCircle,
  RefreshCw,
  Check,
} from 'lucide-react';
import { api } from '../api/client';
import { ServiceItem, IngestionKey } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { useAuth } from '../context/AuthContext';

export const ServicesPage: React.FC = () => {
  const { hasRole } = useAuth();
  const isAdmin = hasRole(['super_admin']);
  const canCreate = hasRole(['super_admin', 'engineer']);

  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Register Modal
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [name, setName] = useState('');
  const [environment, setEnvironment] = useState('production');
  const [description, setDescription] = useState('');
  const [ownerTeam, setOwnerTeam] = useState('');
  const [regError, setRegError] = useState<string | null>(null);

  // Ingestion Key Modal
  const [selectedService, setSelectedService] = useState<ServiceItem | null>(null);
  const [keys, setKeys] = useState<IngestionKey[]>([]);
  const [keyName, setKeyName] = useState('');
  const [oneTimeRawKey, setOneTimeRawKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [keyError, setKeyError] = useState<string | null>(null);

  const fetchServices = async () => {
    setLoading(true);
    try {
      const data = await api.get<ServiceItem[]>('/services');
      setServices(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
  }, []);

  const handleRegisterService = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError(null);
    try {
      await api.post('/services', {
        name: name.trim(),
        environment,
        description: description.trim() || undefined,
        owner_team: ownerTeam.trim(),
      });
      setIsRegisterOpen(false);
      setName('');
      setDescription('');
      setOwnerTeam('');
      await fetchServices();
    } catch (err: any) {
      setRegError(err?.message || 'Failed to register service');
    }
  };

  const openKeyManager = async (svc: ServiceItem) => {
    setSelectedService(svc);
    setOneTimeRawKey(null);
    setKeyName('');
    setKeyError(null);
    try {
      const kList = await api.get<IngestionKey[]>(`/services/${svc.id}/keys`);
      setKeys(kList);
    } catch (err) {
      console.error('Failed to load keys for service:', err);
    }
  };

  const handleIssueKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedService || !keyName.trim()) return;
    setKeyError(null);
    try {
      const data = await api.post<{ id: string; raw_key: string }>(
        `/services/${selectedService.id}/keys`,
        { key_name: keyName.trim() }
      );
      setOneTimeRawKey(data.raw_key);
      setKeyName('');
      const kList = await api.get<IngestionKey[]>(`/services/${selectedService.id}/keys`);
      setKeys(kList);
    } catch (err: any) {
      setKeyError(err?.message || 'Failed to issue key');
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!selectedService || !confirm('Are you sure you want to revoke this ingestion key?')) return;
    try {
      await api.post(`/services/${selectedService.id}/keys/${keyId}/revoke`);
      const kList = await api.get<IngestionKey[]>(`/services/${selectedService.id}/keys`);
      setKeys(kList);
    } catch (err: any) {
      alert(err?.message || 'Failed to revoke key');
    }
  };

  const copyKeyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Service Registry & Telemetry Keys</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Registered microservices, ingestion credentials, and live health evaluation
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchServices}
            className="flex items-center space-x-2 px-3 py-1.5 bg-white dark:bg-navy-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-charcoal-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 transition cursor-pointer shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          {canCreate && (
            <button
              onClick={() => setIsRegisterOpen(true)}
              className="flex items-center space-x-2 px-3.5 py-1.5 bg-brand-600 hover:bg-brand-500 rounded-lg text-xs font-semibold text-white transition shadow-sm cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Register Service</span>
            </button>
          )}
        </div>
      </div>

      {/* Services Grid */}
      {loading ? (
        <LoadingSkeleton rows={4} height="h-32" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {services.map((svc) => (
            <div
              key={svc.id}
              className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-colors duration-150"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-brand-600 dark:text-brand-400">
                      <Server className="w-4 h-4" />
                    </span>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">{svc.name}</h3>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono capitalize">
                        {svc.environment} • {svc.owner_team}
                      </span>
                    </div>
                  </div>
                  <StatusBadge status={svc.health_status} type="health" />
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 mb-4 leading-relaxed">
                  {svc.description || 'No description recorded.'}
                </p>

                <div className="grid grid-cols-2 gap-2 bg-slate-50 dark:bg-navy-950 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs mb-4">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[10px]">Active Incidents</span>
                    <span className="font-bold text-slate-800 dark:text-white text-sm">{svc.active_incidents_count}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[10px]">Errors (1h)</span>
                    <span className="font-bold text-rose-500 dark:text-rose-400 text-sm">{svc.recent_error_count}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                <span className="text-[11px] text-slate-500 dark:text-slate-400">
                  {svc.last_log_at
                    ? `Last log ${new Date(svc.last_log_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                    : 'No telemetry yet'}
                </span>
                {isAdmin && (
                  <button
                    onClick={() => openKeyManager(svc)}
                    className="flex items-center space-x-1.5 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-semibold transition cursor-pointer"
                  >
                    <Key className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                    <span>Manage Keys</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Register Service Modal */}
      {isRegisterOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Server className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Register New Microservice</h3>
              </div>
              <button onClick={() => setIsRegisterOpen(false)} className="text-slate-400 hover:text-slate-700 dark:hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {regError && (
              <div className="p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 dark:text-red-400 shrink-0" />
                <span>{regError}</span>
              </div>
            )}

            <form onSubmit={handleRegisterService} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Service Identifier / Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. recommendation-engine"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 font-mono focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Environment</label>
                <select
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                >
                  <option value="production">production</option>
                  <option value="staging">staging</option>
                  <option value="testing">testing</option>
                  <option value="development">development</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Owner Team</label>
                <input
                  type="text"
                  required
                  value={ownerTeam}
                  onChange={(e) => setOwnerTeam(e.target.value)}
                  placeholder="e.g. AI Platforms Squad"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Service role in distributed architecture..."
                  rows={2}
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsRegisterOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium cursor-pointer transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-semibold cursor-pointer transition shadow-sm"
                >
                  Register Service
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Ingestion Key Manager Dialog */}
      {selectedService && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/65 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Key className="w-4 h-4 text-amber-500 dark:text-amber-400" />
                  <span>Ingestion Keys: {selectedService.name}</span>
                </h3>
                <span className="text-xs text-slate-500 dark:text-slate-400">Environment: {selectedService.environment}</span>
              </div>
              <button onClick={() => setSelectedService(null)} className="text-slate-400 hover:text-slate-700 dark:hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* One-Time Raw Key Banner */}
            {oneTimeRawKey && (
              <div className="p-4 bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-700 rounded-xl text-xs space-y-2">
                <div className="font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span>Key Generated Successfully! Copy it now:</span>
                </div>
                <div className="p-2 bg-white dark:bg-navy-950 rounded border border-emerald-200 dark:border-emerald-800/80 font-mono text-slate-900 dark:text-slate-100 flex items-center justify-between break-all">
                  <span>{oneTimeRawKey}</span>
                  <button
                    onClick={() => copyKeyToClipboard(oneTimeRawKey)}
                    className="ml-2 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-sans shrink-0 transition font-medium"
                  >
                    {copiedKey ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <p className="text-[11px] text-emerald-700 dark:text-emerald-400">
                  ⚠️ This raw secret will NOT be shown again. It is stored as a one-way hash.
                </p>
              </div>
            )}

            {keyError && (
              <div className="p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300 text-xs">
                {keyError}
              </div>
            )}

            {/* Issue New Key Form */}
            <form onSubmit={handleIssueKey} className="flex gap-2">
              <input
                type="text"
                required
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                placeholder="Key label (e.g. k8s-daemonset-key)..."
                className="flex-1 bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold shrink-0 transition cursor-pointer"
              >
                Issue Key
              </button>
            </form>

            {/* Active Keys List */}
            <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 block mb-2">Existing Keys</span>
              {keys.length === 0 ? (
                <div className="text-xs text-slate-400 italic">No keys issued for this service.</div>
              ) : (
                keys.map((k) => (
                  <div
                    key={k.id}
                    className="p-3 bg-slate-50 dark:bg-navy-950 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-slate-800 dark:text-slate-200">{k.key_name}</div>
                      <div className="font-mono text-[11px] text-slate-500 dark:text-slate-400">
                        Prefix: <span className="text-brand-600 dark:text-brand-400">{k.key_prefix}...</span> •{' '}
                        {k.is_revoked ? (
                          <span className="text-red-500 dark:text-red-400 font-semibold">REVOKED</span>
                        ) : (
                          <span className="text-emerald-600 dark:text-emerald-400 font-semibold">ACTIVE</span>
                        )}
                      </div>
                    </div>
                    {!k.is_revoked && (
                      <button
                        onClick={() => handleRevokeKey(k.id)}
                        className="px-2.5 py-1 text-red-600 dark:text-red-400 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/40 rounded transition text-[11px] font-medium"
                      >
                        Revoke
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
