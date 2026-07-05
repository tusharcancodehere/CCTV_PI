import React from 'react';
import { useStore } from '../store/useStore';
import { Cpu, MemoryStick, Activity, Video } from 'lucide-react';
import CameraFeed from './CameraFeed';

function StatCard({ title, value, unit, icon: Icon, trend }) {
  return (
    <div className="stat-card hover:shadow-card-hover transition-shadow">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-text-muted tracking-wide uppercase">
          {title}
        </span>
        <Icon className="w-4 h-4 text-text-dim" />
      </div>
      <div className="flex items-end gap-1.5">
        <span className="text-[28px] font-bold text-text-base leading-none mono">
          {value}
        </span>
        <span className="text-[13px] text-text-muted mb-0.5">{unit}</span>
      </div>
      {trend !== undefined && (
        <div className="w-full h-1 bg-surface2 rounded-full overflow-hidden">
          <div
            className="h-full bg-accent rounded-full transition-all duration-700"
            style={{ width: `${Math.min(100, Math.max(0, trend))}%` }}
          />
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const { sysStatus, camStatus } = useStore();

  const cpu = sysStatus.cpu_percent ?? 0;
  const ram = sysStatus.ram_percent ?? 0;
  const fps = camStatus.fps ?? 0;

  return (
    <div className="h-full flex flex-col gap-4 p-5 overflow-hidden">

      {/* ── KPI strip ────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 shrink-0">
        <StatCard title="Processor" value={cpu.toFixed(1)} unit="%" icon={Cpu}        trend={cpu} />
        <StatCard title="Memory"    value={ram.toFixed(1)} unit="%" icon={MemoryStick} trend={ram} />
        <StatCard title="Frame Rate" value={fps.toFixed(1)} unit="fps" icon={Activity} trend={(fps/60)*100} />
        <StatCard
          title="Resolution"
          value={camStatus.resolution?.[1] ?? '—'}
          unit="p"
          icon={Video}
        />
      </div>

      {/* ── Camera feed (fills remaining height) ─────────────────────────── */}
      <div className="flex-1 min-h-0">
        <CameraFeed />
      </div>

    </div>
  );
}
