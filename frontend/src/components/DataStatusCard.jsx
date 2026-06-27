import { Database, Cpu, Wifi, WifiOff, Clock } from "lucide-react";

export default function DataStatusCard({ status, isLive }) {
  const sources = status?.sources || [];
  const mlSource = sources.find((s) => s.name === "ML Model");
  const lastUpdated = status?.last_updated
    ? new Date(status.last_updated).toLocaleString()
    : "—";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <Database size={16} className="text-brand" />
          Data Source Status
        </h3>
        <span
          className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
            isLive
              ? "bg-green-50 text-green-700"
              : "bg-amber-50 text-amber-700"
          }`}
        >
          {isLive ? <Wifi size={12} /> : <WifiOff size={12} />}
          {isLive ? "Live API" : "Demo Fallback"}
        </span>
      </div>

      <ul className="space-y-2">
        {sources.map((s) => (
          <li
            key={s.name}
            className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2"
          >
            <span className="text-sm text-slate-600">{s.name}</span>
            <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium capitalize text-slate-500 ring-1 ring-slate-200">
              {s.status}
            </span>
          </li>
        ))}
        {!sources.length && (
          <li className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-700">
            Using local demo data
          </li>
        )}
      </ul>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
        <span className="flex items-center gap-1">
          <Cpu size={12} />
          ML: {mlSource ? mlSource.status : "fallback-rule"}
        </span>
        <span className="flex items-center gap-1">
          <Clock size={12} />
          Updated: {lastUpdated}
        </span>
      </div>
    </div>
  );
}
