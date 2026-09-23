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

const BELTS = [
  {id:'', name:'All Tribal Belts (Pan-India)', center:[20.5,80.0] as [number,number], zoom:5},
  {id:'jhk', name:'Jharkhand-Odisha-Chhattisgarh', center:[23.45,84.95] as [number,number], zoom:10},
  {id:'mp', name:'Madhya Pradesh', center:[22.90,78.60] as [number,number], zoom:9},
  {id:'rj', name:'Rajasthan-Gujarat Bhil', center:[23.80,73.50] as [number,number], zoom:9},
  {id:'ne', name:'Northeast (Meghalaya-Nagaland)', center:[26.10,92.90] as [number,number], zoom:8},
  {id:'ghats', name:'Western Ghats (Kerala-Karnataka)', center:[11.80,76.10] as [number,number], zoom:8},
  {id:'tn', name:'Tamil Nadu-Andhra', center:[13.50,79.00] as [number,number], zoom:8},
  {id:'mh', name:'Maharashtra-Chhattisgarh', center:[19.50,80.20] as [number,number], zoom:8},
];

export default function RechargeMapPage() {
  const nav = useNavigate();
  const [springs, setSprings] = useState<any[]>([]);
  const [villages, setVillages] = useState<any[]>([]);
  const [wells, setWells] = useState<any[]>([]);
  const [grid, setGrid] = useState<any[]>([]);
  const [layers, setLayers] = useState<MapLayers>({ ...ALL_LAYERS });
  const [search, setSearch] = useState('');
  const [focus, setFocus] = useState<Focus | undefined>();
  const [belt, setBelt] = useState<string>(() => localStorage.getItem('jr-belt') || '');
  const [center, setCenter] = useState<[number,number]>(BELTS.find(b=>b.id===belt)?.center || [23.46,84.96]);
  const [zoom, setZoom] = useState(BELTS.find(b=>b.id===belt)?.zoom || 6);
  const [selected, setSelected] = useState<any>(null);
  const [err, setErr] = useState('');
  const [form, setForm] = useState({ rainfall: 1200, slope: 12, soil_moisture: 0.7, land_use: 'forest', geology: 'fractured_rock', distance_to_stream: 250, lineament_density: 0.8, groundwater_depth: 15 });
  const [calc, setCalc] = useState<any>(null);
  const [calcErr, setCalcErr] = useState('');

  const load = (beltId = belt) => {
    setErr('');
    const q = beltId ? {belt_id: beltId} : undefined;
    Promise.all([api.springs(q), api.villages(q), api.wells(q), api.rechargeMap(q ? {belt_id: beltId} : undefined)])
      .then(([s, v, w, m]) => { setSprings(s.springs); setVillages(v.villages); setWells(w.wells); setGrid(m.grid); })
      .catch((e) => setErr(e.message));
  };
  useEffect(()=>{ load(); }, []);
  useEffect(()=>{ localStorage.setItem('jr-belt', belt); }, [belt]);

  const onBeltChange = (id: string) => {
    setBelt(id);
    const b = BELTS.find(x=>x.id===id) || BELTS[0];
    setCenter(b.center); setZoom(b.zoom);
    setFocus({lat:b.center[0], lon:b.center[1], key:Date.now()});
    load(id);
  };

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

  if (err) return <Err message={err} onRetry={()=>load()} />;
  if (!springs.length) return <Loading label="Loading map layers…" />;

  const set = (k: string, v: any) => setForm({ ...form, [k]: v });

  const onSpringClick = (id:string) => {
    api.springDetail(id).then(setSelected).catch(()=>{});
  };

  return (
    <div className="grid lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <div className="bg-white border border-slate-200 rounded-lg p-3 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold text-slate-600">Tribal Belt:</span>
            <select value={belt} onChange={e=>onBeltChange(e.target.value)} className={inputCls + ' !w-auto !py-1'}>
              {BELTS.map(b=> <option key={b.id} value={b.id}>{b.name} {b.id?`(${springs.filter(s=> s.state && b.name.toLowerCase().includes(s.state.toLowerCase().slice(0,4))).length || ''})`:''}</option>)}
            </select>
            <span className="text-xs text-slate-500">{springs.length} springs · {villages.length} villages · {grid.length} grid</span>
            <span className="ml-auto text-[11px] text-slate-400">Coords shown on hover · Scale bottom-left</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {LAYER_LABELS.map(([k, label]) => (
              <label key={k} className="text-xs flex items-center gap-1.5 mr-2">
                <input type="checkbox" checked={layers[k]} onChange={() => setLayers({ ...layers, [k]: !layers[k] })} />
                {label}
              </label>
            ))}
          </div>
          <div className="flex gap-2">
            <input value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && doSearch()}
              placeholder="Search village / spring ID" className={inputCls + ' !w-52'} />
            <button onClick={doSearch} className={btnGhost}>Search</button>
            <button onClick={() => { const b = BELTS.find(x=>x.id===belt) || BELTS[0]; setFocus({ lat:b.center[0], lon:b.center[1], key:Date.now()}); }} className={btnGhost}>Reset to belt</button>
          </div>
        </div>
        <div className="border border-slate-300 rounded-lg overflow-hidden relative" style={{ height: 560 }}>
          <MapView springs={springs} villages={villages} wells={wells} grid={grid} interventions={[]}
            layers={layers} focus={focus} center={center} zoom={zoom}
            selected={selected} onSpringClick={onSpringClick}
            springshed={selected?.estimated_springshed ? { lat: selected.estimated_springshed.center[0], lon: selected.estimated_springshed.center[1], radius: selected.estimated_springshed.radius_m } : null} />
          {selected && (
            <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur rounded-lg shadow-lg border border-slate-200 p-3 w-[320px] text-xs">
              <div className="font-bold">{selected.spring_id} — {selected.nearby_village} ({selected.state})</div>
              <div className="text-slate-600">{selected.latitude.toFixed(4)}, {selected.longitude.toFixed(4)} · {selected.elevation_m}m · {selected.seasonality}</div>
              <div className="mt-1">Recharge <b>{selected.recharge_suitability}%</b> ({selected.suitability_class}) · Priority <b>{selected.priority?.priority_score}</b></div>
              <div className="flex gap-2 mt-2">
                <button onClick={()=>nav(`/springs?sel=${selected.spring_id}`)} className={btnGhost + ' !py-1 !text-xs'}>Open detail</button>
                <button onClick={async()=>{
                  const a = await api.analysis(selected.spring_id);
                  alert(`AI Analysis: ${a.assessment.recharge_suitability}% ${a.assessment.recharge_class} · Water stress ${a.assessment.water_stress} · Recommend ${a.recommendation.type} — ${a.recommendation.why}`);
                }} className={btnPrimary + ' !py-1 !text-xs'}>RUN AI ANALYSIS</button>
              </div>
            </div>
          )}
        </div>
        <div className="text-[11px] text-slate-500">Selected: {selected?.spring_id || 'none'} · Grid: {grid.length} points · State filter: {belt || 'All'} · Data source: Synthetic Prototype Dataset</div>
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
