import { useEffect, useMemo, useState } from "react";
import { Thermometer, TrendingDown, Gauge, Wallet, CheckCircle2, AlertCircle, SlidersHorizontal } from "lucide-react";
import { simulateCooling, getHotspots } from "../api/api.js";
import { getDemoHotspots } from "../data/demoData.js";
import { DEFAULT_CITY, CITY_CENTERS } from "../utils/constants.js";
import { localSimulation, formatTemperature, safeNumber } from "../utils/helpers.js";
import SimulatorForm from "../components/SimulatorForm.jsx";

const INITIAL_INPUTS = {
  tree_cover_increase: 25,
  cool_roof_percentage: 40,
  green_roof_percentage: 10,
  water_body_improvement: 5,
  high_albedo_surface: 20,
};

function ResultMetric({ icon: Icon, label, value, accent = "text-slate-700" }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="flex items-center gap-1.5 text-xs text-slate-400">
        <Icon size={14} /> {label}
      </p>
      <p className={`mt-1 text-lg font-bold ${accent}`}>{value}</p>
    </div>
  );
}

export default function Simulator() {
  const [city, setCity] = useState(DEFAULT_CITY);
  const [zones, setZones] = useState(getDemoHotspots(DEFAULT_CITY));
  const [zoneId, setZoneId] = useState(zones[0]?.zone_id || "");
  const [inputs, setInputs] = useState(INITIAL_INPUTS);
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [usedFallback, setUsedFallback] = useState(false);

  useEffect(() => {
    let active = true;
    const safeCity = CITY_CENTERS[city] ? city : DEFAULT_CITY;
    setResult(null);
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

  async function runSimulation() {
    if (!zone) return;
    setRunning(true);
    setUsedFallback(false);
    const payload = { zone_id: zone.zone_id, ...inputs };

    try {
      const data = await simulateCooling(payload);
      setResult(data);
    } catch {
      setResult(localSimulation(zone, inputs));
      setUsedFallback(true);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="bg-slate-50">
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-brand">
              <SlidersHorizontal size={20} />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-800">Cooling Simulator</h1>
              <p className="text-sm text-slate-500">
                Test cooling interventions and estimate temperature reduction for a zone.
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
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
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
        <div className="grid gap-5 lg:grid-cols-2">
          {/* Left: zone details + form */}
          <div className="space-y-5">
            {zone && (
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-700">
                  Current Zone Conditions — {zone.zone_name}
                </h3>
                <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
                  <ResultMetric icon={Thermometer} label="Current LST" value={formatTemperature(zone.lst_temperature)} accent="text-red-600" />
                  <ResultMetric icon={Gauge} label="Heat Score" value={safeNumber(zone.heat_risk_score)} />
                  <ResultMetric icon={TrendingDown} label="Green Cover" value={`${safeNumber(zone.green_cover_percentage)}%`} />
                </div>
              </div>
            )}

            <SimulatorForm
              values={inputs}
              onChange={setInputs}
              onRun={runSimulation}
              running={running}
            />
          </div>

          {/* Right: result */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700">Simulation Result</h3>

            {usedFallback && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                <AlertCircle size={14} />
                Backend simulation unavailable — computed locally.
              </div>
            )}

            {result ? (
              <>
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <ResultMetric icon={Thermometer} label="Current LST" value={formatTemperature(result.current_lst)} />
                  <ResultMetric icon={Thermometer} label="Estimated New LST" value={formatTemperature(result.estimated_new_lst)} accent="text-teal-600" />
                  <ResultMetric icon={TrendingDown} label="Temp Reduction" value={formatTemperature(result.estimated_temp_reduction)} accent="text-teal-700" />
                  <ResultMetric icon={Gauge} label="Impact Score" value={`${safeNumber(result.impact_score)}/100`} />
                  <ResultMetric icon={Wallet} label="Cost Level" value={result.cost_level} />
                  <ResultMetric icon={CheckCircle2} label="Feasibility" value={result.feasibility} />
                </div>

                <div className="mt-4 rounded-lg border border-teal-100 bg-teal-50 p-3">
                  <p className="text-xs font-semibold text-teal-800">
                    Recommended Strategy
                  </p>
                  <p className="text-sm font-medium text-teal-900">
                    {result.recommended_strategy}
                  </p>
                  <p className="mt-2 text-sm text-teal-800">{result.explanation}</p>
                </div>
              </>
            ) : (
              <div className="mt-6 rounded-lg border border-dashed border-slate-200 p-8 text-center text-sm text-slate-400">
                Adjust the interventions and run a simulation to see results.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
