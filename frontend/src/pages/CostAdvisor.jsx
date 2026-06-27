import { useEffect, useMemo, useState } from "react";
import { IndianRupee, Target, TrendingDown, PiggyBank, Lightbulb, AlertCircle } from "lucide-react";
import { getHotspots, getCostAdvisor } from "../api/api.js";
import { getDemoHotspots } from "../data/demoData.js";
import { DEFAULT_CITY, CITY_CENTERS } from "../utils/constants.js";
import { formatTemperature } from "../utils/helpers.js";
import StatCard from "../components/StatCard.jsx";
import LoadingState from "../components/LoadingState.jsx";

export default function CostAdvisor() {
  const [city, setCity] = useState(DEFAULT_CITY);
  const [zones, setZones] = useState(getDemoHotspots(DEFAULT_CITY));
  const [zoneId, setZoneId] = useState(zones[0]?.zone_id || "");
  const [target, setTarget] = useState(2.0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const safeCity = CITY_CENTERS[city] ? city : DEFAULT_CITY;
    getHotspots(safeCity)
      .then((list) => {
        if (!active) return;
        const l = list && list.length ? list : getDemoHotspots(safeCity);
        setZones(l);
        setZoneId(l[0]?.zone_id || "");
      })
      .catch(() => {
        if (!active) return;
        const l = getDemoHotspots(safeCity);
        setZones(l);
        setZoneId(l[0]?.zone_id || "");
      });
    return () => {
      active = false;
    };
  }, [city]);

  const zone = useMemo(
    () => zones.find((z) => z.zone_id === zoneId) || zones[0] || null,
    [zones, zoneId]
  );

  async function run() {
    if (!zone) return;
    setLoading(true);
    setError("");
    try {
      setData(await getCostAdvisor(zone.zone_id, target));
    } catch {
      setError("Backend unavailable — could not compute cost plan.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (zone) run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoneId]);

  return (
    <div className="bg-slate-50">
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-brand">
              <IndianRupee size={20} />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-800">Cost Advisor</h1>
              <p className="text-sm text-slate-500">
                See what cooling costs and the cheapest, highest-impact way to achieve it.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
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
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-slate-600">Zone</label>
              <select
                value={zoneId}
                onChange={(e) => setZoneId(e.target.value)}
                className="max-w-[200px] rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              >
                {zones.map((z) => (
                  <option key={z.zone_id} value={z.zone_id}>
                    {z.zone_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Target control */}
        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex-1 min-w-[260px]">
              <div className="mb-1 flex items-center justify-between text-sm">
                <label className="font-medium text-slate-600">Target temperature reduction</label>
                <span className="font-semibold text-slate-700">{target.toFixed(1)} °C</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="4"
                step="0.1"
                value={target}
                onChange={(e) => setTarget(Number(e.target.value))}
                className="w-full accent-teal-600"
              />
            </div>
            <button
              onClick={run}
              className="flex items-center gap-2 rounded-lg bg-brand px-5 py-2.5 font-medium text-white transition hover:bg-brand-dark"
            >
              <Target size={16} /> Calculate Cost
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {loading ? (
          <LoadingState label="Calculating cost plan..." />
        ) : data ? (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard title="Target Cooling" value={formatTemperature(data.target_reduction)} subtitle={data.zone_name} icon={Target} accent="orange" />
              <StatCard title="Optimised Cost" value={`₹${data.total_cost_lakh}L`} subtitle="Minimum-cost plan" icon={IndianRupee} accent="green" />
              <StatCard title="Naive Cost" value={`₹${data.naive_cost_lakh}L`} subtitle="Least-efficient method" icon={TrendingDown} accent="red" />
              <StatCard title="You Save" value={`${data.savings_pct}%`} subtitle={`₹${data.savings_lakh}L cheaper`} icon={PiggyBank} accent="blue" />
            </div>

            <div className="flex items-start gap-2 rounded-lg border border-teal-100 bg-teal-50 p-4 text-sm text-teal-900">
              <Lightbulb size={18} className="mt-0.5 shrink-0 text-teal-700" />
              <span>{data.tip}</span>
            </div>

            <div className="grid gap-5 lg:grid-cols-2">
              {/* Minimum-cost plan */}
              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 px-5 py-3">
                  <h3 className="text-sm font-semibold text-slate-700">Recommended Low-Cost Plan</h3>
                  <p className="text-xs text-slate-400">
                    Reaches {formatTemperature(data.achieved_reduction)} for ₹{data.total_cost_lakh} lakh
                  </p>
                </div>
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-400">
                    <tr>
                      <th className="px-4 py-2">Method</th>
                      <th className="px-4 py-2">Coverage</th>
                      <th className="px-4 py-2">Cooling</th>
                      <th className="px-4 py-2">Cost</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.plan.map((p) => (
                      <tr key={p.key}>
                        <td className="px-4 py-2 font-medium text-slate-700">{p.method}</td>
                        <td className="px-4 py-2 text-slate-600">{p.coverage_pct}%</td>
                        <td className="px-4 py-2 text-teal-700">-{p.cooling} °C</td>
                        <td className="px-4 py-2 text-slate-600">₹{p.cost_lakh}L</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Efficiency ranking */}
              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 px-5 py-3">
                  <h3 className="text-sm font-semibold text-slate-700">Cost-Effectiveness of Methods</h3>
                  <p className="text-xs text-slate-400">Cooling per ₹ lakh — higher is better value</p>
                </div>
                <div className="space-y-3 p-4">
                  {data.efficiency_ranking.map((m) => {
                    const max = data.efficiency_ranking[0].cooling_per_lakh || 1;
                    const pct = Math.round((m.cooling_per_lakh / max) * 100);
                    return (
                      <div key={m.key}>
                        <div className="mb-1 flex items-center justify-between text-xs">
                          <span className="font-medium text-slate-600">{m.method}</span>
                          <span className="text-slate-400">{m.cooling_per_lakh.toFixed(3)} °C/₹L</span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100">
                          <div className="h-2 rounded-full bg-teal-500" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-200 bg-white p-10 text-center text-sm text-slate-400">
            Choose a zone and target, then click <b className="mx-1">Calculate Cost</b>.
          </div>
        )}
      </div>
    </div>
  );
}
