import { sortByPriority, getCategoryColor, getPriorityColor, formatTemperature } from "../utils/helpers.js";

export default function PriorityTable({ hotspots = [], onSelect }) {
  const rows = sortByPriority(hotspots);

  if (!rows.length) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-400 shadow-sm">
        No hotspot data to rank.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-3">
        <h3 className="text-sm font-semibold text-slate-700">
          Priority Ranking
        </h3>
        <p className="text-xs text-slate-400">Zones sorted by heat risk score</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3">Zone</th>
              <th className="px-4 py-3">Heat Score</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Main Cause</th>
              <th className="px-4 py-3 hidden lg:table-cell">Recommended Action</th>
              <th className="px-4 py-3">Cooling</th>
              <th className="px-4 py-3">Priority</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((h) => {
              const cat = getCategoryColor(h.hotspot_category);
              const pri = getPriorityColor(h.priority_level);
              return (
                <tr
                  key={h.zone_id}
                  className="cursor-pointer transition hover:bg-slate-50"
                  onClick={() => onSelect && onSelect(h)}
                >
                  <td className="px-4 py-3 font-medium text-slate-700">
                    {h.zone_name}
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-700">
                    {h.heat_risk_score}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="rounded-full px-2.5 py-1 text-xs font-semibold"
                      style={{ backgroundColor: cat.bg, color: cat.text }}
                    >
                      {h.hotspot_category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {(h.main_drivers && h.main_drivers[0]) || "—"}
                  </td>
                  <td className="px-4 py-3 hidden max-w-xs truncate text-slate-500 lg:table-cell">
                    {h.recommended_action}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {formatTemperature(h.expected_temp_reduction)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="rounded-full px-2.5 py-1 text-xs font-semibold"
                      style={{ backgroundColor: pri.bg, color: pri.text }}
                    >
                      {h.priority_level}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
