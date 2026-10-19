import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Radio, LogIn, Lock, Mail, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

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
    <div className="min-h-screen bg-navy-950 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-brand-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md z-10">
        {/* Brand Logo & Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 to-blue-400 text-white shadow-xl shadow-brand-500/20 ring-1 ring-blue-300/30 mb-4">
            <Radio className="w-8 h-8 animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">LogSentinel</h1>
          <p className="text-sm text-slate-400 mt-1">Cloud Log Intelligence & Incident Platform</p>
        </div>

        {/* Login Card */}
        <div className="bg-navy-900 border border-charcoal-700 rounded-2xl shadow-2xl p-6 sm:p-8 backdrop-blur-xl">
          <h2 className="text-lg font-semibold text-slate-100 mb-6">Sign in to your account</h2>

          {error && (
            <div className="mb-5 p-3 rounded-xl bg-red-950/60 border border-red-800/80 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@logsentinel.local"
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:border-brand-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-navy-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:border-brand-500 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-2.5 px-4 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-medium text-sm transition flex items-center justify-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50 cursor-pointer"
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
          <div className="mt-8 pt-6 border-t border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 text-center">
              Quick Demo Accounts (1-Click Fill)
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@logsentinel.local', 'AdminSecurePass123!')}
                className="p-2 bg-navy-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-left transition cursor-pointer"
              >
                <div className="text-[11px] font-bold text-brand-400">Admin</div>
                <div className="text-[9px] text-slate-400 truncate">Super Admin</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('engineer@logsentinel.local', 'EngineerSecurePass123!')}
                className="p-2 bg-navy-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-left transition cursor-pointer"
              >
                <div className="text-[11px] font-bold text-amber-400">Engineer</div>
                <div className="text-[9px] text-slate-400 truncate">On-Call SRE</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('viewer@logsentinel.local', 'ViewerSecurePass123!')}
                className="p-2 bg-navy-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-left transition cursor-pointer"
              >
                <div className="text-[11px] font-bold text-slate-300">Viewer</div>
                <div className="text-[9px] text-slate-400 truncate">Read-Only</div>
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          Designed for Cloud Telemetry & Reliable Incident Response
        </p>
      </div>
    </div>
  );
};
