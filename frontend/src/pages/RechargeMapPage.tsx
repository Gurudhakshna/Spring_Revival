import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import MapView, { ALL_LAYERS, Focus, MapLayers } from '../components/MapView';
import { btnGhost, btnPrimary, Card, Err, Field, inputCls, Loading } from '../components/ui';

const LAYER_LABELS: [keyof MapLayers, string][] = [
  ['villages', 'Villages'], ['springs', 'Springs'], ['wells', 'Wells'],
  ['recharge', 'Recharge Suitability'], ['priority', 'High Priority Zones'], ['interventions', 'Intervention Sites'],
];

const LU = ['forest', 'agroforestry', 'agriculture', 'grassland', 'settlement', 'barren'];
const GEO = ['fractured_rock', 'weathered_granite', 'sandstone', 'shale', 'clay'];

export default function RechargeMapPage() {
  const nav = useNavigate();
  const [springs, setSprings] = useState<any[]>([]);
  const [villages, setVillages] = useState<any[]>([]);
  const [wells, setWells] = useState<any[]>([]);
  const [grid, setGrid] = useState<any[]>([]);
  const [layers, setLayers] = useState<MapLayers>({ ...ALL_LAYERS });
  const [search, setSearch] = useState('');
  const [focus, setFocus] = useState<Focus | undefined>();
  const [err, setErr] = useState('');
  const [form, setForm] = useState({ rainfall: 1200, slope: 12, soil_moisture: 0.7, land_use: 'forest', geology: 'fractured_rock', distance_to_stream: 250, lineament_density: 0.8, groundwater_depth: 15 });
  const [calc, setCalc] = useState<any>(null);
  const [calcErr, setCalcErr] = useState('');

  const load = () => {
    setErr('');
    Promise.all([api.springs(), api.villages(), api.wells(), api.rechargeMap()])
      .then(([s, v, w, m]) => { setSprings(s.springs); setVillages(v.villages); setWells(w.wells); setGrid(m.grid); })
      .catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const doSearch = () => {
    const q = search.trim().toLowerCase();
    if (!q) return;
    const s = springs.find((x) => x.spring_id.toLowerCase() === q || x.spring_id.toLowerCase().includes(q));
    const v = villages.find((x) => x.name.toLowerCase().includes(q) || x.village_id.toLowerCase() === q);
    const t = s || v;
    if (t) setFocus({ lat: t.latitude, lon: t.longitude, key: Date.now() });
    else alert('No village or spring matched "' + search + '"');
  };

  const runCalc = () => {
    setCalcErr('');
    api.rechargeCalculate(form).then(setCalc).catch((e) => setCalcErr(e.message));
  };

  if (err) return <Err message={err} onRetry={load} />;
  if (!springs.length) return <Loading label="Loading map layers…" />;

  const set = (k: string, v: any) => setForm({ ...form, [k]: v });

  return (
    <div className="grid lg:grid-cols-[1fr_320px] gap-4">
      <div className="space-y-3">
        <div className="bg-white border border-slate-200 rounded-lg p-3 flex flex-wrap items-center gap-2">
          {LAYER_LABELS.map(([k, label]) => (
            <label key={k} className="text-xs flex items-center gap-1.5 mr-2">
              <input type="checkbox" checked={layers[k]} onChange={() => setLayers({ ...layers, [k]: !layers[k] })} />
              {label}
            </label>
          ))}
          <span className="mx-1 h-4 w-px bg-slate-200" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && doSearch()}
            placeholder="Search village / spring ID" className={inputCls + ' !w-52'} />
          <button onClick={doSearch} className={btnGhost}>Search</button>
          <button onClick={() => setFocus({ lat: 23.46, lon: 84.96, key: Date.now() })} className={btnGhost}>Reset map</button>
        </div>
        <div className="border border-slate-300 rounded-lg overflow-hidden" style={{ height: 560 }}>
          <MapView springs={springs} villages={villages} wells={wells} grid={grid} interventions={[]}
            layers={layers} focus={focus} onSpringClick={(id) => nav(`/springs?sel=${id}`)} />
        </div>
      </div>
      <div className="space-y-3">
        <Card title="Recharge calculator" sub="Prototype Decision-Support Estimate">
          <div className="space-y-2">
            <Field label="Annual rainfall (mm)"><input type="number" value={form.rainfall} onChange={(e) => set('rainfall', +e.target.value)} className={inputCls} /></Field>
            <Field label="Slope (deg)"><input type="number" value={form.slope} onChange={(e) => set('slope', +e.target.value)} className={inputCls} /></Field>
            <Field label="Soil moisture (0–1)"><input type="number" step="0.05" value={form.soil_moisture} onChange={(e) => set('soil_moisture', +e.target.value)} className={inputCls} /></Field>
            <Field label="Land use">
              <select value={form.land_use} onChange={(e) => set('land_use', e.target.value)} className={inputCls}>
                {LU.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </Field>
            <Field label="Geology">
              <select value={form.geology} onChange={(e) => set('geology', e.target.value)} className={inputCls}>
                {GEO.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
            </Field>
            <Field label="Distance to stream (m)"><input type="number" value={form.distance_to_stream} onChange={(e) => set('distance_to_stream', +e.target.value)} className={inputCls} /></Field>
            <Field label="Lineament density (0–1)"><input type="number" step="0.05" value={form.lineament_density} onChange={(e) => set('lineament_density', +e.target.value)} className={inputCls} /></Field>
            <Field label="Groundwater depth (m)"><input type="number" value={form.groundwater_depth} onChange={(e) => set('groundwater_depth', +e.target.value)} className={inputCls} /></Field>
            <button onClick={runCalc} className={btnPrimary + ' w-full'}>Calculate</button>
            {calcErr && <div className="text-xs text-red-700">{calcErr}</div>}
            {calc && (
              <div className="text-sm border-t pt-2 mt-2 space-y-1">
                <div className="text-2xl font-bold">Score: {calc.score} <span className="text-sm">({calc.class})</span></div>
                <div className="text-xs">Confidence: {calc.confidence}</div>
                {Object.entries(calc.factors).map(([k, v]: any) => (
                  <div key={k} className="flex items-center gap-2 text-xs">
                    <span className="w-32 text-slate-600">{k}</span>
                    <div className="flex-1 h-2 bg-slate-100 rounded"><div className="h-2 rounded bg-brand-600" style={{ width: `${Math.min(100, (v / 20) * 100)}%` }} /></div>
                    <span className="w-10 text-right font-semibold">{v}</span>
                  </div>
                ))}
                <div className="text-[11px] text-slate-500">{calc.disclaimer}</div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
