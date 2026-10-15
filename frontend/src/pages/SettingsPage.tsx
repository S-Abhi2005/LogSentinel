import React, { useState, useEffect } from 'react';
import {
  User as UserIcon,
  Lock,
  Users,
  Shield,
  CheckCircle2,
  AlertCircle,
  Plus,
  Power,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { User, UserRole } from '../types';
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';

export const SettingsPage: React.FC = () => {
  const { user, hasRole } = useAuth();
  const isAdmin = hasRole(['super_admin']);

  // Change Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwMessage, setPwMessage] = useState<{ text: string; error: boolean } | null>(null);
  const [pwSubmitting, setPwSubmitting] = useState(false);

  // User Management state (Admin only)
  const [usersList, setUsersList] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('viewer');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [addUserError, setAddUserError] = useState<string | null>(null);

  const fetchUsers = async () => {
    if (!isAdmin) return;
    setLoadingUsers(true);
    try {
      const data = await api.get<User[]>('/auth/users');
      setUsersList(data);
    } catch (_) {}
    finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [isAdmin]);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwMessage(null);

    if (newPassword !== confirmPassword) {
      setPwMessage({ text: 'New passwords do not match', error: true });
      return;
    }
    if (newPassword.length < 8) {
      setPwMessage({ text: 'New password must be at least 8 characters long', error: true });
      return;
    }

    setPwSubmitting(true);
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwMessage({ text: 'Password successfully updated!', error: false });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPwMessage({ text: err?.message || 'Failed to update password', error: true });
    } finally {
      setPwSubmitting(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddUserError(null);
    try {
      await api.post('/auth/users', {
        email: newEmail.trim(),
        full_name: newFullName.trim(),
        role: newRole,
        password: newUserPassword,
      });
      setIsAddUserOpen(false);
      setNewEmail('');
      setNewFullName('');
      setNewUserPassword('');
      await fetchUsers();
    } catch (err: any) {
      setAddUserError(err?.message || 'Failed to create user');
    }
  };

  const handleToggleUserActive = async (targetUser: User) => {
    try {
      await api.patch(`/auth/users/${targetUser.id}`, {
        is_active: !targetUser.is_active,
      });
      await fetchUsers();
    } catch (err: any) {
      alert(err?.message || 'Failed to modify user status');
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">System Settings & Profile</h1>
        <p className="text-xs text-slate-400">Account preferences and role-based access management</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* User Profile Card */}
        <div className="bg-navy-900 border border-charcoal-700 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-800">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center font-bold text-lg text-white shadow-md">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">{user?.full_name}</h3>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div>
              <span className="text-slate-400 block text-[11px]">Role Permission</span>
              <span className="font-semibold text-brand-400 capitalize bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20 inline-block mt-0.5">
                {user?.role?.replace('_', ' ')}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Account ID</span>
              <span className="font-mono text-slate-300 text-[11px] truncate block">{user?.id}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Account Created</span>
              <span className="text-slate-300 text-[11px]">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Change Password Form */}
        <div className="md:col-span-2 bg-navy-900 border border-charcoal-700 rounded-2xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-1">
            <Lock className="w-4 h-4 text-brand-400" />
            <span>Update Account Password</span>
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Ensure your account is protected with a secure password (minimum 8 characters).
          </p>

          {pwMessage && (
            <div
              className={`p-3 rounded-xl mb-4 text-xs flex items-center gap-2 border ${
                pwMessage.error
                  ? 'bg-red-950/70 border-red-800 text-red-300'
                  : 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
              }`}
            >
              {pwMessage.error ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
              <span>{pwMessage.text}</span>
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-3 max-w-md text-xs">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Current Password</label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">New Password</label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Confirm New Password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>

            <button
              type="submit"
              disabled={pwSubmitting}
              className="py-2 px-4 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg font-semibold transition cursor-pointer"
            >
              {pwSubmitting ? 'Updating...' : 'Change Password'}
            </button>
          </form>
        </div>
      </div>

      {/* User Administration Section (Super Admin Only) */}
      {isAdmin && (
        <div className="bg-navy-900 border border-charcoal-700 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-brand-400" />
                <span>User Directory & Role-Based Access</span>
              </h3>
              <p className="text-xs text-slate-400">Manage member accounts and permissions</p>
            </div>
            <button
              onClick={() => setIsAddUserOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition cursor-pointer self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              <span>Add Member</span>
            </button>
          </div>

          {loadingUsers ? (
            <LoadingSkeleton rows={3} height="h-10" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-navy-950 text-slate-400 uppercase tracking-wider font-mono border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Name</th>
                    <th className="py-2.5 px-3">Email</th>
                    <th className="py-2.5 px-3">Role</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {usersList.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-3 font-semibold text-slate-200">{u.full_name}</td>
                      <td className="py-3 px-3 text-slate-400 font-mono">{u.email}</td>
                      <td className="py-3 px-3">
                        <span className="capitalize px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px]">
                          {u.role.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        {u.is_active ? (
                          <span className="text-emerald-400 flex items-center gap-1 text-[11px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            Active
                          </span>
                        ) : (
                          <span className="text-red-400 flex items-center gap-1 text-[11px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                            Deactivated
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-right">
                        {u.id !== user?.id && (
                          <button
                            onClick={() => handleToggleUserActive(u)}
                            className={`p-1.5 rounded transition ${
                              u.is_active ? 'text-red-400 hover:bg-red-950/40' : 'text-emerald-400 hover:bg-emerald-950/40'
                            }`}
                            title={u.is_active ? 'Deactivate user' : 'Re-activate user'}
                          >
                            <Power className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Add User Modal */}
      {isAddUserOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-navy-900 border border-charcoal-700 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Create New User</h3>
              <button onClick={() => setIsAddUserOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {addUserError && (
              <div className="p-3 bg-red-950 border border-red-800 rounded-xl text-red-300 text-xs">
                {addUserError}
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  placeholder="e.g. Dana Scully"
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="scully@logsentinel.local"
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as UserRole)}
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                >
                  <option value="viewer">Viewer (Read-Only)</option>
                  <option value="engineer">Engineer (Triage & Investigate)</option>
                  <option value="super_admin">Super Admin (Full System Access)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Temporary Password</label>
                <input
                  type="password"
                  required
                  value={newUserPassword}
                  onChange={(e) => setNewUserPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddUserOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-medium cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-medium cursor-pointer"
                >
                  Add Member
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
