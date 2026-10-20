import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Radio, LogIn, Lock, Mail, AlertCircle, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { AnimatedBackground } from '../components/common/AnimatedBackground';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { toggleTheme, isDark } = useTheme();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err?.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Animated Aurora Multicolor Background */}
      <AnimatedBackground variant="login" />

      {/* Top right theme toggle */}
      <div className="absolute top-5 right-5 z-20">
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
          className="p-2.5 rounded-xl bg-white/70 dark:bg-navy-900/70 hover:bg-white/90 dark:hover:bg-navy-900/90 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-slate-200 shadow-md backdrop-blur-md transition-all cursor-pointer"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>
      </div>

      <div className="w-full max-w-md z-10 my-8">
        {/* Brand Logo & Title */}
        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 via-indigo-500 to-cyan-400 text-white shadow-xl shadow-brand-500/25 ring-1 ring-white/30 mb-4 transition-transform hover:scale-105 duration-300">
            <Radio className="w-8 h-8 animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white drop-shadow-xs">LogSentinel</h1>
          <p className="text-xs font-medium text-slate-600 dark:text-slate-300 mt-1">Cloud Log Intelligence & Incident Platform</p>
        </div>

        {/* Glassmorphic Login Card */}
        <div className="bg-white/80 dark:bg-navy-900/80 border border-white/80 dark:border-white/10 rounded-3xl shadow-2xl shadow-indigo-950/15 dark:shadow-black/60 p-6 sm:p-8 backdrop-blur-2xl transition-all">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-6">Sign in to your account</h2>

          {error && (
            <div className="mb-5 p-3 rounded-xl bg-rose-50/90 dark:bg-red-950/70 border border-rose-200 dark:border-red-800/80 text-rose-700 dark:text-red-300 text-xs flex items-center gap-2 shadow-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500 dark:text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 dark:text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@logsentinel.local"
                  className="w-full bg-slate-50/90 dark:bg-navy-950/80 border border-slate-300 dark:border-slate-700/80 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 dark:text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-50/90 dark:bg-navy-950/80 border border-slate-300 dark:border-slate-700/80 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white rounded-xl font-semibold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-brand-500/25 disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? (
                <span>Authenticating...</span>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-8 pt-6 border-t border-slate-200/60 dark:border-slate-800">
            <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2.5 text-center">
              Quick Demo Accounts (1-Click Fill)
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@logsentinel.local', 'AdminSecurePass123!')}
                className="p-2.5 bg-slate-50/80 hover:bg-slate-100 dark:bg-navy-950/70 dark:hover:bg-slate-800/80 border border-slate-200/80 dark:border-slate-800/80 rounded-xl text-left transition cursor-pointer shadow-xs hover:border-brand-400 dark:hover:border-brand-500/50"
              >
                <div className="text-[11px] font-bold text-brand-600 dark:text-brand-400">Admin</div>
                <div className="text-[9px] text-slate-500 dark:text-slate-400 truncate">Super Admin</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('engineer@logsentinel.local', 'EngineerSecurePass123!')}
                className="p-2.5 bg-slate-50/80 hover:bg-slate-100 dark:bg-navy-950/70 dark:hover:bg-slate-800/80 border border-slate-200/80 dark:border-slate-800/80 rounded-xl text-left transition cursor-pointer shadow-xs hover:border-amber-400 dark:hover:border-amber-500/50"
              >
                <div className="text-[11px] font-bold text-amber-600 dark:text-amber-400">Engineer</div>
                <div className="text-[9px] text-slate-500 dark:text-slate-400 truncate">On-Call SRE</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('viewer@logsentinel.local', 'ViewerSecurePass123!')}
                className="p-2.5 bg-slate-50/80 hover:bg-slate-100 dark:bg-navy-950/70 dark:hover:bg-slate-800/80 border border-slate-200/80 dark:border-slate-800/80 rounded-xl text-left transition cursor-pointer shadow-xs hover:border-slate-400 dark:hover:border-slate-600"
              >
                <div className="text-[11px] font-bold text-slate-700 dark:text-slate-300">Viewer</div>
                <div className="text-[9px] text-slate-500 dark:text-slate-400 truncate">Read-Only</div>
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 dark:text-slate-400 mt-6 font-medium">
          Designed for Cloud Telemetry & Reliable Incident Response
        </p>
      </div>
    </div>
  );
};
