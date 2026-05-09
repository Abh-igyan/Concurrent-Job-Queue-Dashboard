import type { EventRecord } from "../types/metrics";

export function EventLog({ events }: { events: EventRecord[] }) {
  return (
    <section className="rounded-md border border-border bg-panel/90 p-4">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-300">Live event stream</h2>
      <div className="max-h-[420px] space-y-2 overflow-y-auto pr-1">
        {events.map((event, index) => (
          <div key={`${event.timestamp}-${index}`} className="rounded-md border border-border bg-slate-950/40 p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="font-mono text-xs text-accent">{event.type}</span>
              <span className="font-mono text-xs text-slate-600">
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-300">{event.message}</p>
            <pre className="mt-2 overflow-x-auto text-xs text-slate-500">
              {JSON.stringify(event.payload)}
            </pre>
          </div>
        ))}
      </div>
    </section>
  );
}
