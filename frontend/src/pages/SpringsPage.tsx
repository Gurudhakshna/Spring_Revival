import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import MapView, { ALL_LAYERS } from '../components/MapView';
import { Badge, btnGhost, Card, Err, inputCls, Loading } from '../components/ui';

export default function SpringsPage() {
  const [params] = useSearchParams();
  const [springs, setSprings] = useState<any[]>([]);
  const [villages, setVillages] = useState<any[]>([]);
  const [wells, setWells] = useState<any[]>([]);
  const [sel, setSel] = useState<any>(null);
  const [rain, setRain] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [cls, setCls] = useState('');
  const [seas, setSeas] = useState('');
  const [err, setErr] = useState('');

  const load = (over?: any) => {
    api.springs(over ?? { search: q || undefined, suitability_class: cls || undefined, seasonality: seas || undefined })
      .then((r) => {
        setSprings(r.springs);
        const wanted = params.get('sel');
        const target = wanted ? r.springs.find((s) => s.spring_id === wanted) : r.springs[0];
        if (target) openSpring(target.spring_id);
      })
      .catch((e) => setErr(e.message));
    api.villages().then((r) => setVillages(r.villages)).catch(() => {});
    api.wells().then((r) => setWells(r.wells)).catch(() => {});
    api.rainfall().then((r) => setRain(r.monthly)).catch(() => {});
  };
  useEffect(() => { load(); }, []); // eslint-disable-line

  const openSpring = (id: string) => {
    api.springDetail(id).then(setSel).catch((e) => setErr(e.message));
  };

  const applyFilters = () => { setErr(''); load(); };

  if (err && !springs.length) return <Err message={err} onRetry={() => load()} />;

  return (
    <div className="grid lg:grid-cols-[300px_1fr_340px] gap-4">
      <Card title={`Springs (${springs.length})`} sub="Click a spring for detail">
        <div className="space-y-2 mb-3">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search ID / village" className={inputCls} />
          <div className="flex gap-2">
            <select value={cls} onChange={(e) => setCls(e.target.value)} className={inputCls}>
              <option value="">All classes</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option>
            </select>
            <select value={seas} onChange={(e) => setSeas(e.target.value)} className={inputCls}>
              <option value="">All</option><option value="perennial">Perennial</option><option value="seasonal">Seasonal</option>
            </select>
          </div>
          <button onClick={applyFilters} className={btnGhost + ' w-full'}>Apply filters</button>
        </div>
        <div className="max-h-[520px] overflow-y-auto divide-y divide-slate-100">
          {springs.map((s) => (
            <button key={s.spring_id} onClick={() => openSpring(s.spring_id)}
              className={`w-full text-left py-2 px-1 hover:bg-slate-50 ${sel?.spring_id === s.spring_id ? 'bg-brand-50' : ''}`}>
              <div className="text-sm font-bold">{s.spring_id} <Badge tone={s.suitability_class === 'HIGH' ? 'ok' : s.suitability_class === 'LOW' ? 'warn' : 'demo'}>{s.suitability_class} {Number(s.recharge_suitability).toFixed(0)}%</Badge></div>
              <div className="text-xs text-slate-500">{s.nearby_village} · {s.seasonality} · {s.discharge_lpm} L/min</div>
            </button>
          ))}
        </div>
      </Card>

      <div className="border border-slate-300 rounded-lg overflow-hidden" style={{ height: 640 }}>
        <MapView springs={springs} villages={villages} wells={wells} grid={[]} interventions={[]}
          layers={{ ...ALL_LAYERS, recharge: false }}
          selected={sel} onSpringClick={openSpring}
          springshed={sel?.estimated_springshed ? { lat: sel.estimated_springshed.center[0], lon: sel.estimated_springshed.center[1], radius: sel.estimated_springshed.radius_m } : null} />
      </div>

      <div className="space-y-3">
        {!sel ? <Loading label="Select a spring…" /> : (
          <>
            <Card title={`${sel.spring_id} — detail`} sub={sel.disclaimer}>
              <dl className="text-sm space-y-1">
                <div className="flex justify-between"><dt className="text-slate-500">Location</dt><dd className="font-semibold">{Number(sel.latitude).toFixed(4)}, {Number(sel.longitude).toFixed(4)}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Elevation</dt><dd className="font-semibold">{sel.elevation_m} m</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Discharge</dt><dd className="font-semibold">{sel.discharge_lpm} L/min</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Seasonality</dt><dd className="font-semibold">{sel.seasonality}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Nearby village</dt><dd className="font-semibold">{sel.nearby_village}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Recharge score</dt><dd className="font-bold">{sel.recharge_suitability}% ({sel.suitability_class})</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Confidence</dt><dd className="font-semibold">{sel.confidence}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Priority</dt><dd className="font-bold">{sel.priority.priority_score} ({sel.priority.priority_class})</dd></div>
              </dl>
              <div className="text-[11px] text-slate-500 mt-2">{sel.estimated_springshed.label} · radius {sel.estimated_springshed.radius_m} m</div>
            </Card>
            <Card title="Monthly rainfall context (mm)" sub="Prototype station data">
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={rain.map((r: any) => ({ m: r.month, mm: Number(r.rainfall_mm) }))}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="m" fontSize={10} /><YAxis fontSize={10} />
                  <Tooltip /><Bar dataKey="mm" fill="#20665b" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Risk flags">
              <ul className="text-sm space-y-1">
                {sel.risk_flags.map((f: any) => (
                  <li key={f.code}>{f.level === 'warn' ? '⚠' : '✓'} <span className={f.level === 'warn' ? 'text-red-700 font-semibold' : 'text-emerald-700'}>{f.message}</span></li>
                ))}
              </ul>
            </Card>
            <Card title="Why this location?">
              <ul className="text-sm space-y-1">{sel.priority.why.map((w: string, i: number) => <li key={i}>✓ {w}</li>)}</ul>
              <div className="text-[11px] text-slate-500 mt-2">Formula: {sel.priority.formula}</div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
