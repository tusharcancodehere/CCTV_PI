import { create } from 'zustand';

export const useStore = create((set, get) => ({
  // ── Remote state ──────────────────────────────────────────────────────────
  sysStatus: {
    cpu_percent: 0,
    ram_percent: 0,
    cpu_avg: 0,
    ram_avg: 0,
    disk_percent: 0,
  },
  camStatus: {
    fps: 0,
    connected: false,
    running: false,
    state: 'OFFLINE',
    resolution: [1280, 720],
    recording: false,
    backend: 'opencv',
    frame_count: 0,
  },
  analytics: null,
  logs: [],

  // ── UI state ──────────────────────────────────────────────────────────────
  activeTab: 'dashboard',
  fullscreen: false,
  commandOpen: false,

  // ── Setters ───────────────────────────────────────────────────────────────
  setSysStatus: (s) => set({ sysStatus: s }),
  setCamStatus: (s) => set({ camStatus: s }),
  setAnalytics: (a) => set({ analytics: a }),
  setLogs: (l) => set({ logs: l }),
  setActiveTab: (t) => set({ activeTab: t }),
  setFullscreen: (f) => set({ fullscreen: f }),
  setCommandOpen: (o) => set({ commandOpen: o }),
}));
