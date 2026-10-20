import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Layout } from './components/layout/Layout';
import { LoadingSkeleton } from './components/common/LoadingSkeleton';

// Route-level code splitting via React.lazy
const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })));
const OverviewPage = lazy(() => import('./pages/OverviewPage').then((m) => ({ default: m.OverviewPage })));
const LogsExplorerPage = lazy(() => import('./pages/LogsExplorerPage').then((m) => ({ default: m.LogsExplorerPage })));
const IncidentsPage = lazy(() => import('./pages/IncidentsPage').then((m) => ({ default: m.IncidentsPage })));
const IncidentDetailPage = lazy(() => import('./pages/IncidentDetailPage').then((m) => ({ default: m.IncidentDetailPage })));
const RulesPage = lazy(() => import('./pages/RulesPage').then((m) => ({ default: m.RulesPage })));
const ServicesPage = lazy(() => import('./pages/ServicesPage').then((m) => ({ default: m.ServicesPage })));
const AlertsPage = lazy(() => import('./pages/AlertsPage').then((m) => ({ default: m.AlertsPage })));
const AuditLogsPage = lazy(() => import('./pages/AuditLogsPage').then((m) => ({ default: m.AuditLogsPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));
const AccessDeniedPage = lazy(() => import('./pages/AccessDeniedPage').then((m) => ({ default: m.AccessDeniedPage })));

const PageSuspenseFallback: React.FC = () => (
  <div className="p-8 max-w-6xl mx-auto">
    <LoadingSkeleton rows={5} height="h-24" />
  </div>
);

const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-navy-950 flex items-center justify-center p-8">
        <LoadingSkeleton rows={4} height="h-16" className="w-80" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

const AdminRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-navy-950 flex items-center justify-center p-8">
        <LoadingSkeleton rows={4} height="h-16" className="w-80" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== 'super_admin') {
    return <AccessDeniedPage requiredRole="Super Administrator (super_admin)" />;
  }

  return children;
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageSuspenseFallback />}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />

              <Route
                path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<OverviewPage />} />
              <Route path="logs" element={<LogsExplorerPage />} />
              <Route path="incidents" element={<IncidentsPage />} />
              <Route path="incidents/:id" element={<IncidentDetailPage />} />
              <Route path="rules" element={<RulesPage />} />
              <Route path="services" element={<ServicesPage />} />
              <Route path="alerts" element={<AlertsPage />} />
              <Route
                path="audit"
                element={
                  <AdminRoute>
                    <AuditLogsPage />
                  </AdminRoute>
                }
              />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  </ThemeProvider>
  );
};

export default App;
