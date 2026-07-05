import React from 'react';
import { useStore } from '../store/useStore';
import {
  LayoutDashboard, Activity, Terminal,
  Settings, Eye, Video,
} from 'lucide-react';

const NAV = [
  { id: 'dashboard', label: 'Dashboard',  icon: LayoutDashboard },
  { id: 'analytics', label: 'Analytics',  icon: Activity },
  { id: 'logs',      label: 'System Logs',icon: Terminal },
  { id: 'settings',  label: 'Settings',   icon: Settings },
];

export default function Sidebar() {
  const { activeTab, setActiveTab, camStatus } = useStore();

  return (
    <aside className="w-56 h-full flex flex-col border-r border-border bg-surface shrink-0">

      {/* ── Logo ─────────────────────────────────────────────────────────── */}
      <div className="px-5 pt-5 pb-4 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-[8px] bg-accent flex items-center justify-center">
            <Eye className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-[13px] font-bold text-text-base leading-none">VisionCV</p>
            <p className="text-[10px] text-text-muted mt-0.5">Dashboard v1.0</p>
          </div>
        </div>
      </div>

      {/* ── Camera live chip ─────────────────────────────────────────────── */}
      <div className="px-3 pt-4">
        <div className={`flex items-center gap-2 px-3 py-2 rounded-[8px] border text-[12px] font-medium ${
          camStatus.connected
            ? 'bg-green-500/8 border-green-500/15 text-green-400'
            : 'bg-[#1a1d24] border-border text-text-muted'
        }`}>
          <span className={`w-2 h-2 rounded-full shrink-0 ${
            camStatus.connected ? 'bg-green-400 pulse-dot' : 'bg-text-dim'
          }`} />
          {camStatus.connected
            ? `${camStatus.fps?.toFixed(0) ?? 0} FPS · ${camStatus.resolution?.[0] ?? '?'}p`
            : 'Camera offline'}
        </div>
      </div>

      {/* ── Navigation ───────────────────────────────────────────────────── */}
      <nav className="flex-1 px-3 pt-4 space-y-0.5">
        {NAV.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`w-full nav-item ${activeTab === id ? 'nav-item-active' : ''}`}
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </button>
        ))}
      </nav>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <div className="px-4 py-4 border-t border-border">
        <p className="text-[11px] text-text-dim">OpenCV · Flask · React</p>
      </div>
    </aside>
  );
}
