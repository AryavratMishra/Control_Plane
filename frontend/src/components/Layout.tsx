import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';

const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: '⬡' },
  { path: '/incidents', label: 'Incidents', icon: '🚨' },
  { path: '/review', label: 'Review Queue', icon: '👤' },
  { path: '/policies', label: 'Policies', icon: '📋' },
];

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden bg-[#080c14]">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 flex flex-col border-r border-[#1e2d45] bg-[#0d1421]">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-[#1e2d45]">
          <div className="flex items-center gap-3">
            <img 
              src="/logo.svg" 
              alt="Logo" 
              className="w-8 h-8 invert opacity-90 drop-shadow-md" 
            />
            <div>
              <div className="text-sm font-bold text-[#e8edf5]">ControlPlane<span className="text-blue-400">.ai</span></div>
              <div className="text-xs text-[#4a5568]">AI Governance Layer</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = location.pathname === item.path ||
              (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200',
                  active
                    ? 'bg-blue-500/15 text-blue-400 border border-blue-500/20 font-medium'
                    : 'text-[#8b9bb4] hover:bg-[#111827] hover:text-[#e8edf5] border border-transparent',
                )}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-[#1e2d45]">
          <div className="flex items-center gap-2 px-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-[#4a5568]"></span>
          </div>
          <p className="text-xs text-[#4a5568] mt-2 px-2"></p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
