import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Mail,
  Globe,
  UploadCloud,
  History,
  Settings,
  ShieldCheck
} from 'lucide-react';
import { cn } from '../../utils/cn';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Email Analysis', path: '/email', icon: Mail },
  { name: 'URL Analysis', path: '/url', icon: Globe },
  { name: 'Batch EML Upload', path: '/upload-eml', icon: UploadCloud },
  { name: 'Audit History', path: '/history', icon: History },
  { name: 'Settings & Diagnostics', path: '/settings', icon: Settings },
];

export function Sidebar({ onCloseMobile, className }) {
  return (
    <aside
      className={cn(
        'w-64 bg-[#101216] border-r border-white/[0.08] flex flex-col justify-between p-4 z-40',
        className
      )}
    >
      <div>
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-2 py-3 mb-4 border-b border-white/[0.06]">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#181c23] border border-white/[0.08] text-slate-200">
            <ShieldCheck className="w-4 h-4 text-slate-200" />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-white leading-none">
              PhishGuard
            </h1>
            <p className="text-xs text-slate-400 mt-1">Threat Analysis Console</p>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="px-2 pb-2">
          <span className="text-[11px] font-medium text-slate-500">Navigation</span>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onCloseMobile}
                end={item.path === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors duration-150',
                    isActive
                      ? 'bg-[#1c2027] text-white border border-white/[0.08]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#14171c]'
                  )
                }
              >
                {({ isActive }) => (
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        'w-4 h-4',
                        isActive ? 'text-white' : 'text-slate-400'
                      )}
                    />
                    <span>{item.name}</span>
                  </div>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-white/[0.06] px-2 space-y-1.5">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#2da44e]" />
            <span className="text-[11px]">System online</span>
          </span>
          <span className="font-mono text-[11px] text-slate-500">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
}
