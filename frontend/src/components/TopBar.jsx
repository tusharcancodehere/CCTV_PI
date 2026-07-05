import React from 'react';
import { useStore } from '../store/useStore';
import { Cpu, MemoryStick, Wifi, WifiOff, Circle } from 'lucide-react';

function Pill({ label, value, unit, colorClass = 'text-text-muted' }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-[8px] bg-surface2 border border-border text-[12px]">
      <span className="text-text-dim">{label}</span>
      <span className={`font-semibold mono ${colorClass}`}>{value}</span>
      {unit && <span className="text-text-dim">{unit}</span>}
    </div>
  );
}

export default function TopBar() {
  const { sysStatus, camStatus } = useStore();

  const cpu = sysStatus.cpu_percent ?? 0;
  const ram = sysStatus.ram_percent ?? 0;
  const fps = camStatus.fps ?? 0;
  const online = camStatus.connected;

  const cpuColor = cpu > 80 ? 'text-red-400' : cpu > 60 ? 'text-yellow-400' : 'text-text-base';
  const ramColor = ram > 80 ? 'text-red-400' : ram > 60 ? 'text-yellow-400' : 'text-text-base';

  return (
    <header className="h-12 shrink-0 flex items-center justify-between px-5
                       border-b border-border bg-surface">
      {/* ── Left: page context ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        <span className="text-[13px] font-semibold text-text-base">
          Vision Control Center
        </span>
        <span className="text-text-dim text-[12px]">/</span>
        <span className="text-[12px] text-text-muted">Live</span>
      </div>

      {/* ── Right: system metrics ──────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        <Pill label="CPU" value={cpu.toFixed(0)} unit="%" colorClass={cpuColor} />
        <Pill label="RAM" value={ram.toFixed(0)} unit="%" colorClass={ramColor} />
        <Pill label="FPS" value={fps.toFixed(0)} colorClass="text-accent" />

        {/* ── Connection badge ───────────────────────────────────────── */}
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-[8px] border text-[12px] font-medium ${
          online
            ? 'bg-green-500/8 border-green-500/15 text-green-400'
            : 'bg-surface2 border-border text-text-muted'
        }`}>
          {online
            ? <><Circle className="w-2 h-2 fill-current pulse-dot" />Live</>
            : <><WifiOff className="w-3 h-3" />Offline</>
          }
        </div>
      </div>
    </header>
  );
}
