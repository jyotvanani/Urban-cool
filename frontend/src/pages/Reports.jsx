import { useEffect, useMemo, useState } from "react";
import { FileText, Download, AlertCircle, CheckCircle2 } from "lucide-react";
import { getReport, downloadReport, getHotspots } from "../api/api.js";
import { getDemoHotspots, buildDemoReport } from "../data/demoData.js";
import { DEFAULT_CITY, CITY_CENTERS } from "../utils/constants.js";
import {
  getCategoryColor,
  getPriorityColor,
  formatTemperature,
} from "../utils/helpers.js";
import LoadingState from "../components/LoadingState.jsx";

export default function Reports() {
  const [city, setCity] = useState(DEFAULT_CITY);
  const [zones, setZones] = useState(getDemoHotspots(DEFAULT_CITY));
  const [zoneId, setZoneId] = useState(zones[0]?.zone_id || "");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");

  useEffect(() => {
    let active = true;
    const safeCity = CITY_CENTERS[city] ? city : DEFAULT_CITY;
    setReport(null);
    setMessage("");
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

  async function generateReport() {
    if (!zone) return;
    setLoading(true);
    setMessage("");
    try {
      const data = await getReport(zone.zone_id);
      setReport(data);
      setMessage("Report generated from backend.");
      setMessageType("success");
    } catch {
      setReport(buildDemoReport(zone));
      setMessage("Backend unavailable — showing demo report preview.");
      setMessageType("info");
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload() {
    if (!zone) return;
    setMessage("");
    try {
      const blob = await downloadReport(zone.zone_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `UrbanCool_Report_${zone.zone_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setMessage("PDF downloaded successfully.");
      setMessageType("success");
    } catch {
      if (!report) setReport(buildDemoReport(zone));
      setMessage(
        "Backend PDF generation unavailable. Showing report preview instead."
      );
      setMessageType("info");
    }
  }

  const cat = report ? getCategoryColor(report.heat_condition?.hotspot_category) : null;
  const pri = report ? getPriorityColor(report.priority_level) : null;

  return (
    <div className="bg-slate-50">
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-brand">
              <FileText size={20} />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-800">Reports</h1>
              <p className="text-sm text-slate-500">
                Generate planner-ready heat mitigation reports for any zone.
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

      <div className="mx-auto max-w-5xl px-4 py-6">
        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={generateReport}
            className="flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-dark"
          >
            <FileText size={16} /> Generate Report
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
          >
            <Download size={16} /> Download PDF
          </button>
        </div>

        {message && (
          <div
            className={`mt-4 flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm ${
              messageType === "success"
                ? "border-green-200 bg-green-50 text-green-800"
                : "border-amber-200 bg-amber-50 text-amber-800"
            }`}
          >
            {messageType === "success" ? (
              <CheckCircle2 size={16} />
            ) : (
              <AlertCircle size={16} />
            )}
            {message}
          </div>
        )}

        {/* Report preview */}
        <div className="mt-6">
        {loading ? (
          <LoadingState label="Generating report..." />
        ) : report ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-800">
                  {report.zone_summary?.zone_name}
                </h2>
                <p className="text-sm capitalize text-slate-400">
                  {report.zone_summary?.city} · Zone {report.zone_summary?.zone_id}
                </p>
              </div>
              <div className="flex gap-2">
                {cat && (
                  <span
                    className="rounded-full px-3 py-1 text-xs font-semibold"
                    style={{ backgroundColor: cat.bg, color: cat.text }}
                  >
                    {report.heat_condition?.hotspot_category}
                  </span>
                )}
                {pri && (
                  <span
                    className="rounded-full px-3 py-1 text-xs font-semibold"
                    style={{ backgroundColor: pri.bg, color: pri.text }}
                  >
                    {report.priority_level} priority
                  </span>
                )}
              </div>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Heat Condition
                </h3>
                <ul className="mt-2 space-y-1 text-sm text-slate-600">
                  <li>Heat Risk Score: <b>{report.heat_condition?.heat_risk_score}</b></li>
                  <li>LST: <b>{formatTemperature(report.heat_condition?.lst_temperature)}</b></li>
                  <li>Air Temp: <b>{formatTemperature(report.heat_condition?.air_temperature)}</b></li>
                  <li>Humidity: <b>{report.heat_condition?.humidity}%</b></li>
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Main Causes
                </h3>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {(report.main_causes || []).map((c) => (
                    <span
                      key={c}
                      className="rounded-full bg-orange-50 px-2.5 py-1 text-xs font-medium text-orange-700"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-4 rounded-lg border border-teal-100 bg-teal-50 p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-teal-700">
                Recommended Actions
              </h3>
              <p className="mt-1 text-sm text-teal-900">
                {report.recommended_actions}
              </p>
              <p className="mt-2 text-sm font-medium text-teal-800">
                Expected reduction:{" "}
                {formatTemperature(report.expected_temperature_reduction)}
              </p>
            </div>

            <div className="mt-4">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Implementation Suggestions
              </h3>
              <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-600">
                {(report.implementation_suggestions || []).map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-200 bg-white p-10 text-center text-sm text-slate-400">
            Select a zone and click <b className="mx-1">Generate Report</b> to
            preview it here.
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
