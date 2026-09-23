import { useEffect, useState } from 'react';
import { Circle, CircleMarker, MapContainer, Marker, Popup, ScaleControl, TileLayer, Tooltip, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { reportColor, riskColor, scoreColor } from '../api/client';

export interface Focus { lat: number; lon: number; key: number }

function FlyTo({ focus }: { focus?: Focus }) {
  const map = useMap();
  useEffect(() => {
    if (focus) map.flyTo([focus.lat, focus.lon], 13, { duration: 1 });
  }, [focus, map]);
  return null;
}

function Invalidate() {
  const map = useMap();
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 300);
    return () => clearTimeout(t);
  }, [map]);
  return null;
}

function Coords() {
  const [c, setC] = useState<{lat:number;lon:number}|null>(null);
  useMapEvents({
    mousemove(e){ setC({lat: e.latlng.lat, lon: e.latlng.lng}); },
  });
  if(!c) return null;
  return (
    <div className="leaflet-bottom leaflet-left" style={{pointerEvents:'none'}}>
      <div className="leaflet-control bg-white/90 text-[11px] px-2 py-1 rounded shadow border border-slate-200" style={{margin:'0 0 10px 10px'}}>
        {c.lat.toFixed(4)}, {c.lon.toFixed(4)}
      </div>
    </div>
  );
}

function Legend() {
  const map = useMap();
  useEffect(() => {
    const ctl = new L.Control({ position: 'bottomright' });
    ctl.onAdd = () => {
      const d = L.DomUtil.create('div', 'jr-legend');
      d.innerHTML =
        `<div style="font-weight:700;margin-bottom:4px">Legend</div>` +
        `<div><span class="sw" style="background:#15803d"></span>High recharge (≥70)</div>` +
        `<div><span class="sw" style="background:#d97706"></span>Medium (45–70)</div>` +
        `<div><span class="sw" style="background:#b91c1c"></span>Low (&lt;45)</div>` +
        `<div><span class="sw" style="background:#1d4ed8;border-radius:3px"></span>Well</div>` +
        `<div><span class="sw" style="background:#0f766e"></span>Village</div>` +
        `<div><span class="sw" style="background:#7c3aed"></span>Intervention</div>`;
      return d;
    };
    ctl.addTo(map);
    return () => { ctl.remove(); };
  }, [map]);
  return null;
}

const pin = (cls: string, html: string, size = 26, extra = '') =>
  L.divIcon({ className: '', html: `<div class="jr-pin ${cls}" style="width:${size}px;height:${size}px;${extra}">${html}</div>`, iconSize: [size, size], iconAnchor: [size / 2, size / 2] });

export interface MapLayers { villages: boolean; springs: boolean; wells: boolean; recharge: boolean; priority: boolean; interventions: boolean }

export const ALL_LAYERS: MapLayers = { villages: true, springs: true, wells: true, recharge: true, priority: true, interventions: true };

export default function MapView({ springs, villages, wells, grid, interventions, layers,
  selected, springshed, focus, onSpringClick, height = '100%',
  gwStations = [], reports = [], center, zoom, onStationClick, onReportClick }: {
  springs: any[]; villages: any[]; wells: any[]; grid: any[]; interventions: any[];
  layers: MapLayers; selected?: any; springshed?: { lat: number; lon: number; radius: number } | null;
  focus?: Focus; onSpringClick?: (id: string) => void; height?: string;
  gwStations?: any[]; reports?: any[]; center?: [number, number]; zoom?: number;
  onStationClick?: (id: string) => void; onReportClick?: (id: string) => void;
}) {
  return (
    <MapContainer center={center || [23.46, 84.96]} zoom={zoom || 11} style={{ height, width: '100%', minHeight: 420 }} scrollWheelZoom>
      <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Invalidate /><FlyTo focus={focus} /><Legend /><ScaleControl position="bottomleft" /><Coords />
      {layers.recharge && grid.map((g) => (
        <CircleMarker key={g.id} center={[g.latitude, g.longitude]} radius={7}
          pathOptions={{ color: scoreColor(g.score), fillColor: scoreColor(g.score), fillOpacity: 0.45, weight: 1 }}>
          <Tooltip>Grid {g.id} — score {g.score} ({g.class})<br />Prototype Decision-Support Estimate</Tooltip>
        </CircleMarker>
      ))}
      {layers.villages && villages.map((v) => (
        <Marker key={v.village_id} position={[v.latitude, v.longitude]} icon={pin('jr-village', 'V', 22)}>
          <Tooltip direction="top" offset={[0, -12]} opacity={1}>
            <span className="text-xs"><b>{v.name}</b> ({v.village_id})<br />Pop. {v.population} · {v.block}</span>
          </Tooltip>
        </Marker>
      ))}
      {layers.wells && wells.map((w) => (
        <Marker key={w.well_id} position={[w.latitude, w.longitude]} icon={pin('jr-well', 'W', 22)}>
          <Tooltip direction="top" offset={[0, -12]} opacity={1}>
            <span className="text-xs"><b>{w.well_id}</b> — {w.well_type}<br />Depth {w.depth_m} m · Water level {w.water_level_m} m</span>
          </Tooltip>
        </Marker>
      ))}
      {layers.springs && springs.map((s) => {
        const sc = Number(s.recharge_suitability ?? 0);
        const cls = sc >= 70 ? 'jr-spring-high' : sc >= 45 ? 'jr-spring-medium' : 'jr-spring-low';
        return (
          <Marker key={s.spring_id} position={[s.latitude, s.longitude]} icon={pin(cls, 'S')}>
            <Popup>
              <div style={{ fontSize: 12, minWidth: 180 }}>
                <div style={{ fontWeight: 800 }}>Spring ID: {s.spring_id}</div>
                <div>Elevation: {s.elevation_m} m</div>
                <div>Seasonality: {s.seasonality}</div>
                <div>Discharge: {s.discharge_lpm} L/min</div>
                <div>Recharge Suitability: <b>{sc}%</b></div>
                <div>Confidence: {s.confidence ?? '—'}</div>
                {onSpringClick && (
                  <button onClick={() => onSpringClick(s.spring_id)}
                    style={{ marginTop: 6, background: '#1c534b', color: '#fff', border: 0, borderRadius: 4, padding: '4px 10px', cursor: 'pointer' }}>
                    Open detail
                  </button>
                )}
              </div>
            </Popup>
          </Marker>
        );
      })}
      {layers.priority && springs.filter((s) => Number(s.recharge_suitability ?? 0) >= 70).map((s) => (
        <Circle key={'pz-' + s.spring_id} center={[s.latitude, s.longitude]} radius={420}
          pathOptions={{ color: '#15803d', weight: 1.5, dashArray: '5 5', fillOpacity: 0.05 }} />
      ))}
      {layers.interventions && interventions.map((it: any, i: number) => (
        it.latitude && it.longitude ? (
          <Marker key={'iv-' + i} position={[it.latitude, it.longitude]} icon={pin('jr-interv', 'I', 22)}>
            <Tooltip direction="top" offset={[0, -12]} opacity={1}>
              <span className="text-xs"><b>{it.intervention_name || it.intervention}</b><br />
              Score {it.base_score} → {it.predicted_score} (＋{it.improvement}) · ₹{Number(it.estimated_cost_inr).toLocaleString('en-IN')}</span>
            </Tooltip>
          </Marker>
        ) : null
      ))}
      {springshed && (
        <Circle center={[springshed.lat, springshed.lon]} radius={springshed.radius}
          pathOptions={{ color: '#0d9488', weight: 2, dashArray: '6 4', fillOpacity: 0.08 }}>
          <Tooltip permanent direction="top" opacity={1}>
            <span className="text-xs">Estimated Prototype Springshed (not officially delineated)</span>
          </Tooltip>
        </Circle>
      )}
      {selected && <Circle center={[selected.latitude, selected.longitude]} radius={120} pathOptions={{ color: '#111827', weight: 2, fillOpacity: 0 }} />}
      {gwStations.map((g: any) => (
        g.latitude && g.longitude ? (
          <CircleMarker key={'gw-' + g.station_id} center={[g.latitude, g.longitude]} radius={6}
            pathOptions={{ color: riskColor(g.risk_level), fillColor: riskColor(g.risk_level), fillOpacity: 0.7, weight: 1 }}>
            <Popup>
              <div style={{ fontSize: 12, minWidth: 170 }}>
                <div style={{ fontWeight: 800 }}>Station: {g.station_id}</div>
                <div>Risk: <b style={{ color: riskColor(g.risk_level) }}>{g.risk_level}</b> ({g.risk_score})</div>
                <div>Trend: {g.trend}</div>
                <div>Current: {g.latest_value} m ({g.latest_date})</div>
                <div style={{ fontSize: 11, color: '#64748b' }}>AI/Prototype Decision Support</div>
                {onStationClick && (
                  <button onClick={() => onStationClick(g.station_id)}
                    style={{ marginTop: 6, background: '#1c534b', color: '#fff', border: 0, borderRadius: 4, padding: '4px 10px', cursor: 'pointer' }}>
                    Open station
                  </button>
                )}
              </div>
            </Popup>
          </CircleMarker>
        ) : null
      ))}
      {reports.map((r: any) => (
        r.latitude && r.longitude ? (
          <Marker key={'rp-' + r.report_id} position={[r.latitude, r.longitude]}
            icon={pin('jr-report', 'R', 22,
              `background:${reportColor(r.status)};${r.severity === 'CRITICAL' ? 'border-color:#b91c1c;box-shadow:0 0 0 3px #fca5a5;' : ''}`)}>
            <Popup>
              <div style={{ fontSize: 12, minWidth: 180 }}>
                <div style={{ fontWeight: 800 }}>{r.report_id}</div>
                <div>{String(r.problem_type).replace(/_/g, ' ')} · {r.village}</div>
                <div>Severity: <b>{r.severity}</b> · Status: <b style={{ color: reportColor(r.status) }}>{String(r.status).replace(/_/g, ' ')}</b></div>
                <div>Nearest station: {r.nearest_station_id || '—'} ({r.risk_level || '—'})</div>
                <div style={{ fontSize: 11, color: '#64748b' }}>Community reported — pending field verification.</div>
                {onReportClick && (
                  <button onClick={() => onReportClick(r.report_id)}
                    style={{ marginTop: 6, background: '#1c534b', color: '#fff', border: 0, borderRadius: 4, padding: '4px 10px', cursor: 'pointer' }}>
                    Open report
                  </button>
                )}
              </div>
            </Popup>
          </Marker>
        ) : null
      ))}
    </MapContainer>
  );
}
