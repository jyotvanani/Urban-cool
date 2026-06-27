import { useEffect, useState } from "react";
import { Flame, AlertTriangle, Gauge, Leaf, AlertCircle, MapPinned } from "lucide-react";
import { getDataStatus, getHotspots } from "../api/api.js";
import { demoDataStatus, getDemoHotspots } from "../data/demoData.js";
import { DEFAULT_CITY, CITY_CENTERS } from "../utils/constants.js";
import {
  calculateAverageHeatScore,
  countSevereZones,
  sortByPriority,
  formatTemperature,
} from "../utils/helpers.js";
import StatCard from "../components/StatCard.jsx";
import DataStatusCard from "../components/DataStatusCard.jsx";
import HeatMap from "../components/HeatMap.jsx";
import HotspotPanel from "../components/HotspotPanel.jsx";
import DriverChart from "../components/DriverChart.jsx";
import PriorityTable from "../components/PriorityTable.jsx";
import LoadingState from "../components/LoadingState.jsx";
import AirQualityCard from "../components/AirQualityCard.jsx";

function SectionHeader({ title, subtitle }) {
  return (
    <div className="mb-3 flex items-center gap-3">
      <div className="h-5 w-1 rounded-full bg-brand" />
      <div>
        <h2 className="text-base font-semibold text-slate-800">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [city, setCity] = useState(DEFAULT_CITY);
  const [hotspots, setHotspots] = useState([]);
  const [status, setStatus] = useState(null);
  const [selected, setSelected] = useState(null);
  const [isLive, setIsLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [warning, setWarning] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setWarning("");
      const safeCity = CITY_CENTERS[city] ? city : DEFAULT_CITY;

      let live = true;
      let nextHotspots = [];
      let nextStatus = null;

      try {
        nextHotspots = await getHotspots(safeCity);
      } catch {
        live = false;
        nextHotspots = getDemoHotspots(safeCity);
      }

      try {
        nextStatus = await getDataStatus();
      } catch {
        live = false;
        nextStatus = demoDataStatus;
      }

      if (!nextHotspots || !nextHotspots.length) {
        nextHotspots = getDemoHotspots(safeCity);
        live = false;
      }

      if (!active) return;
      setHotspots(nextHotspots);
      setStatus(nextStatus);
      setIsLive(live);
      setSelected(sortByPriority(nextHotspots)[0] || null);
      if (!live) {
        setWarning("Backend unavailable — showing local demo data.");
      }
      setLoading(false);
    }

    load();
    return () => {
      active = false;
    };
  }, [city]);

  const avgScore = calculateAverageHeatScore(hotspots);
  const severeCount = countSevereZones(hotspots);
  const bestPotential = hotspots.length
    ? sortByPriority(hotspots).reduce((best, h) =>
        (h.expected_temp_reduction || 0) > (best.expected_temp_reduction || 0)
          ? h
          : best
      )
    : null;
  const safeCity = CITY_CENTERS[city] ? city : DEFAULT_CITY;

  return (
    <div className="bg-slate-50">
      {/* Page header band */}
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-brand">
              <MapPinned size={20} />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-800">Heat Risk Dashboard</h1>
              <p className="text-sm text-slate-500">
                Detect and prioritize urban heat hotspots across the city.
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
        {warning && (
          <div className="mb-6 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
            <AlertCircle size={16} />
            {warning}
          </div>
        )}

        {loading ? (
          <LoadingState label="Loading hotspot data..." />
        ) : (
          <div className="space-y-8">
            {/* Overview stats */}
            <section>
              <SectionHeader title="Overview" subtitle="Key metrics for the selected city" />
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard title="Total Hotspots" value={hotspots.length} subtitle="Monitored zones" icon={Flame} accent="blue" />
                <StatCard title="Severe Zones" value={severeCount} subtitle="Need urgent action" icon={AlertTriangle} accent="red" />
                <StatCard title="Avg Heat Score" value={avgScore} subtitle="0–100 scale" icon={Gauge} accent="orange" />
                <StatCard
                  title="Best Cooling Potential"
                  value={bestPotential ? formatTemperature(bestPotential.expected_temp_reduction) : "—"}
                  subtitle={bestPotential ? bestPotential.zone_name : "—"}
                  icon={Leaf}
                  accent="green"
                />
              </div>
            </section>

            {/* Map + context cards */}
            <section>
              <SectionHeader title="Hotspot Map" subtitle="Click any marker to inspect a zone" />
              <div className="grid gap-5 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <HeatMap hotspots={hotspots} city={safeCity} selected={selected} onSelect={setSelected} />
                </div>
                <div className="space-y-5">
                  <DataStatusCard status={status} isLive={isLive} />
                  <AirQualityCard city={safeCity} />
                </div>
              </div>
            </section>

            {/* Selected zone analysis */}
            <section>
              <SectionHeader
                title="Selected Zone Analysis"
                subtitle={selected ? selected.zone_name : "Select a zone on the map"}
              />
              <div className="grid gap-5 lg:grid-cols-2">
                <HotspotPanel hotspot={selected} />
                <DriverChart hotspot={selected} />
              </div>
            </section>

            {/* Priority ranking */}
            <section>
              <SectionHeader title="Priority Ranking" subtitle="Zones ranked by heat risk score" />
              <PriorityTable hotspots={hotspots} onSelect={setSelected} />
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
