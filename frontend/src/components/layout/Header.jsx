import React, { useEffect, useState } from 'react';
import { Menu, Database, Cpu, ExternalLink } from 'lucide-react';
import { getHealth } from '../../api/healthService';

export function Header({ onOpenMobile }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let isMounted = true;
    getHealth()
      .then((data) => {
        if (isMounted) setHealth(data);
      })
      .catch(() => {
        if (isMounted) setHealth({ status: 'degraded' });
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const isHealthy = health?.status === 'healthy';
  const dbConnected = health?.database?.status === 'connected';

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-14 px-4 md:px-8 bg-[#101216]/95 border-b border-white/[0.08] backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenMobile}
          className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-[#181c23] md:hidden transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>
        <span className="text-xs font-medium text-slate-400 hidden sm:inline-block">
          Dual-Stream Threat Analysis Engine
        </span>
      </div>

      {/* Right Telemetry Indicators */}
      <div className="flex items-center gap-2.5 text-xs">
        {/* ML & DB Status Group */}
        <div className="hidden sm:flex items-center gap-2.5 px-3 py-1 rounded-md bg-[#14171b] border border-white/[0.08] text-slate-300">
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-300">ML Engine</span>
          </div>
          <span className="text-white/[0.15]">|</span>
          <div className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span className={`text-xs ${dbConnected ? 'text-slate-300' : 'text-[#e3b341]'}`}>
              {dbConnected ? 'PostgreSQL' : 'Disconnected'}
            </span>
          </div>
          <span
            className={`w-2 h-2 rounded-full ${
              isHealthy ? 'bg-[#2da44e]' : 'bg-[#d29922]'
            }`}
          />
        </div>

        {/* API Docs Link */}
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-white/[0.08] bg-[#14171b] hover:bg-[#1c2027] text-slate-300 hover:text-white transition-colors"
        >
          <span className="text-xs">API Docs</span>
          <ExternalLink className="w-3 h-3 text-slate-400" />
        </a>
      </div>
    </header>
  );
}
