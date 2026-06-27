import { MapPin, Thermometer, Leaf, Droplets } from "lucide-react";
import { getCategoryColor, formatTemperature, safeNumber } from "../utils/helpers.js";

function Metric({ label, value }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-slate-700">{value}</p>
    </div>
  );
}

export default function HotspotPanel({ hotspot }) {
  if (!hotspot) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-400 shadow-sm">
        Select a zone on the map to view details.
      </div>
    );
  }

  const cat = getCategoryColor(hotspot.hotspot_category);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="flex items-center gap-1.5 text-lg font-bold text-slate-800">
            <MapPin size={18} className="text-brand" />
            {hotspot.zone_name}
          </h3>
          <p className="text-sm capitalize text-slate-400">{hotspot.city}</p>
        </div>
        <span
          className="rounded-full px-3 py-1 text-xs font-semibold"
          style={{ backgroundColor: cat.bg, color: cat.text }}
        >
          {hotspot.hotspot_category}
        </span>
      </div>

      <div className="mt-4 flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2">
          <Thermometer size={18} className="text-red-600" />
          <div>
            <p className="text-xs text-slate-400">LST</p>
            <p className="text-sm font-bold text-red-700">
              {formatTemperature(hotspot.lst_temperature)}
            </p>
          </div>
        </div>
        <div className="flex-1">
          <p className="text-xs text-slate-400">Heat Risk Score</p>
          <div className="mt-1 flex items-center gap-2">
            <div className="h-2 flex-1 rounded-full bg-slate-100">
              <div
                className="h-2 rounded-full"
                style={{
                  width: `${safeNumber(hotspot.heat_risk_score)}%`,
                  backgroundColor: cat.color,
                }}
              />
            </div>
            <span className="text-sm font-bold text-slate-700">
              {safeNumber(hotspot.heat_risk_score)}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
        <Metric label="NDVI" value={safeNumber(hotspot.ndvi).toFixed(2)} />
        <Metric label="NDBI" value={safeNumber(hotspot.ndbi).toFixed(2)} />
        <Metric label="Built-up" value={safeNumber(hotspot.built_up_density).toFixed(2)} />
        <Metric label="Green Cover" value={`${safeNumber(hotspot.green_cover_percentage)}%`} />
        <Metric label="Water Dist." value={`${safeNumber(hotspot.water_body_distance_km)} km`} />
        <Metric label="Humidity" value={`${safeNumber(hotspot.humidity)}%`} />
      </div>

      <div className="mt-4">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Main Drivers
        </p>
        <div className="flex flex-wrap gap-1.5">
          {(hotspot.main_drivers || []).map((d) => (
            <span
              key={d}
              className="rounded-full bg-orange-50 px-2.5 py-1 text-xs font-medium text-orange-700"
            >
              {d}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-teal-100 bg-teal-50 p-3">
        <p className="flex items-center gap-1.5 text-xs font-semibold text-teal-800">
          <Leaf size={14} /> Recommended Action
        </p>
        <p className="mt-1 text-sm text-teal-900">{hotspot.recommended_action}</p>
        <p className="mt-2 flex items-center gap-1.5 text-xs font-medium text-teal-700">
          <Droplets size={14} />
          Expected reduction: {formatTemperature(hotspot.expected_temp_reduction)}
        </p>
      </div>
    </div>
  );
}
