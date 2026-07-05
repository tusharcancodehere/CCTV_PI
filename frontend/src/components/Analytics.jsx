import React, { useMemo } from 'react';
import { useStore } from '../store/useStore';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid,
} from 'recharts';

function Chart({ title, data, color, unit }) {
  const points = useMemo(() =>
    (data ?? []).map((pt, i) => ({
      i,
      v: typeof pt === 'object' ? pt.value : pt,
    })),
    [data]
  );

  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[12px] font-semibold text-text-muted tracking-wide uppercase">
          {title}
        </h3>
        <span className="mono text-[11px] text-text-dim">
          {points.length ? points[points.length - 1].v?.toFixed(1) : '—'} {unit}
        </span>
      </div>
      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={points} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
            <defs>
              <linearGradient id={`grad-${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={color} stopOpacity={0.25} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#282c36" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="i" hide />
            <YAxis domain={[0, 'auto']} tick={{ fontSize: 10, fill: '#6b7280' }} />
            <Tooltip
              contentStyle={{ background: '#13151a', border: '1px solid #282c36', borderRadius: 8, fontSize: 12 }}
              labelFormatter={() => ''}
              formatter={(v) => [`${v?.toFixed(1)} ${unit}`, title]}
            />
            <Area
              type="monotone"
              dataKey="v"
              stroke={color}
              strokeWidth={1.5}
              fill={`url(#grad-${title})`}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function Analytics() {
  const { analytics, sysStatus } = useStore();

  const metrics = analytics?.metrics ?? {};

  return (
    <div className="h-full overflow-y-auto scroll-y p-5">
      <h2 className="text-[15px] font-semibold text-text-base mb-4">Analytics</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        <Chart title="FPS"             data={metrics.fps}             color="#5b7fff" unit="fps" />
        <Chart title="Total Latency"   data={metrics.latency}         color="#ef4444" unit="ms" />
        <Chart title="CPU Usage"       data={metrics.cpu}             color="#7c63f5" unit="%" />
        <Chart title="GPU Usage"       data={metrics.gpu}             color="#10b981" unit="%" />
        <Chart title="Memory"          data={metrics.ram}             color="#22c55e" unit="%" />
        <Chart title="Temperature"     data={metrics.temperature}     color="#f59e0b" unit="°C" />
        <Chart title="Detector Time"   data={metrics.detector_time}   color="#ec4899" unit="ms" />
        <Chart title="Processing Time" data={metrics.processing_time} color="#8b5cf6" unit="ms" />
        <Chart title="Encoding Time"   data={metrics.encoding_time}   color="#0ea5e9" unit="ms" />
      </div>

      {/* ── Counters ─────────────────────────────────────────────────────── */}
      {analytics?.counters && (
        <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Object.entries(analytics.counters).map(([k, v]) => (
            <div key={k} className="card p-3">
              <p className="text-[10px] text-text-dim uppercase tracking-wide">{k.replace(/_/g, ' ')}</p>
              <p className="text-[20px] font-bold mono text-text-base mt-1">{v}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
