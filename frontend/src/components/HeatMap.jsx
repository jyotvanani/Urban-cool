import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";
import { CITY_CENTERS } from "../utils/constants.js";
import { getCategoryColor, formatTemperature, safeNumber } from "../utils/helpers.js";

function RecenterMap({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
}

export default function HeatMap({ hotspots = [], city, selected, onSelect }) {
  const cityInfo = CITY_CENTERS[city] || CITY_CENTERS.ahmedabad;
  const center = [cityInfo.lat, cityInfo.lng];

  return (
    <div className="h-[480px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <MapContainer center={center} zoom={cityInfo.zoom} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <RecenterMap center={center} zoom={cityInfo.zoom} />

        {hotspots.map((h) => {
          const cat = getCategoryColor(h.hotspot_category);
          const isActive = selected && selected.zone_id === h.zone_id;
          return (
            <CircleMarker
              key={h.zone_id}
              center={[safeNumber(h.latitude), safeNumber(h.longitude)]}
              radius={isActive ? 14 : 10}
              pathOptions={{
                color: isActive ? "#0f172a" : cat.color,
                weight: isActive ? 3 : 1.5,
                fillColor: cat.color,
                fillOpacity: 0.75,
              }}
              eventHandlers={{ click: () => onSelect && onSelect(h) }}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold text-slate-800">{h.zone_name}</p>
                  <p className="text-slate-500">
                    LST: {formatTemperature(h.lst_temperature)}
                  </p>
                  <p className="text-slate-500">
                    Heat Score: {safeNumber(h.heat_risk_score)}
                  </p>
                  <p>
                    <span
                      className="rounded px-2 py-0.5 text-xs font-semibold"
                      style={{ backgroundColor: cat.bg, color: cat.text }}
                    >
                      {h.hotspot_category}
                    </span>
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
