import React, { useState, useCallback } from 'react';
import { useStore } from '../store/useStore';
import {
  Camera, CameraOff, Maximize2, Minimize2, RefreshCw,
  AlertTriangle,
} from 'lucide-react';

const STREAM_URL = '/api/stream';

export default function CameraFeed() {
  const { camStatus } = useStore();
  const [error, setError]         = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [retryKey, setRetryKey]   = useState(0);

  const retry = useCallback(() => {
    setError(false);
    setRetryKey(k => k + 1);
  }, []);

  const online = camStatus.connected && !error;

  return (
    <div className={`relative flex flex-col overflow-hidden rounded-[10px] border border-border bg-black ${
      fullscreen ? 'fixed inset-0 z-50 rounded-none border-0' : 'h-full'
    }`}>

      {/* ── Header bar ─────────────────────────────────────────────────── */}
      <div className="absolute top-0 inset-x-0 z-10 flex items-center justify-between px-4 py-3
                      bg-gradient-to-b from-black/80 to-transparent">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${online ? 'bg-green-400 pulse-dot' : 'bg-red-500'}`} />
          <span className="text-[11px] font-semibold tracking-widest text-white/70 mono">
            CAM-01
          </span>
          {online && (
            <span className="badge badge-green">
              {camStatus.fps?.toFixed(0)} FPS
            </span>
          )}
        </div>
        <button
          onClick={() => setFullscreen(f => !f)}
          className="p-1.5 rounded-[6px] bg-white/5 hover:bg-white/10 text-white/60
                     hover:text-white transition-colors"
        >
          {fullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* ── Stream / offline state ─────────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center">
        {online ? (
          <img
            key={retryKey}
            src={STREAM_URL}
            alt="Camera feed"
            className="w-full h-full object-contain"
            onError={() => setError(true)}
          />
        ) : (
          <div className="flex flex-col items-center gap-4 text-center px-8">
            {camStatus.connected && error ? (
              <AlertTriangle className="w-12 h-12 text-yellow-500/60" />
            ) : (
              <CameraOff className="w-12 h-12 text-text-dim" />
            )}
            <div>
              <p className="text-[15px] font-semibold text-text-muted">
                {camStatus.connected && error ? 'Stream error' : 'Camera offline'}
              </p>
              <p className="text-[12px] text-text-dim mt-1">
                {camStatus.connected && error
                  ? 'Could not load the MJPEG stream'
                  : 'No camera device detected or camera is busy'}
              </p>
            </div>
            <button onClick={retry} className="btn-ghost mt-1">
              <RefreshCw className="w-3.5 h-3.5" />
              Retry connection
            </button>
          </div>
        )}
      </div>

      {/* ── Bottom status bar ─────────────────────────────────────────── */}
      {online && (
        <div className="absolute bottom-0 inset-x-0 flex items-center gap-4 px-4 py-2.5
                        bg-gradient-to-t from-black/70 to-transparent">
          <span className="text-[10px] mono text-white/40">
            {camStatus.resolution?.[0]}×{camStatus.resolution?.[1]}
          </span>
          <span className="text-[10px] mono text-white/40">
            {camStatus.backend}
          </span>
          <span className="text-[10px] mono text-white/40 ml-auto">
            frames: {camStatus.frame_count?.toLocaleString()}
          </span>
        </div>
      )}
    </div>
  );
}
