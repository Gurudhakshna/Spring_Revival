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
  const [analysis, setAnalysis] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [rain, setRain] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [cls, setCls] = useState('');
  const [seas, setSeas] = useState('');
  const [belt, setBelt] = useState<string>(() => localStorage.getItem('jr-belt') || '');
  const [err, setErr] = useState('');

  const load = (over?: any) => {
    const beltQ = belt ? {belt_id: belt} : undefined;
    const baseQ = over ?? { search: q || undefined, suitability_class: cls || undefined, seasonality: seas || undefined, ...(beltQ||{}) };
    // Merge belt if over provided without belt
    const finalQ = belt && !over?.belt_id && !over?.state ? {...baseQ, belt_id: belt} : baseQ;
    api.springs(finalQ as any)
      .then((r) => {
        setSprings(r.springs);
        const wanted = params.get('sel');
        const target = wanted ? r.springs.find((s) => s.spring_id === wanted) : r.springs[0];
        if (target) openSpring(target.spring_id);
      })
      .catch((e) => setErr(e.message));
    api.villages(beltQ as any).then((r) => setVillages(r.villages)).catch(() => {});
    api.wells(beltQ as any).then((r) => setWells(r.wells)).catch(() => {});
    api.rainfall().then((r) => setRain(r.monthly)).catch(() => {});
  };
  useEffect(() => { load(); }, []); // eslint-disable-line
  useEffect(()=>{ localStorage.setItem('jr-belt', belt); load(); }, [belt]);

  const openSpring = (id: string) => {
    api.springDetail(id).then((s)=>{ setSel(s); setAnalysis(null); }).catch((e) => setErr(e.message));
  };

  const runAnalysis = async () => {
    if(!sel) return;
    setAnalysisLoading(true); setErr('');
    try{
      const a = await api.analysis(sel.spring_id);
      setAnalysis(a);
    }catch(e:any){ setErr(e.message); }
    finally{ setAnalysisLoading(false); }
  };

  const generateReport = async () => {
    if(!sel) return;
    try{
      const r = await fetch(`/api/reports/${encodeURIComponent(sel.spring_id)}`);
      if(r.headers.get('content-type')?.includes('application/pdf')){
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href=url; a.download=`JAL-RAKSHA-${sel.spring_id}.pdf`; a.click(); URL.revokeObjectURL(url);
      } else {
        const j = await r.json();
        alert('Report (JSON preview): ' + JSON.stringify(j).slice(0,500));
      }
    }catch(e:any){ setErr(e.message); }
  };

  const applyFilters = () => { setErr(''); load(); };

  if (err && !springs.length) return <Err message={err} onRetry={() => load()} />;

  const BELT_OPTS = [
    {id:'', name:'All Tribal Belts'},
    {id:'jhk', name:'Jharkhand-Odisha-Chhattisgarh'},
    {id:'mp', name:'Madhya Pradesh'},
    {id:'rj', name:'Rajasthan-Gujarat'},
    {id:'ne', name:'Northeast'},
    {id:'ghats', name:'Western Ghats'},
    {id:'tn', name:'Tamil Nadu-Andhra'},
    {id:'mh', name:'Maharashtra'},
  ];

  return (
    <div className="grid lg:grid-cols-[320px_1fr_380px] gap-4">
      <Card title={`Springs (${springs.length})`} sub="Pan-India · Click a spring for detail">
        <div className="space-y-2 mb-3">
          <select value={belt} onChange={e=>setBelt(e.target.value)} className={inputCls}>
            {BELT_OPTS.map(o=> <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search ID / village / state" className={inputCls} />
          <div className="flex gap-2">
            <select value={cls} onChange={(e) => setCls(e.target.value)} className={inputCls}>
              <option value="">All classes</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option>
            </select>
            <select value={seas} onChange={(e) => setSeas(e.target.value)} className={inputCls}>
              <option value="">All</option><option value="perennial">Perennial</option><option value="seasonal">Seasonal</option>
            </select>
          </div>
          <button onClick={applyFilters} className={btnGhost + ' w-full'}>Apply filters</button>
          <div className="text-[11px] text-slate-500">Belt filter uses backend ?belt_id — try Rajasthan → 18 LOW springs</div>
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

      <div className="space-y-3 max-h-[640px] overflow-y-auto">
        {!sel ? <Loading label="Select a spring…" /> : (
          <>
            <Card title={`${sel.spring_id} — detail`} sub={`${sel.state} · ${sel.tribal_belt} · ${sel.disclaimer}`}>
              <dl className="text-sm space-y-1">
                <div className="flex justify-between"><dt className="text-slate-500">Location</dt><dd className="font-semibold">{Number(sel.latitude).toFixed(4)}, {Number(sel.longitude).toFixed(4)}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">State / Belt</dt><dd className="font-semibold">{sel.state}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Elevation</dt><dd className="font-semibold">{sel.elevation_m} m</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Discharge</dt><dd className="font-semibold">{sel.discharge_lpm} L/min</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Seasonality</dt><dd className="font-semibold">{sel.seasonality}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Nearby village</dt><dd className="font-semibold">{sel.nearby_village}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Recharge score</dt><dd className="font-bold">{sel.recharge_suitability}% ({sel.suitability_class})</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Confidence</dt><dd className="font-semibold">{sel.confidence}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Priority</dt><dd className="font-bold">{sel.priority.priority_score} ({sel.priority.priority_class})</dd></div>
              </dl>
              <div className="text-[11px] text-slate-500 mt-2">{sel.estimated_springshed.label} · radius {sel.estimated_springshed.radius_m} m</div>
              <div className="flex gap-2 mt-3">
                <button onClick={runAnalysis} disabled={analysisLoading} className="flex-1 text-sm font-bold bg-brand-700 text-white rounded px-3 py-2 hover:bg-brand-800 disabled:opacity-50">
                  {analysisLoading ? 'Analyzing…' : 'RUN AI ANALYSIS'}
                </button>
                <button onClick={generateReport} className="text-sm font-semibold border border-slate-300 rounded px-3 py-2 hover:bg-slate-50">📄 Report</button>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Calls POST /api/analysis/{sel.spring_id} → recharge+risk+priority+why+recommendation</div>
            </Card>

            {analysis && (
              <Card title="Overall Assessment" sub={`Model: RandomForest · ${analysis.timestamp}`}>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-slate-50 rounded p-2"><div className="text-xs text-slate-500">Recharge</div><div className="text-lg font-bold" style={{color: analysis.recharge.class==='HIGH'?'#15803d':analysis.recharge.class==='LOW'?'#b91c1c':'#d97706'}}>{analysis.recharge.score}% {analysis.recharge.class}</div></div>
                  <div className="bg-slate-50 rounded p-2"><div className="text-xs text-slate-500">Water Stress</div><div className="text-lg font-bold">{analysis.assessment.water_stress}</div></div>
                  <div className="bg-slate-50 rounded p-2"><div className="text-xs text-slate-500">Spring Risk</div><div className="text-lg font-bold">{analysis.assessment.spring_risk}</div></div>
                  <div className="bg-slate-50 rounded p-2"><div className="text-xs text-slate-500">Confidence</div><div className="text-lg font-bold">{analysis.assessment.confidence}</div></div>
                </div>
                <div className="mt-3">
                  <div className="text-xs font-bold">Why?</div>
                  <div className="space-y-1 mt-1">
                    {analysis.why.slice(0,5).map((w:any)=> (
                      <div key={w.factor} className="flex items-center gap-2 text-xs">
                        <span className="w-36 text-slate-600">{w.factor}</span>
                        <div className="flex-1 h-2 bg-slate-100 rounded"><div className="h-2 rounded bg-brand-600" style={{width:`${Math.min(100, (w.value/20)*100)}%`}}/></div>
                        <span className="w-10 text-right font-semibold">{w.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-xs">
                  <b>Recommended:</b> {analysis.recommendation.type} — {analysis.recommendation.why}
                </div>
                <div className="flex gap-2 mt-2">
                  <button onClick={()=> window.location.href=`/planner?spring=${analysis.spring_id}&type=${analysis.recommendation.type}`} className="text-xs font-semibold bg-emerald-700 text-white rounded px-3 py-1.5">Simulate this → Planner</button>
                  <button onClick={async()=>{ const r=await fetch(`/api/analysis/${analysis.spring_id}/explain`,{method:'POST'}); const j=await r.json(); alert(j.explanation); }} className="text-xs border rounded px-3 py-1.5">Explain (AI)</button>
                </div>
              </Card>
            )}
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
