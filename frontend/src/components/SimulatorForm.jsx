import { Play } from "lucide-react";

const FIELDS = [
  { key: "tree_cover_increase", label: "Tree Cover Increase", max: 1.5 },
  { key: "cool_roof_percentage", label: "Cool Roof Coverage", max: 1.2 },
  { key: "green_roof_percentage", label: "Green Roof Coverage", max: 0.8 },
  { key: "water_body_improvement", label: "Water Body Improvement", max: 0.7 },
  { key: "high_albedo_surface", label: "High-Albedo Surface", max: 0.9 },
];

export default function SimulatorForm({ values, onChange, onRun, running }) {
  const update = (key, value) =>
    onChange({ ...values, [key]: Number(value) });

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700">Cooling Interventions</h3>
      <p className="mb-4 text-xs text-slate-400">
        Adjust each intervention (% of zone area). Max cooling per lever shown on
        the right.
      </p>

      <div className="space-y-4">
        {FIELDS.map((f) => (
          <div key={f.key}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <label className="font-medium text-slate-600">{f.label}</label>
              <span className="text-slate-500">
                {values[f.key] || 0}%
                <span className="ml-1 text-xs text-slate-400">
                  (≤ {f.max}°C)
                </span>
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={values[f.key] || 0}
              onChange={(e) => update(f.key, e.target.value)}
              className="w-full accent-teal-600"
            />
          </div>
        ))}
      </div>

      <button
        onClick={onRun}
        disabled={running}
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-brand px-4 py-2.5 font-medium text-white transition hover:bg-brand-dark disabled:opacity-60"
      >
        <Play size={16} />
        {running ? "Running..." : "Run Simulation"}
      </button>
    </div>
  );
}
