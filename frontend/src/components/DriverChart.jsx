import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid,
} from "recharts";
import { buildFeatureContribution } from "../utils/helpers.js";

const COLORS = ["#0d9488", "#0ea5e9", "#f97316", "#6366f1", "#f59e0b"];

export default function DriverChart({ hotspot }) {
  const data = buildFeatureContribution(hotspot);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700">
        Heat Driver Analysis
        {hotspot ? (
          <span className="ml-1 font-normal text-slate-400">
            — {hotspot.zone_name}
          </span>
        ) : null}
      </h3>
      <p className="mb-3 text-xs text-slate-400">
        Relative contribution of each factor to heat risk (%)
      </p>

      {data.length ? (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: "#64748b" }}
                angle={-20}
                textAnchor="end"
                interval={0}
              />
              <YAxis tick={{ fontSize: 11, fill: "#64748b" }} unit="%" />
              <Tooltip
                formatter={(v) => [`${v}%`, "Contribution"]}
                contentStyle={{ borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="py-10 text-center text-sm text-slate-400">
          No driver data available.
        </p>
      )}
    </div>
  );
}
