import React, { useEffect, useCallback, useRef } from 'react';
import { useStore } from './store/useStore';
import Sidebar   from './components/Sidebar';
import TopBar    from './components/TopBar';
import Dashboard from './components/Dashboard';
import Analytics from './components/Analytics';
import Settings  from './components/ControlPanel';
import LogsPanel from './components/LogsPanel';

// ── Polling interval ──────────────────────────────────────────────────────────
const POLL_STATUS_MS  = 1000;
const POLL_LOGS_MS    = 3000;
const POLL_ANALYTICS_MS = 5000;

export default function App() {
  const {
    activeTab,
    setSysStatus,
    setCamStatus,
    setAnalytics,
    setLogs,
  } = useStore();

  // ── Abort controllers so we never pile up stale requests ─────────────────
  const statusController  = useRef(null);
  const logsController    = useRef(null);
  const analyticsController = useRef(null);

  const fetchStatus = useCallback(async () => {
    statusController.current?.abort();
    statusController.current = new AbortController();
    try {
      const [sysRes, camRes] = await Promise.all([
        fetch('/api/status',        { signal: statusController.current.signal }),
        fetch('/api/camera/status', { signal: statusController.current.signal }),
      ]);
      if (sysRes.ok) {
        const d = await sysRes.json();
        if (d.success) setSysStatus(d.data);
      }
      if (camRes.ok) {
        const d = await camRes.json();
        if (d.success) setCamStatus(d.data);
      }
    } catch (_) { /* aborted or offline — silently ignore */ }
  }, [setSysStatus, setCamStatus]);

  const fetchLogs = useCallback(async () => {
    logsController.current?.abort();
    logsController.current = new AbortController();
    try {
      const res = await fetch('/api/logs?limit=100', { signal: logsController.current.signal });
      if (res.ok) {
        const d = await res.json();
        if (d.success) setLogs(d.logs);
      }
    } catch (_) {}
  }, [setLogs]);

  const fetchAnalytics = useCallback(async () => {
    analyticsController.current?.abort();
    analyticsController.current = new AbortController();
    try {
      const res = await fetch('/api/analytics', { signal: analyticsController.current.signal });
      if (res.ok) {
        const d = await res.json();
        if (d.success) setAnalytics(d.data);
      }
    } catch (_) {}
  }, [setAnalytics]);

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, POLL_STATUS_MS);
    return () => { clearInterval(id); statusController.current?.abort(); };
  }, [fetchStatus]);

  useEffect(() => {
    fetchLogs();
    const id = setInterval(fetchLogs, POLL_LOGS_MS);
    return () => { clearInterval(id); logsController.current?.abort(); };
  }, [fetchLogs]);

  useEffect(() => {
    fetchAnalytics();
    const id = setInterval(fetchAnalytics, POLL_ANALYTICS_MS);
    return () => { clearInterval(id); analyticsController.current?.abort(); };
  }, [fetchAnalytics]);

  // ── Tab → component map ──────────────────────────────────────────────────
  const view = {
    dashboard: <Dashboard />,
    analytics: <Analytics />,
    logs:      <LogsPanel />,
    settings:  <Settings />,
  };

  return (
    <div className="w-screen h-screen flex overflow-hidden bg-bg text-text-base font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-hidden">
          <div className="h-full fade-in">{view[activeTab] ?? <Dashboard />}</div>
        </main>
      </div>
    </div>
  );
}
