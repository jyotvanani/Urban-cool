import { useEffect, useState } from "react";
import { Sparkles, Target, TrendingDown, Layers, Wallet, AlertCircle } from "lucide-react";
import { getOptimize } from "../api/api.js";
import { DEFAULT_CITY, CITY_CENTERS } from "../utils/constants.js";
import { getCategoryColor, formatTemperature } from "../utils/helpers.js";
import StatCard from "../components/StatCard.jsx";
import LoadingState from "../components/LoadingState.jsx";

export default function Optimize() {
  const [city, setCity] = useState(DEFAULT_CITY);
  const [budget, setBudget] = useState(8);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run(c = city, b = budget) {
    setLoading(true);
    setError("");
    try {
      const result = await getOptimize(c, b);
      setData(result);
    } catch {
      setError("Backend unavailable — could not run optimization.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    run(city, budget);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city]);

  const safeCity = CITY_CENTERS[city] ? city : DEFAULT_CITY;

  return (
    <div className="bg-slate-50">
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-brand">
              <Sparkles size={20} />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-800">Cooling Optimizer</h1>
              <p className="text-sm text-slate-500">
                Find the highest-impact zones and the best interventions to maximize city-wide cooling.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-slate-600">City</label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            >
              <option value="ahmedabad">Ahmedabad</option>
              <option value="surat">Surat</option>
            </select>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Budget control */}
        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex-1 min-w-[260px]">
              <div className="mb-1 flex items-center justify-between text-sm">
                <label className="font-medium text-slate-600">
                  Budget — number of priority zones to treat
                </label>
                <span className="font-semibold text-slate-700">{budget} zones</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full accent-teal-600"
              />
            </div>
            <button
              onClick={() => run(safeCity, budget)}
              className="flex items-center gap-2 rounded-lg bg-brand px-5 py-2.5 font-medium text-white transition hover:bg-brand-dark"
            >
              <Target size={16} /> Optimize
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {loading ? (
          <LoadingState label="Optimizing cooling plan..." />
        ) : data ? (
          <div className="space-y-6">
            {/* Summary stats */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard title="Zones Treated" value={data.zones_treated} subtitle="Priority selection" icon={Layers} accent="blue" />
              <StatCard title="Total Cooling" value={formatTemperature(data.total_expected_reduction)} subtitle="Combined reduction" icon={TrendingDown} accent="green" />
              <StatCard title="Avg per Zone" value={formatTemperature(data.average_reduction)} subtitle="Mean reduction" icon={Target} accent="orange" />
              <StatCard title="Overall Cost" value={data.overall_cost_level} subtitle="Investment level" icon={Wallet} accent="red" />
            </div>

            <div className="rounded-lg border border-teal-100 bg-teal-50 p-4 text-sm text-teal-900">
              {data.summary}
            </div>

            {/* Plan table */}
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 px-5 py-3">
                <h3 className="text-sm font-semibold text-slate-700">Optimized Action Plan</h3>
                <p className="text-xs text-slate-400">Ranked by priority, with the recommended intervention mix per zone</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-400">
                    <tr>
                      <th className="px-4 py-3">#</th>
                      <th className="px-4 py-3">Zone</th>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Current LST</th>
                      <th className="px-4 py-3">New LST</th>
                      <th className="px-4 py-3">Reduction</th>
                      <th className="px-4 py-3">Strategy</th>
                      <th className="px-4 py-3">Cost</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.plan.map((p, i) => {
                      const cat = getCategoryColor(p.hotspot_category);
                      return (
                        <tr key={p.zone_id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-semibold text-slate-400">{i + 1}</td>
                          <td className="px-4 py-3 font-medium text-slate-700">{p.zone_name}</td>
                          <td className="px-4 py-3">
                            <span className="rounded-full px-2.5 py-1 text-xs font-semibold" style={{ backgroundColor: cat.bg, color: cat.text }}>
                              {p.hotspot_category}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-600">{formatTemperature(p.current_lst)}</td>
                          <td className="px-4 py-3 font-medium text-teal-700">{formatTemperature(p.estimated_new_lst)}</td>
                          <td className="px-4 py-3 font-semibold text-teal-700">-{p.estimated_temp_reduction} °C</td>
                          <td className="px-4 py-3 text-slate-500">{p.recommended_strategy}</td>
                          <td className="px-4 py-3 text-slate-600">{p.cost_level}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-200 bg-white p-10 text-center text-sm text-slate-400">
            Set a budget and click <b className="mx-1">Optimize</b> to generate a plan.
          </div>
        )}
      </div>
    </div>
  );
}
