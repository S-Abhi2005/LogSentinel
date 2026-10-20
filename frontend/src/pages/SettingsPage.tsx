import React, { useState, useEffect, useCallback } from 'react';
import {
  Lock,
  Users,
  CheckCircle2,
  AlertCircle,
  Plus,
  Power,
  X,
  User as UserIcon,
  Edit2,
  Shield,
} from 'lucide-react';
import { api } from '../api/client';
import { User, UserRole } from '../types';
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';

export const SettingsPage: React.FC = () => {
  const { user, hasRole, refreshUser } = useAuth();
  const isAdmin = hasRole(['super_admin']);

  // Edit Profile state
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileFullName, setProfileFullName] = useState(user?.full_name || '');
  const [profileMessage, setProfileMessage] = useState<{ text: string; error: boolean } | null>(null);
  const [profileSubmitting, setProfileSubmitting] = useState(false);

  // Sync profile name when user loads
  useEffect(() => {
    if (user?.full_name) {
      setProfileFullName(user.full_name);
    }
  }, [user]);

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

  const fetchUsers = useCallback(async () => {
    if (!isAdmin) return;
    setLoadingUsers(true);
    try {
      const data = await api.get<User[]>('/auth/users');
      setUsersList(data);
    } catch (err) {
      console.error('Failed to load users in settings:', err);
    } finally {
      setLoadingUsers(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMessage(null);

    const trimmed = profileFullName.trim();
    if (trimmed.length < 2) {
      setProfileMessage({ text: 'Full name must be at least 2 characters.', error: true });
      return;
    }

    setProfileSubmitting(true);
    try {
      await api.patch('/auth/me', { full_name: trimmed });
      await refreshUser();
      setProfileMessage({ text: 'Profile successfully updated!', error: false });
      setTimeout(() => {
        setIsEditingProfile(false);
        setProfileMessage(null);
      }, 1500);
    } catch (err: any) {
      setProfileMessage({ text: err?.message || 'Failed to update profile', error: true });
    } finally {
      setProfileSubmitting(false);
    }
  };

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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* User Profile Card */}
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center font-bold text-lg text-white shadow-md">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">{user?.full_name}</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
              </div>
            </div>
          </div>

          <div className="space-y-2.5 text-xs">
            <div>
              <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Role Permission</span>
              <span className="font-semibold text-brand-700 dark:text-brand-400 capitalize bg-brand-50 dark:bg-brand-500/10 px-2 py-0.5 rounded border border-brand-200 dark:border-brand-500/20 inline-block mt-0.5">
                {user?.role?.replace('_', ' ')}
              </span>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Account ID</span>
              <span className="font-mono text-slate-700 dark:text-slate-300 text-[11px] truncate block">{user?.id}</span>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Account Created</span>
              <span className="text-slate-700 dark:text-slate-300 text-[11px]">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>

          {/* Edit Profile Form / Toggle */}
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
            {!isEditingProfile ? (
              <button
                type="button"
                onClick={() => {
                  setProfileFullName(user?.full_name || '');
                  setIsEditingProfile(true);
                  setProfileMessage(null);
                }}
                className="w-full flex items-center justify-center gap-1.5 py-2 px-3 bg-slate-100 hover:bg-slate-200 dark:bg-navy-950 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-semibold transition cursor-pointer"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>Edit Profile Details</span>
              </button>
            ) : (
              <form onSubmit={handleUpdateProfile} className="space-y-3 pt-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 dark:text-slate-100">Edit Name</span>
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingProfile(false);
                      setProfileMessage(null);
                    }}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs"
                  >
                    Cancel
                  </button>
                </div>

                {profileMessage && (
                  <div
                    className={`p-2 rounded-lg text-[11px] flex items-center gap-1.5 border ${
                      profileMessage.error
                        ? 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/70 dark:border-rose-800 dark:text-rose-300'
                        : 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/70 dark:border-emerald-800 dark:text-emerald-300'
                    }`}
                  >
                    {profileMessage.error ? <AlertCircle className="w-3.5 h-3.5 shrink-0" /> : <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />}
                    <span>{profileMessage.text}</span>
                  </div>
                )}

                <div>
                  <label className="block text-slate-700 dark:text-slate-300 text-[11px] font-medium mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={profileFullName}
                    onChange={(e) => setProfileFullName(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                    placeholder="Your full name"
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={profileSubmitting}
                    className="flex-1 py-1.5 px-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition cursor-pointer"
                  >
                    {profileSubmitting ? 'Saving...' : 'Save Name'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Change Password Form */}
        <div className="md:col-span-2 bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
            <Lock className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <span>Update Account Password</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
            Ensure your account is protected with a secure password (minimum 8 characters).
          </p>

          {pwMessage && (
            <div
              className={`p-3 rounded-xl mb-4 text-xs flex items-center gap-2 border ${
                pwMessage.error
                  ? 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-red-950/70 dark:border-red-800 dark:text-red-300'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/70 dark:border-emerald-800 dark:text-emerald-300'
              }`}
            >
              {pwMessage.error ? <AlertCircle className="w-4 h-4 shrink-0" /> : <CheckCircle2 className="w-4 h-4 shrink-0" />}
              <span>{pwMessage.text}</span>
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-3 max-w-md text-xs">
            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">Current Password</label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">New Password</label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">Confirm New Password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-type new password"
                className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
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
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <span>User Directory & Role-Based Access</span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Manage member accounts and permissions across the platform</p>
            </div>
            <button
              onClick={() => setIsAddUserOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition cursor-pointer self-start sm:self-auto shadow-sm"
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
                <thead className="bg-slate-50 dark:bg-navy-950 text-slate-600 dark:text-slate-400 uppercase tracking-wider font-mono border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Name</th>
                    <th className="py-2.5 px-3">Email</th>
                    <th className="py-2.5 px-3">Role</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {usersList.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                      <td className="py-3 px-3 font-semibold text-slate-900 dark:text-slate-200">{u.full_name}</td>
                      <td className="py-3 px-3 text-slate-500 dark:text-slate-400 font-mono">{u.email}</td>
                      <td className="py-3 px-3">
                        <span className="capitalize px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[11px] font-medium border border-slate-200 dark:border-slate-700">
                          {u.role.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        {u.is_active ? (
                          <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1 text-[11px] font-medium">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            Active
                          </span>
                        ) : (
                          <span className="text-rose-600 dark:text-rose-400 flex items-center gap-1 text-[11px] font-medium">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                            Deactivated
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-right">
                        {u.id !== user?.id && (
                          <button
                            onClick={() => handleToggleUserActive(u)}
                            className={`p-1.5 rounded transition ${
                              u.is_active
                                ? 'text-rose-600 dark:text-red-400 hover:bg-rose-50 dark:hover:bg-red-950/40'
                                : 'text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/40'
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Create New User</h3>
              <button onClick={() => setIsAddUserOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {addUserError && (
              <div className="p-3 bg-rose-50 dark:bg-red-950 border border-rose-200 dark:border-red-800 rounded-xl text-rose-700 dark:text-red-300 text-xs">
                {addUserError}
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  placeholder="e.g. Dana Scully"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="scully@logsentinel.local"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as UserRole)}
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                >
                  <option value="viewer">Viewer (Read-Only)</option>
                  <option value="engineer">Engineer (Triage & Investigate)</option>
                  <option value="super_admin">Super Admin (Full System Access)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Temporary Password</label>
                <input
                  type="password"
                  required
                  value={newUserPassword}
                  onChange={(e) => setNewUserPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddUserOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium cursor-pointer"
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
