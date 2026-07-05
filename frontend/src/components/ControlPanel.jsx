import React, { useState } from 'react';
import { Settings, Sliders, RotateCcw } from 'lucide-react';

const RESOLUTIONS = [
  { label: '480p',  value: [640, 480] },
  { label: '720p',  value: [1280, 720] },
  { label: '1080p', value: [1920, 1080] },
];
const FRAMERATES = [15, 30, 60];

function Section({ title, children }) {
  return (
    <div className="card p-4">
      <h3 className="text-[11px] font-semibold text-text-muted uppercase tracking-wide mb-3">{title}</h3>
      {children}
    </div>
  );
}

function ToggleGroup({ options, value, onChange, format = (v) => v }) {
  return (
    <div className="flex gap-1.5 flex-wrap">
      {options.map((opt) => {
        const v = opt.value ?? opt;
        const active = JSON.stringify(v) === JSON.stringify(value);
        return (
          <button
            key={opt.label ?? opt}
            onClick={() => onChange(v)}
            className={`px-3 py-1.5 rounded-[7px] text-[12px] font-medium border transition-all ${
              active
                ? 'bg-accent text-white border-accent'
                : 'bg-surface2 border-border text-text-muted hover:border-border2 hover:text-text-base'
            }`}
          >
            {opt.label ?? format(opt)}
          </button>
        );
      })}
    </div>
  );
}

export default function ControlPanel() {
  const [resolution, setResolution] = useState([1280, 720]);
  const [fps,        setFps]        = useState(30);
  const [quality,    setQuality]    = useState(70);
  const [mirrorPreview, setMirrorPreview] = useState(true);
  const [saving,     setSaving]     = useState(false);
  const [saved,      setSaved]      = useState(false);

  const apply = async () => {
    setSaving(true);
    try {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution, fps, quality, mirror_preview: mirrorPreview }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (_) {} finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto scroll-y p-5">
      <div className="flex items-center gap-2 mb-4">
        <Settings className="w-4 h-4 text-text-muted" />
        <h2 className="text-[15px] font-semibold text-text-base">Camera Settings</h2>
      </div>

      <div className="space-y-3 max-w-xl">

        <Section title="Resolution">
          <ToggleGroup options={RESOLUTIONS} value={resolution} onChange={setResolution} />
          <p className="text-[11px] text-text-dim mt-2">
            Current: {resolution[0]}×{resolution[1]}
          </p>
        </Section>

        <Section title="Frame Rate">
          <ToggleGroup options={FRAMERATES} value={fps} onChange={setFps} format={(v) => `${v} fps`} />
        </Section>

        <Section title={`JPEG Quality — ${quality}`}>
          <input
            type="range"
            min={30} max={90} step={5}
            value={quality}
            onChange={(e) => setQuality(Number(e.target.value))}
            className="w-full accent-accent"
          />
          <div className="flex justify-between text-[10px] text-text-dim mt-1">
            <span>30 (fast)</span>
            <span>90 (best)</span>
          </div>
        </Section>

        <Section title="Mirror Mode">
          <ToggleGroup 
            options={[{label: 'ON', value: true}, {label: 'OFF', value: false}]} 
            value={mirrorPreview} 
            onChange={setMirrorPreview} 
          />
        </Section>

        {/* ── Apply button ──────────────────────────────────────────────── */}
        <div className="flex gap-2 pt-1">
          <button
            onClick={apply}
            disabled={saving}
            className="btn-primary flex-1 justify-center"
          >
            {saving ? 'Applying…' : saved ? '✓ Applied' : 'Apply Settings'}
          </button>
          <button
            onClick={() => { setResolution([1280,720]); setFps(30); setQuality(70); setMirrorPreview(true); }}
            className="btn-ghost"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
