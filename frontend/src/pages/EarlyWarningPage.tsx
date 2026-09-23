import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api, riskColor } from '../api/client';
import MapView, { ALL_LAYERS } from '../components/MapView';
import { Badge, btnGhost, btnPrimary, Card, Err, Field, inputCls, Loading } from '../components/ui';

export default function EarlyWarningPage() {
  const [summary, setSummary] = useState<any>(null);
  const [lead, setLead] = useState<any>(null);
  const [risk, setRisk] = useState('');
  const [q, setQ] = useState('');
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [sel, setSel] = useState<any>(null);
  const [fc, setFc] = useState<any>(null);
  const [err, setErr] = useState('');

  const loadSummary = () => {
    api.ewSummary(200).then(setSummary).catch((e) => setErr(e.message));
    api.ewLeadTime().then(setLead).catch(() => {});
  };
  const loadRows = () => {
    api.ewStations({ risk: risk || undefined, search: q || undefined, limit: 100 })
      .then((r) => { setRows(r.warnings); setTotal(r.count); })
      .catch((e) => setErr(e.message));
  };
  useEffect(loadSummary, []);
  useEffect(loadRows, []); // eslint-disable-line

  const openStation = (id: string) => {
    setFc(null);
    api.ewStation(id).then(setSel).catch((e) => setErr(e.message));
  };

  if (err && !summary) return <Err message={err} onRetry={loadSummary} />;
  if (!summary) return <Loading label="Assessing groundwater stations…" />;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Active warnings</div>
          <div className="text-2xl font-bold text-brand-800 mt-1">{summary.count}</div>
          <div className="text-xs text-slate-500 mt-0.5">of {summary.stations_assessed} stations assessed</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Critical</div>
          <div className="text-2xl font-bold text-red-700 mt-1">{summary.levels?.CRITICAL ?? 0}</div>
          <div className="text-xs text-slate-500 mt-0.5">immediate attention</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Warning</div>
          <div className="text-2xl font-bold text-orange-600 mt-1">{summary.levels?.WARNING ?? 0}</div>
          <div className="text-xs text-slate-500 mt-0.5">declining trend</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Watch</div>
          <div className="text-2xl font-bold text-amber-600 mt-1">{summary.levels?.WATCH ?? 0}</div>
          <div className="text-xs text-slate-500 mt-0.5">early signals</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Last updated</div>
          <div className="text-lg font-bold text-brand-800 mt-1">{summary.last_updated}</div>
          <div className="text-xs text-slate-500 mt-0.5">AI/Prototype Decision Support</div>
        </div>
      </div>

      <Card title="Warning lead time (historical validation)" sub="Retrospective — not a village dry-out prediction">
        {!lead ? <Loading /> : lead.possible ? (
          <div className="text-sm text-slate-700">
            Validated warning lead time: <b className="text-lg">{lead.median_days} days</b> (median) ·
            mean {lead.mean_days} d · min {lead.min_days} d · max {lead.max_days} d · {lead.events} events.
            <div className="text-[11px] text-slate-500 mt-1">{lead.method}</div>
          </div>
        ) : (
          <div className="text-sm text-slate-600">{lead.reason || 'Insufficient historical event labels for validated lead-time estimation.'}</div>
        )}
      </Card>

      <div className="grid lg:grid-cols-[1fr_380px] gap-4">
        <div className="space-y-3">
          <div className="bg-white border border-slate-200 rounded-lg p-3 flex flex-wrap items-center gap-2">
            <select value={risk} onChange={(e) => setRisk(e.target.value)} className={inputCls + ' !w-40'}>
              <option value="">All levels</option><option>CRITICAL</option><option>WARNING</option><option>WATCH</option>
            </select>
            <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && loadRows()}
              placeholder="Search station ID" className={inputCls + ' !w-52'} />
            <button onClick={loadRows} className={btnGhost}>Apply</button>
            <span className="text-xs text-slate-500 ml-auto">{total} stations</span>
          </div>
          <div className="border border-slate-300 rounded-lg overflow-hidden" style={{ height: 420 }}>
            <MapView springs={[]} villages={[]} wells={[]} grid={[]} interventions={[]}
              layers={{ ...ALL_LAYERS, villages: false, springs: false, wells: false, recharge: false, priority: false, interventions: false }}
              gwStations={rows} center={[22.5, 79.5]} zoom={5} onStationClick={openStation} />
          </div>
          <Card title={`Stations (${total})`} sub="Click a station for detail">
            <div className="max-h-[380px] overflow-y-auto divide-y divide-slate-100">
              {rows.map((w) => (
                <button key={w.station_id} onClick={() => openStation(w.station_id)}
                  className={`w-full text-left py-2 px-1 hover:bg-slate-50 ${sel?.station_id === w.station_id ? 'bg-brand-50' : ''}`}>
                  <div className="text-sm font-bold">
                    {w.risk_level === 'CRITICAL' ? '🔴' : w.risk_level === 'WARNING' ? '🟠' : '🟡'} {w.station_id}{' '}
                    <span className="text-xs" style={{ color: riskColor(w.risk_level) }}>{w.risk_level} · {w.risk_score}</span>
                  </div>
                  <div className="text-xs text-slate-500">
                    Current {w.latest_value} m ({w.latest_date}) · trend {w.trend} ·
                    rainfall {w.rainfall_anomaly_pct ?? '—'}% · decline {w.consecutive_declines}d
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-3">
          {!sel ? <Loading label="Select a station…" /> : (
            <>
              <Card title={`${sel.station_id} — ${sel.risk_level}`} sub="AI/Prototype Decision Support">
                <dl className="text-sm space-y-1">
                  <div className="flex justify-between"><dt className="text-slate-500">Current value</dt><dd className="font-bold">{sel.latest_value} m ({sel.latest_date})</dd></div>
                  <div className="flex justify-between"><dt className="text-slate-500">Trend</dt><dd className="font-semibold">{sel.trend}</dd></div>
                  <div className="flex justify-between"><dt className="text-slate-500">MA 7/30/90</dt><dd className="font-semibold">{sel.ma7 ?? '—'} / {sel.ma30 ?? '—'} / {sel.ma90 ?? '—'}</dd></div>
                  <div className="flex justify-between"><dt className="text-slate-500">Seasonal baseline</dt><dd className="font-semibold">{sel.seasonal_baseline ?? 'insufficient data'}</dd></div>
                  <div className="flex justify-between"><dt className="text-slate-500">GW anomaly</dt><dd className="font-semibold">{sel.gw_anomaly_m ?? '—'} m</dd></div>
                  <div className="flex justify-between"><dt className="text-slate-500">Rainfall anomaly</dt><dd className="font-semibold">{sel.rainfall_anomaly_pct ?? '—'}%</dd></div>
                  <div className="flex justify-between"><dt className="text-slate-500">Consecutive decline</dt><dd className="font-semibold">{sel.consecutive_declines} obs</dd></div>
                </dl>
                <div className="text-[11px] text-slate-500 mt-2">{sel.reason_summary}</div>
                <Link to="/planner" className={btnPrimary + ' w-full mt-3 inline-block text-center'}>Simulate Intervention</Link>
              </Card>
              <Card title="Groundwater history" sub={`n=${sel.history?.count ?? sel.n_obs} observations`}>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={(sel.history?.points || []).map((p: any, i: number) => ({ ...p, ma: sel.history?.ma30obs?.[i] }))}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" fontSize={9} tick={false} /><YAxis fontSize={10} />
                    <Tooltip /><Legend />
                    <Line type="monotone" dataKey="target" name="Level (m)" stroke="#1c534b" strokeWidth={1.5} dot={false} />
                    <Line type="monotone" dataKey="ma" name="MA-30obs" stroke="#d97706" strokeWidth={1.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
              <Card title="Why this warning?">
                <ul className="text-sm space-y-1">
                  {(sel.reasons || []).map((r: string, i: number) => <li key={i}>✓ {r}</li>)}
                  {(sel.ok_signals || []).map((r: string, i: number) => <li key={2000 + i}>- {r}</li>)}
                  {!(sel.reasons || []).length && <li className="text-slate-500">No stress signals — calculated from actual history.</li>}
                </ul>
                <div className="mt-3">
                  <button onClick={() => api.ewForecast(sel.station_id, 30).then(setFc).catch((e) => setErr(e.message))}
                    className={btnGhost}>Forecast 30 days</button>
                  {fc && (
                    <div className="text-sm mt-2">
                      {fc.detail ? <span className="text-slate-500">{fc.detail}</span> : (
                        <>Forecast <b>{fc.forecast_target} m</b> · risk {fc.risk}
                        {fc.confidence_interval_80 && <span> · 80% [{fc.confidence_interval_80[0]}, {fc.confidence_interval_80[1]}]</span>}
                        {!fc.confidence_interval_80 && <span> · {fc.confidence_note}</span>}
                        <div className="text-[11px] text-slate-500">Holdout MAE {fc.validation?.holdout_mae} (chronological, no shuffling)</div></>)}
                    </div>
                  )}
                </div>
              </Card>
            </>
          )}
        </div>
      </div>
      <div><Badge tone="info">Groundwater data: provided dataset (real) · warnings: AI/Prototype Decision Support</Badge></div>
    </div>
  );
}
