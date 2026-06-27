import {
  HEAT_CATEGORIES,
  PRIORITY_LEVELS,
  SIMULATION_MAX_EFFECTS,
  SIMULATION_CAP,
} from "./constants.js";

export function safeNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function formatTemperature(value) {
  return `${safeNumber(value).toFixed(1)} °C`;
}

export function getCategoryColor(category) {
  return HEAT_CATEGORIES[category] || HEAT_CATEGORIES.Moderate;
}

export function getPriorityColor(priority) {
  return PRIORITY_LEVELS[priority] || PRIORITY_LEVELS.Medium;
}

export function calculateAverageHeatScore(hotspots = []) {
  if (!hotspots.length) return 0;
  const sum = hotspots.reduce(
    (acc, h) => acc + safeNumber(h.heat_risk_score),
    0
  );
  return Math.round(sum / hotspots.length);
}

export function countSevereZones(hotspots = []) {
  return hotspots.filter((h) => h.hotspot_category === "Severe").length;
}

export function sortByPriority(hotspots = []) {
  return [...hotspots].sort(
    (a, b) => safeNumber(b.heat_risk_score) - safeNumber(a.heat_risk_score)
  );
}

/**
 * Local fallback simulation using the same transparent formula as the backend.
 */
export function localSimulation(zone, inputs) {
  const currentLst = safeNumber(zone?.lst_temperature, 42);

  const contributions = {};
  let total = 0;
  for (const key of Object.keys(SIMULATION_MAX_EFFECTS)) {
    const pct = Math.min(Math.max(safeNumber(inputs[key]), 0), 100);
    const reduction = (pct / 100) * SIMULATION_MAX_EFFECTS[key];
    contributions[key] = reduction;
    total += reduction;
  }

  const totalReduction = Math.min(total, SIMULATION_CAP);
  const newLst = currentLst - totalReduction;
  const impactScore = Math.round((totalReduction / SIMULATION_CAP) * 100);

  const labels = {
    tree_cover_increase: "Tree cover",
    cool_roof_percentage: "Cool roofs",
    green_roof_percentage: "Green roofs",
    water_body_improvement: "Water body improvement",
    high_albedo_surface: "High-albedo surfaces",
  };
  const ranked = Object.entries(contributions)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
    .map(([k]) => labels[k]);
  const strategy = ranked.length ? ranked.join(" + ") : "No intervention selected";

  const spend =
    safeNumber(inputs.tree_cover_increase) * 0.006 +
    safeNumber(inputs.cool_roof_percentage) * 0.008 +
    safeNumber(inputs.green_roof_percentage) * 0.01 +
    safeNumber(inputs.water_body_improvement) * 0.012 +
    safeNumber(inputs.high_albedo_surface) * 0.007;

  const costLevel = spend < 0.8 ? "Low" : spend < 1.8 ? "Medium" : "High";
  const feasibility = spend < 1.0 ? "High" : spend < 2.2 ? "Medium" : "Low";

  return {
    zone_id: zone?.zone_id || "unknown",
    current_lst: Number(currentLst.toFixed(2)),
    estimated_new_lst: Number(newLst.toFixed(2)),
    estimated_temp_reduction: Number(totalReduction.toFixed(2)),
    impact_score: impactScore,
    cost_level: costLevel,
    feasibility,
    recommended_strategy: strategy,
    explanation: ranked.length
      ? `Applying ${strategy.toLowerCase()} can reduce land surface temperature by about ${totalReduction.toFixed(
          2
        )} °C, lowering it from ${currentLst.toFixed(1)} °C to ${newLst.toFixed(
          1
        )} °C.`
      : "No interventions were selected, so no temperature reduction is expected.",
  };
}

/**
 * Build feature contribution values for the driver chart from a hotspot.
 */
export function buildFeatureContribution(zone) {
  if (!zone) return [];

  if (zone.feature_contribution && typeof zone.feature_contribution === "object") {
    return Object.entries(zone.feature_contribution).map(([name, value]) => ({
      name,
      value: safeNumber(value),
    }));
  }

  const ndvi = safeNumber(zone.ndvi, 0.3);
  const built = safeNumber(zone.built_up_density, 0.5);
  const lst = safeNumber(zone.lst_temperature, 38);
  const waterDist = safeNumber(zone.water_body_distance_km, 2);
  const wind = safeNumber(zone.wind_speed, 8);

  const raw = {
    "Vegetation Loss": Math.max(0, (0.6 - ndvi) / 0.6) * 100,
    "Built-up Density": built * 100,
    "Surface Temperature": Math.max(0, (lst - 28) / 20) * 100,
    "Water Distance": Math.min(1, waterDist / 5) * 100,
    "Weather Impact": Math.max(0, (12 - wind) / 12) * 100,
  };
  const total = Object.values(raw).reduce((a, b) => a + b, 0) || 1;
  return Object.entries(raw).map(([name, value]) => ({
    name,
    value: Math.round((value / total) * 100),
  }));
}
