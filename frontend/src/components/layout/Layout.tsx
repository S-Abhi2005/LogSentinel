import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const Layout: React.FC = () => {
  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 dark:bg-navy-950 dark:text-slate-100 overflow-hidden transition-colors duration-150">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50 dark:bg-navy-950 transition-colors duration-150">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
