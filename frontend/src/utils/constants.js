export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const DEFAULT_CITY = "ahmedabad";

export const CITY_CENTERS = {
  ahmedabad: { name: "Ahmedabad", lat: 23.0225, lng: 72.5714, zoom: 12 },
  surat: { name: "Surat", lat: 21.1702, lng: 72.8311, zoom: 12 },
};

export const HEAT_CATEGORIES = {
  Low: { color: "#16a34a", bg: "#dcfce7", text: "#166534" },
  Moderate: { color: "#eab308", bg: "#fef9c3", text: "#854d0e" },
  High: { color: "#f97316", bg: "#ffedd5", text: "#9a3412" },
  Severe: { color: "#dc2626", bg: "#fee2e2", text: "#991b1b" },
};

export const PRIORITY_LEVELS = {
  Low: { color: "#16a34a", bg: "#dcfce7", text: "#166534" },
  Medium: { color: "#eab308", bg: "#fef9c3", text: "#854d0e" },
  High: { color: "#f97316", bg: "#ffedd5", text: "#9a3412" },
  Critical: { color: "#dc2626", bg: "#fee2e2", text: "#991b1b" },
};

export const SIMULATION_MAX_EFFECTS = {
  tree_cover_increase: 1.5,
  cool_roof_percentage: 1.2,
  green_roof_percentage: 0.8,
  water_body_improvement: 0.7,
  high_albedo_surface: 0.9,
};

export const SIMULATION_CAP = 4.0;
