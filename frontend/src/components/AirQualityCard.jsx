import { useEffect, useState } from "react";
import { Wind, Loader2 } from "lucide-react";
import { getAirQuality } from "../api/api.js";
import { getDemoAirQuality } from "../data/demoData.js";

const AQI_COLORS = {
  Good: { bg: "#dcfce7", text: "#166534", bar: "#16a34a" },
  Satisfactory: { bg: "#ecfccb", text: "#3f6212", bar: "#65a30d" },
  Moderate: { bg: "#fef9c3", text: "#854d0e", bar: "#eab308" },
  Poor: { bg: "#ffedd5", text: "#9a3412", bar: "#f97316" },
  "Very Poor": { bg: "#fee2e2", text: "#991b1b", bar: "#dc2626" },
  Severe: { bg: "#fae8ff", text: "#86198f", bar: "#a21caf" },
};

export default function AirQualityCard({ city }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getAirQuality(city)
      .then((d) => active && setData(d))
      .catch(() => active && setData(getDemoAirQuality(city)))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [city]);

  const color = data ? AQI_COLORS[data.category] || AQI_COLORS.Moderate : AQI_COLORS.Moderate;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <Wind size={16} className="text-brand" />
          Air Quality Index
        </h3>
        {data && (
          <span
            className="rounded-full px-2.5 py-1 text-xs font-semibold"
            style={{ backgroundColor: color.bg, color: color.text }}
          >
            {data.source === "data.gov.in" ? "Live (CPCB)" : "Demo"}
          </span>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center gap-2 py-6 text-slate-400">
          <Loader2 size={18} className="animate-spin" /> Loading air quality...
        </div>
      ) : data ? (
        <>
          <div className="flex items-end gap-3">
            <span className="text-4xl font-bold" style={{ color: color.bar }}>
              {data.aqi}
            </span>
            <div className="pb-1">
              <p className="text-sm font-semibold" style={{ color: color.text }}>
                {data.category}
              </p>
              <p className="text-xs text-slate-400">
                Dominant: {data.dominant_pollutant}
              </p>
            </div>
          </div>

          <div className="mt-2 h-2 w-full rounded-full bg-slate-100">
            <div
              className="h-2 rounded-full"
              style={{
                width: `${Math.min((data.aqi / 500) * 100, 100)}%`,
                backgroundColor: color.bar,
              }}
            />
          </div>

          <div className="mt-3 grid grid-cols-3 gap-1.5">
            {Object.entries(data.pollutants || {}).map(([name, value]) => (
              <div key={name} className="rounded-lg bg-slate-50 px-2 py-1 text-center">
                <p className="text-[10px] uppercase text-slate-400">{name}</p>
                <p className="text-sm font-semibold text-slate-700">{value}</p>
              </div>
            ))}
          </div>

          <p className="mt-2 text-[11px] text-slate-400">
            {data.city} · {data.stations_count} station(s) · source: {data.source}
          </p>
        </>
      ) : (
        <p className="py-6 text-center text-sm text-slate-400">No air quality data.</p>
      )}
    </div>
  );
}
