import axios from "axios";
import { API_BASE_URL } from "../utils/constants.js";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

function unwrap(payload) {
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload;
}

function toError(error, action) {
  const detail =
    error?.response?.data?.error ||
    error?.response?.data?.detail ||
    error?.message ||
    "Unknown error";
  return new Error(`Failed to ${action}: ${detail}`);
}

export async function getHealth() {
  try {
    const res = await client.get("/api/health");
    return res.data;
  } catch (error) {
    throw toError(error, "fetch backend health");
  }
}

export async function getDataStatus() {
  try {
    const res = await client.get("/api/data/status");
    return res.data;
  } catch (error) {
    throw toError(error, "fetch data status");
  }
}

export async function getCities() {
  try {
    const res = await client.get("/api/cities");
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "fetch cities");
  }
}

export async function getHotspots(city) {
  try {
    const res = await client.get("/api/hotspots", { params: { city } });
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "fetch hotspots");
  }
}

export async function getHotspotById(zoneId) {
  try {
    const res = await client.get(`/api/hotspots/${zoneId}`);
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "fetch hotspot detail");
  }
}

export async function predictHeatRisk(payload) {
  try {
    const res = await client.post("/api/predict", payload);
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "predict heat risk");
  }
}

export async function simulateCooling(payload) {
  try {
    const res = await client.post("/api/simulate", payload);
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "run simulation");
  }
}

export async function getReport(zoneId) {
  try {
    const res = await client.get(`/api/report/${zoneId}`);
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "fetch report");
  }
}

export async function downloadReport(zoneId) {
  try {
    const res = await client.get(`/api/report/${zoneId}/download`, {
      responseType: "blob",
    });
    if (res.data?.type === "application/json") {
      throw new Error("PDF generation unavailable");
    }
    return res.data;
  } catch (error) {
    throw toError(error, "download PDF report");
  }
}


export async function getAirQuality(city) {
  try {
    const res = await client.get("/api/air-quality", { params: { city } });
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "fetch air quality");
  }
}


export async function getOptimize(city, budget = 8) {
  try {
    const res = await client.get("/api/optimize", { params: { city, budget } });
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "run optimization");
  }
}


export async function getCostAdvisor(zoneId, target = 2.0) {
  try {
    const res = await client.get("/api/cost-advisor", {
      params: { zone_id: zoneId, target },
    });
    return unwrap(res.data);
  } catch (error) {
    throw toError(error, "fetch cost advisor");
  }
}
