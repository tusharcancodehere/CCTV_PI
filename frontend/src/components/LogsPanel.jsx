import React, { useRef, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { Terminal, Circle } from 'lucide-react';

const LEVEL_STYLE = {
  ERROR:   'text-red-400',
  WARNING: 'text-yellow-400',
  INFO:    'text-accent',
  DEBUG:   'text-text-dim',
};

export default function LogsPanel() {
  const { logs } = useStore();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="h-full flex flex-col p-5">
      <div className="flex items-center gap-2 mb-3 shrink-0">
        <Terminal className="w-4 h-4 text-text-muted" />
        <h2 className="text-[13px] font-semibold text-text-base">System Logs</h2>
        <span className="badge badge-blue ml-auto">{logs.length}</span>
      </div>

      <div className="flex-1 card overflow-y-auto scroll-y p-3 font-mono text-[11px] leading-relaxed space-y-px">
        {logs.length === 0 ? (
          <p className="text-text-dim text-center mt-6">Waiting for events…</p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="flex gap-3 px-2 py-1 rounded-[6px] hover:bg-surface2 transition-colors">
              <span className="text-text-dim shrink-0 whitespace-nowrap">
                {log.timestamp
                  ? new Date(log.timestamp).toLocaleTimeString()
                  : '--:--:--'}
              </span>
              <span className={`shrink-0 font-semibold w-14 ${LEVEL_STYLE[log.level?.toUpperCase()] ?? 'text-text-muted'}`}>
                {log.level ?? 'INFO'}
              </span>
              <span className="text-text-muted break-all">{log.message}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
