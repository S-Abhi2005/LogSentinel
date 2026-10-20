import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  Play,
  RotateCcw,
  MessageSquare,
  Clock,
  Terminal,
  Send,
  AlertCircle,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { IncidentDetail, Assignee } from '../types';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { useAuth } from '../context/AuthContext';

export const IncidentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();

  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [assignees, setAssignees] = useState<Assignee[]>([]);
  const [assigneesLoading, setAssigneesLoading] = useState<boolean>(false);
  const [assigneesError, setAssigneesError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [commentText, setCommentText] = useState<string>('');
  const [submittingComment, setSubmittingComment] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Resolution Modal State
  const [isResolveModalOpen, setIsResolveModalOpen] = useState<boolean>(false);
  const [resolveReason, setResolveReason] = useState<string>('');
  const [isResolving, setIsResolving] = useState<boolean>(false);

  const canModify = hasRole(['super_admin', 'engineer']);

  const fetchAssignees = useCallback(async () => {
    if (!canModify) return;
    setAssigneesLoading(true);
    setAssigneesError(null);
    try {
      const data = await api.get<Assignee[]>('/auth/assignees');
      setAssignees(data || []);
    } catch (err: any) {
      if (err?.status === 403) {
        setAssigneesError('Forbidden: Only engineers and admins can view assignees.');
      } else {
        setAssigneesError(err?.message || 'Failed to load assignees');
      }
    } finally {
      setAssigneesLoading(false);
    }
  }, [canModify]);

  const fetchIncidentDetails = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await api.get<IncidentDetail>(`/incidents/${id}`);
      setIncident(data);
    } catch (err: any) {
      setActionError(err?.message || 'Failed to load incident');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchIncidentDetails();
    if (canModify) {
      fetchAssignees();
    }
  }, [fetchIncidentDetails, fetchAssignees, canModify]);

  const handleStatusTransition = async (action: 'acknowledge' | 'investigate' | 'resolve' | 'reopen', reason?: string) => {
    if (!id) return;
    setActionError(null);
    try {
      let endpoint = `/incidents/${id}/${action}`;
      if (action === 'resolve' && reason) {
        endpoint += `?reason=${encodeURIComponent(reason)}`;
      }
      await api.post(endpoint);
      await fetchIncidentDetails();
    } catch (err: any) {
      setActionError(err?.message || `Failed to ${action} incident`);
    }
  };

  const handleConfirmResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsResolving(true);
    try {
      await handleStatusTransition('resolve', resolveReason.trim() || 'Issue mitigated');
      setIsResolveModalOpen(false);
      setResolveReason('');
    } finally {
      setIsResolving(false);
    }
  };

  const handleAssignUser = async (targetUserId: string) => {
    if (!id) return;
    setActionError(null);
    try {
      await api.post(`/incidents/${id}/assign`, {
        assigned_user_id: targetUserId === '' ? null : targetUserId,
      });
      await fetchIncidentDetails();
    } catch (err: any) {
      setActionError(err?.message || 'Failed to assign user');
    }
  };

  const handlePostComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !commentText.trim()) return;
    setSubmittingComment(true);
    setActionError(null);
    try {
      await api.post(`/incidents/${id}/comments`, { comment: commentText.trim() });
      setCommentText('');
      await fetchIncidentDetails();
    } catch (err: any) {
      setActionError(err?.message || 'Failed to submit comment');
    } finally {
      setSubmittingComment(false);
    }
  };

  if (loading && !incident) {
    return <LoadingSkeleton rows={6} height="h-32" />;
  }

  if (!incident) {
    return (
      <div className="p-8 text-center bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white">Incident Not Found</h3>
        <button
          onClick={() => navigate('/incidents')}
          className="mt-4 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold cursor-pointer transition shadow-sm"
        >
          Return to Incidents
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/incidents')}
          className="inline-flex items-center space-x-2 text-xs text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Incidents List</span>
        </button>
      </div>

      {actionError && (
        <div className="p-3 bg-red-50 dark:bg-red-950/80 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-500 dark:text-red-400 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Main Incident Banner */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-6 shadow-sm transition-colors duration-150">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge severity={incident.severity} size="md" />
              <StatusBadge status={incident.status} />
              <span className="font-mono text-xs text-slate-700 dark:text-slate-400 bg-slate-100 dark:bg-navy-950 px-2.5 py-1 rounded-md border border-slate-200 dark:border-slate-800">
                {incident.service_name} [{incident.environment}]
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                • {incident.event_count} telemetry events deduplicated
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">{incident.title}</h1>
            <p className="text-xs text-slate-600 dark:text-slate-300 max-w-3xl leading-relaxed">{incident.description}</p>
          </div>

          {/* Action State Transition Buttons */}
          {canModify && (
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {incident.status === 'OPEN' && (
                <button
                  onClick={() => handleStatusTransition('acknowledge')}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-sm"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Acknowledge</span>
                </button>
              )}

              {(incident.status === 'OPEN' || incident.status === 'ACKNOWLEDGED') && (
                <button
                  onClick={() => handleStatusTransition('investigate')}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-sm"
                >
                  <Play className="w-4 h-4" />
                  <span>Start Investigation</span>
                </button>
              )}

              {incident.status !== 'RESOLVED' && (
                <button
                  onClick={() => {
                    setResolveReason('');
                    setIsResolveModalOpen(true);
                  }}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-sm"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Resolve Incident</span>
                </button>
              )}

              {incident.status === 'RESOLVED' && (
                <button
                  onClick={() => handleStatusTransition('reopen')}
                  className="px-4 py-2 bg-rose-700 hover:bg-rose-600 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-sm"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Reopen Incident</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Metadata stats bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 text-xs">
          <div>
            <span className="text-slate-500 dark:text-slate-400 block mb-0.5">Assigned Engineer</span>
            {canModify ? (
              <div className="space-y-1">
                <select
                  value={incident.assigned_user_id || ''}
                  onChange={(e) => handleAssignUser(e.target.value)}
                  disabled={assigneesLoading}
                  className="bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded px-2 py-1 text-slate-800 dark:text-slate-200 text-xs w-full focus:outline-none focus:border-brand-500 disabled:opacity-50 cursor-pointer"
                >
                  <option value="">Unassigned</option>
                  {assigneesLoading && <option disabled>Loading eligible engineers...</option>}
                  {!assigneesLoading && assignees.length === 0 && (
                    <option disabled>No assignable engineers available</option>
                  )}
                  {assignees.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} ({u.role})
                    </option>
                  ))}
                </select>
                {assigneesError && (
                  <p className="text-[10px] text-rose-500 dark:text-rose-400 mt-0.5">{assigneesError}</p>
                )}
              </div>
            ) : (
              <span className="font-semibold text-slate-800 dark:text-slate-200">{incident.assigned_user_name || 'Unassigned'}</span>
            )}
          </div>

          <div>
            <span className="text-slate-500 dark:text-slate-400 block mb-0.5">First Detected</span>
            <span className="font-mono text-slate-800 dark:text-slate-200">
              {new Date(incident.first_detected_at).toLocaleString()}
            </span>
          </div>

          <div>
            <span className="text-slate-500 dark:text-slate-400 block mb-0.5">Last Recurrence</span>
            <span className="font-mono text-slate-800 dark:text-slate-200">
              {new Date(incident.last_detected_at).toLocaleString()}
            </span>
          </div>

          <div>
            <span className="text-slate-500 dark:text-slate-400 block mb-0.5">Deduplication Fingerprint</span>
            <span className="font-mono text-[11px] text-slate-600 dark:text-slate-400 truncate block" title={incident.fingerprint}>
              {incident.fingerprint.slice(0, 16)}...
            </span>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Left Details/Logs & Right Timeline/Comments */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Related Triggering Logs (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm transition-colors duration-150">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-brand-500 dark:text-brand-400" />
                  <span>Related Trigger Logs ({incident.related_logs?.length || 0})</span>
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">Captured telemetry events associated with this incident</p>
              </div>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-96 overflow-y-auto font-mono text-xs">
              {(incident.related_logs || []).length === 0 ? (
                <div className="py-6 text-center text-slate-400">No linked logs stored.</div>
              ) : (
                (incident.related_logs || []).map((log, idx) => (
                  <div key={idx} className="p-3 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                    <div className="flex items-center justify-between mb-1 text-[11px]">
                      <div className="flex items-center space-x-2">
                        <SeverityBadge severity={log.severity} size="sm" />
                        <span className="text-slate-500 dark:text-slate-400">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {log.trace_id && (
                        <span className="text-brand-600 dark:text-brand-400 text-[10px]">trace: {log.trace_id}</span>
                      )}
                    </div>
                    <div className="text-slate-800 dark:text-slate-200 font-sans text-xs mt-1 leading-relaxed">
                      {log.message}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Timeline & Comments (1 col) */}
        <div className="space-y-6">
          {/* Incident Timeline */}
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm transition-colors duration-150">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-500 dark:text-brand-400" />
              <span>Incident Audit Timeline</span>
            </h3>

            <div className="relative pl-6 space-y-4 border-l border-slate-200 dark:border-slate-800 text-xs">
              {(incident.timeline || []).map((evt) => (
                <div key={evt.id} className="relative">
                  <span className="absolute -left-[29px] top-1 w-2.5 h-2.5 rounded-full bg-brand-500 ring-4 ring-white dark:ring-navy-900" />
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{evt.event_type}</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">by {evt.actor_name}</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                    {new Date(evt.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Investigation Comments */}
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm space-y-4 transition-colors duration-150">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-brand-500 dark:text-brand-400" />
              <span>Investigation Notes ({incident.comments?.length || 0})</span>
            </h3>

            {/* Comments List */}
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {(incident.comments || []).length === 0 ? (
                <div className="text-xs text-slate-400 italic">No comments yet.</div>
              ) : (
                incident.comments.map((c) => (
                  <div key={c.id} className="p-3 bg-slate-50 dark:bg-navy-950 rounded-xl border border-slate-200 dark:border-slate-800 text-xs">
                    <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                      <span className="font-semibold text-slate-700 dark:text-slate-300">{c.user_name || 'Engineer'}</span>
                      <span>{new Date(c.created_at).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-slate-800 dark:text-slate-200 leading-relaxed">{c.comment}</div>
                  </div>
                ))
              )}
            </div>

            {/* Add Comment Box */}
            {canModify && (
              <form onSubmit={handlePostComment} className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Add an investigation note, root cause hypothesis, or mitigation link..."
                  rows={2}
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-brand-500 transition"
                />
                <button
                  type="submit"
                  disabled={submittingComment || !commentText.trim()}
                  className="w-full py-1.5 px-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Post Comment</span>
                </button>
              </form>
            )}
          </div>
        </div>
      </div>

      {/* Resolve Incident Dialog Modal */}
      {isResolveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Resolve Incident</h3>
              </div>
              <button
                onClick={() => setIsResolveModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleConfirmResolve} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
                  Resolution Summary / Fix Applied
                </label>
                <textarea
                  rows={3}
                  value={resolveReason}
                  onChange={(e) => setResolveReason(e.target.value)}
                  placeholder="e.g. Deployed bugfix to payment retry handler, downstream service recovered"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                />
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                  This note will be recorded in the incident audit trail.
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsResolveModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isResolving}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{isResolving ? 'Resolving...' : 'Confirm Resolution'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
