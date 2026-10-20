import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Bell,
  Sun,
  Moon,
  ChevronDown,
  User as UserIcon,
  Lock,
  Settings,
  LogOut,
  X,
  CheckCircle2,
  AlertCircle,
  Shield,
  Clock,
  IdCard,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { api } from '../../api/client';
import { AlertItem } from '../../types';
import { SeverityBadge } from '../common/SeverityBadge';

export const TopBar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, refreshUser } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();

  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isAlertsOpen, setIsAlertsOpen] = useState<boolean>(false);
  const [backendHealthy, setBackendHealthy] = useState<boolean>(true);

  // Profile Dropdown & Modal States
  const [isProfileOpen, setIsProfileOpen] = useState<boolean>(false);
  const [isEditProfileModalOpen, setIsEditProfileModalOpen] = useState<boolean>(false);
  const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] = useState<boolean>(false);

  // Profile Edit Form State
  const [editFullName, setEditFullName] = useState<string>('');
  const [profileSaving, setProfileSaving] = useState<boolean>(false);
  const [profileMessage, setProfileMessage] = useState<{ text: string; error: boolean } | null>(null);

  // Change Password Form State
  const [currPassword, setCurrPassword] = useState<string>('');
  const [newPassword, setNewPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [pwSaving, setPwSaving] = useState<boolean>(false);
  const [pwMessage, setPwMessage] = useState<{ text: string; error: boolean } | null>(null);

  const profileRef = useRef<HTMLDivElement>(null);
  const alertsRef = useRef<HTMLDivElement>(null);

  // Map route to title
  const pageTitles: Record<string, string> = {
    '/': 'Overview Dashboard',
    '/logs': 'Logs Explorer',
    '/incidents': 'Incident Management',
    '/rules': 'Detection Rules',
    '/services': 'Service Registry & Ingestion Keys',
    '/alerts': 'Alert Notifications',
    '/audit': 'Audit & Security Logs',
    '/settings': 'System Settings & Profile',
  };

  const currentTitle = pageTitles[location.pathname] || 'LogSentinel';

  const fetchAlerts = async () => {
    try {
      const data = await api.get<{ items: AlertItem[]; unread_count: number }>('/alerts?limit=5');
      setAlerts(data.items);
      setUnreadCount(data.unread_count);
      setBackendHealthy(true);
    } catch (err) {
      setBackendHealthy(false);
      console.warn('Backend health check or alert fetch failed:', err);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const timer = setInterval(fetchAlerts, 15000);
    return () => clearInterval(timer);
  }, []);

  // Handle outside click & escape key to close menus reliably
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setIsProfileOpen(false);
      }
      if (alertsRef.current && !alertsRef.current.contains(e.target as Node)) {
        setIsAlertsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsProfileOpen(false);
        setIsAlertsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const markAllRead = async () => {
    try {
      await api.post('/alerts/read-all');
      setUnreadCount(0);
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
    } catch (err) {
      console.error('Failed to mark alerts as read:', err);
    }
  };

  const openEditProfile = () => {
    setEditFullName(user?.full_name || '');
    setProfileMessage(null);
    setIsProfileOpen(false);
    setIsEditProfileModalOpen(true);
  };

  const openChangePassword = () => {
    setCurrPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setPwMessage(null);
    setIsProfileOpen(false);
    setIsChangePasswordModalOpen(true);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMessage(null);

    const trimmed = editFullName.trim();
    if (trimmed.length < 2) {
      setProfileMessage({ text: 'Full name must be at least 2 characters long.', error: true });
      return;
    }

    setProfileSaving(true);
    try {
      await api.patch('/auth/me', { full_name: trimmed });
      await refreshUser();
      setProfileMessage({ text: 'Profile updated successfully!', error: false });
      setTimeout(() => {
        setIsEditProfileModalOpen(false);
      }, 1200);
    } catch (err: any) {
      setProfileMessage({ text: err?.message || 'Failed to update profile.', error: true });
    } finally {
      setProfileSaving(false);
    }
  };

  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwMessage(null);

    if (newPassword !== confirmPassword) {
      setPwMessage({ text: 'New passwords do not match.', error: true });
      return;
    }
    if (newPassword.length < 8) {
      setPwMessage({ text: 'New password must be at least 8 characters long.', error: true });
      return;
    }

    setPwSaving(true);
    try {
      await api.post('/auth/change-password', {
        current_password: currPassword,
        new_password: newPassword,
      });
      setPwMessage({ text: 'Password successfully changed!', error: false });
      setCurrPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => {
        setIsChangePasswordModalOpen(false);
      }, 1500);
    } catch (err: any) {
      setPwMessage({ text: err?.message || 'Failed to change password.', error: true });
    } finally {
      setPwSaving(false);
    }
  };

  return (
    <>
      <header className="h-16 bg-white dark:bg-navy-900 border-b border-slate-200 dark:border-charcoal-800 px-6 flex items-center justify-between z-20 shrink-0 transition-colors duration-150">
        {/* Title & Breadcrumbs */}
        <div>
          <div className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400">
            <span>Platform</span>
            <span>/</span>
            <span className="text-slate-700 dark:text-slate-200 capitalize font-medium">
              {location.pathname.replace('/', '') || 'Overview'}
            </span>
          </div>
          <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight">{currentTitle}</h2>
        </div>

        {/* Right Action Controls */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          {/* Live System Status Indicator */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-slate-100 dark:bg-navy-950 rounded-full border border-slate-200 dark:border-slate-800 text-xs">
            <span className={`w-2 h-2 rounded-full ${backendHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-slate-600 dark:text-slate-300 font-medium">
              {backendHealthy ? 'Live Ingestion Active' : 'API Connecting...'}
            </span>
          </div>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition"
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? (
              <Sun className="w-5 h-5 text-amber-400 transition-transform duration-200 hover:rotate-45" />
            ) : (
              <Moon className="w-5 h-5 text-slate-600 transition-transform duration-200 hover:-rotate-12" />
            )}
          </button>

          {/* Alerts Bell Popover */}
          <div className="relative" ref={alertsRef}>
            <button
              onClick={() => setIsAlertsOpen(!isAlertsOpen)}
              className="p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg relative transition"
              title="Notifications"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-white dark:ring-navy-900">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {isAlertsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-xl shadow-2xl py-3 z-50 text-slate-900 dark:text-slate-100 animate-in fade-in zoom-in-95 duration-100">
                <div className="flex items-center justify-between px-4 pb-2 border-b border-slate-200 dark:border-slate-800">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-200">
                    Recent Alerts
                  </span>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-[11px] text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 transition font-medium"
                    >
                      Mark all read
                    </button>
                  )}
                </div>

                <div className="max-h-64 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/60">
                  {alerts.length === 0 ? (
                    <div className="py-6 text-center text-xs text-slate-400">No alerts triggered</div>
                  ) : (
                    alerts.map((alert) => (
                      <div
                        key={alert.id}
                        onClick={() => {
                          setIsAlertsOpen(false);
                          navigate('/alerts');
                        }}
                        className={`p-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition ${
                          !alert.is_read ? 'bg-brand-50/50 dark:bg-brand-500/5' : ''
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <SeverityBadge severity={alert.severity} size="sm" />
                          <span className="text-[10px] text-slate-400">
                            {new Date(alert.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="text-xs font-medium text-slate-800 dark:text-slate-200 line-clamp-1">
                          {alert.title}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-1">
                          {alert.message}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="px-4 pt-2 border-t border-slate-200 dark:border-slate-800 text-center">
                  <button
                    onClick={() => {
                      setIsAlertsOpen(false);
                      navigate('/alerts');
                    }}
                    className="text-xs text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 font-medium"
                  >
                    View all alerts &rarr;
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Dropdown Button */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="flex items-center space-x-2 p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/80 transition focus:outline-none focus:ring-2 focus:ring-brand-500/40"
              aria-haspopup="true"
              aria-expanded={isProfileOpen}
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-xs font-bold text-white shadow-sm ring-1 ring-brand-400">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div className="hidden md:flex flex-col text-left mr-1">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 max-w-[120px] truncate">
                  {user?.full_name || 'User'}
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 capitalize">
                  {user?.role?.replace('_', ' ')}
                </span>
              </div>
              <ChevronDown
                className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${
                  isProfileOpen ? 'rotate-180' : ''
                }`}
              />
            </button>

            {/* Profile Dropdown Menu */}
            {isProfileOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
                {/* Header User Details */}
                <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-sm font-bold text-white shadow ring-2 ring-brand-400">
                      {user?.full_name?.charAt(0) || 'U'}
                    </div>
                    <div className="truncate">
                      <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                        {user?.full_name}
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                        {user?.email}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px] mt-1 pt-2 border-t border-slate-100 dark:border-slate-800/80">
                    <span className="text-slate-500 dark:text-slate-400">Role:</span>
                    <span className="font-semibold text-brand-600 dark:text-brand-400 capitalize bg-brand-50 dark:bg-brand-500/10 px-2 py-0.5 rounded border border-brand-200 dark:border-brand-500/20">
                      {user?.role?.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                {/* Actions list */}
                <div className="p-1 space-y-0.5 text-xs">
                  <button
                    onClick={openEditProfile}
                    className="w-full flex items-center space-x-2.5 px-3 py-2 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition text-left cursor-pointer"
                  >
                    <UserIcon className="w-4 h-4 text-brand-500 dark:text-brand-400 shrink-0" />
                    <span>View & Edit Profile</span>
                  </button>

                  <button
                    onClick={openChangePassword}
                    className="w-full flex items-center space-x-2.5 px-3 py-2 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition text-left cursor-pointer"
                  >
                    <Lock className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0" />
                    <span>Change Password</span>
                  </button>

                  <button
                    onClick={() => {
                      setIsProfileOpen(false);
                      navigate('/settings');
                    }}
                    className="w-full flex items-center space-x-2.5 px-3 py-2 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition text-left cursor-pointer"
                  >
                    <Settings className="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0" />
                    <span>System Settings</span>
                  </button>
                </div>

                <div className="p-1 border-t border-slate-100 dark:border-slate-800 mt-1">
                  <button
                    onClick={() => {
                      setIsProfileOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center space-x-2.5 px-3 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg transition text-left font-medium cursor-pointer"
                  >
                    <LogOut className="w-4 h-4 shrink-0" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Edit Profile Modal */}
      {isEditProfileModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <UserIcon className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Account Profile</h3>
              </div>
              <button
                onClick={() => setIsEditProfileModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {profileMessage && (
              <div
                className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
                  profileMessage.error
                    ? 'bg-red-50 dark:bg-red-950/70 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
                    : 'bg-emerald-50 dark:bg-emerald-950/70 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
                }`}
              >
                {profileMessage.error ? (
                  <AlertCircle className="w-4 h-4 shrink-0" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                )}
                <span>{profileMessage.text}</span>
              </div>
            )}

            <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
              {/* Full Name (Editable) */}
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={editFullName}
                  onChange={(e) => setEditFullName(e.target.value)}
                  placeholder="e.g. Alex Vance"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500 font-medium"
                />
              </div>

              {/* Email (Read Only) */}
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Email Address</label>
                <input
                  type="email"
                  disabled
                  value={user?.email || ''}
                  className="w-full bg-slate-100 dark:bg-navy-950/60 border border-slate-200 dark:border-slate-800 rounded-lg p-2.5 text-slate-500 dark:text-slate-400 cursor-not-allowed font-mono"
                />
                <p className="text-[11px] text-slate-400 mt-1">Managed by system administrator.</p>
              </div>

              {/* Role & Account ID Details */}
              <div className="p-3 bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-2 text-[11px]">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-brand-500" />
                    Role Permission:
                  </span>
                  <span className="font-semibold text-brand-600 dark:text-brand-400 capitalize">
                    {user?.role?.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <IdCard className="w-3.5 h-3.5 text-slate-400" />
                    User ID:
                  </span>
                  <span className="font-mono text-slate-700 dark:text-slate-300 truncate max-w-[180px]">
                    {user?.id}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    Member Since:
                  </span>
                  <span className="text-slate-700 dark:text-slate-300">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEditProfileModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={profileSaving}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-semibold transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                >
                  {profileSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {isChangePasswordModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-charcoal-700 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Lock className="w-5 h-5 text-amber-500 dark:text-amber-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Change Account Password</h3>
              </div>
              <button
                onClick={() => setIsChangePasswordModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {pwMessage && (
              <div
                className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
                  pwMessage.error
                    ? 'bg-red-50 dark:bg-red-950/70 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
                    : 'bg-emerald-50 dark:bg-emerald-950/70 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
                }`}
              >
                {pwMessage.error ? (
                  <AlertCircle className="w-4 h-4 shrink-0" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                )}
                <span>{pwMessage.text}</span>
              </div>
            )}

            <form onSubmit={handleSavePassword} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
                  Current Password <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={currPassword}
                  onChange={(e) => setCurrPassword(e.target.value)}
                  placeholder="Enter current password"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
                  New Password <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
                  Confirm New Password <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                  className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsChangePasswordModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={pwSaving}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-semibold transition disabled:opacity-50 cursor-pointer"
                >
                  {pwSaving ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
