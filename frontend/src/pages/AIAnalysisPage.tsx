import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import { btnPrimary, Card, Err, Field, inputCls, Loading } from '../components/ui';

const PRETTY: Record<string, string> = {
  annual_rainfall_mm: 'Rainfall', geology: 'Geology', slope_deg: 'Slope',
  soil_moisture_index: 'Soil moisture', land_use: 'Land use',
  distance_to_stream_m: 'Distance to stream', elevation_m: 'Elevation',
  lineament_density_index: 'Lineament density', groundwater_depth_m: 'Groundwater depth',
};

export default function AIAnalysisPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [imp, setImp] = useState<any[]>([]);
  const [err, setErr] = useState('');
  const [form, setForm] = useState({ elevation_m: 620, slope_deg: 12, annual_rainfall_mm: 1200, soil_moisture_index: 0.6, land_use: 'forest', geology: 'fractured_rock', distance_to_stream_m: 250, lineament_density_index: 0.6, groundwater_depth_m: 15 });
  const [pred, setPred] = useState<any>(null);
  const [springs, setSprings] = useState<any[]>([]);
  const [selSpring, setSelSpring] = useState('SPR-001');
  const [analysis, setAnalysis] = useState<any>(null);
  const [analysisBusy, setAnalysisBusy] = useState(false);

  const load = () => {
    setErr('');
    Promise.all([api.mlMetrics(), api.mlImportance(), api.springs()])
      .then(([m, f, s]) => { setMetrics(m); setImp(f.features || []); setSprings(s.springs); if(s.springs.length) setSelSpring(s.springs[0].spring_id); })
      .catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  const set = (k: string, v: any) => setForm({ ...form, [k]: v });
  const runUnified = async () => {
    setAnalysisBusy(true); setErr('');
    try{ const a = await api.analysis(selSpring); setAnalysis(a); } catch(e:any){ setErr(e.message); } finally{ setAnalysisBusy(false); }
  };

  if (err) return <Err message={err} onRetry={load} />;
  if (!metrics) return <Loading label="Evaluating model on validation data…" />;

  const chartData = imp.map((f) => ({ name: PRETTY[f.feature] || f.feature, importance: f.importance }));
  const maxI = Math.max(...chartData.map((c) => c.importance), 0.01);

  return (
    <div className="space-y-4">
      {/* Unified Judge Flow - ONE button */}
      <Card title="Unified AI Analysis — Judge Flow" sub="Select spring → RUN AI ANALYSIS → See Why → Recommendation (ONE backend call: GET /api/analysis/{spring_id})">
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex-1 min-w-[200px]"><label className="text-xs font-semibold">Spring</label>
            <select value={selSpring} onChange={e=>setSelSpring(e.target.value)} className={inputCls}>
              {springs.slice(0,60).map(s=> <option key={s.spring_id} value={s.spring_id}>{s.spring_id} — {s.state} — {s.recharge_suitability}%</option>)}
            </select>
          </div>
          <button onClick={runUnified} disabled={analysisBusy} className={btnPrimary + ' !py-2'}>
            {analysisBusy ? 'Analyzing…' : 'RUN AI ANALYSIS'}
          </button>
          {analysis && <span className="text-xs text-slate-500">Timestamp {analysis.timestamp} · Source {analysis.data_source}</span>}
        </div>
        {analysis && (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                ['Recharge', `${analysis.recharge.score}% ${analysis.recharge.class}`],
                ['Water Stress', analysis.assessment.water_stress],
                ['Spring Risk', analysis.assessment.spring_risk],
                ['Confidence', String(analysis.assessment.confidence)],
              ].map(([l,v])=>(
                <div key={l} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
                  <div className="text-[11px] font-semibold uppercase text-slate-500">{l}</div>
                  <div className="text-lg font-bold text-brand-800">{String(v)}</div>
                </div>
              ))}
            </div>
            <div className="grid md:grid-cols-2 gap-3">
              <div className="bg-white border rounded p-3">
                <div className="text-xs font-bold">Why? — Contributing factors (real from recharge engine)</div>
                <div className="space-y-1.5 mt-2">
                  {analysis.why.slice(0,6).map((w:any)=> (
                    <div key={w.factor} className="flex items-center gap-2 text-xs">
                      <span className="w-36 text-slate-600">{w.factor}</span>
                      <div className="flex-1 h-2.5 bg-slate-100 rounded"><div className="h-2.5 rounded bg-brand-600" style={{width:`${Math.min(100,(w.value/20)*100)}%`}}/></div>
                      <span className="w-10 text-right font-semibold">{w.value}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm">
                <div className="font-bold">Recommended Intervention</div>
                <div className="mt-1"><b>{analysis.recommendation.type}</b> — {analysis.recommendation.why}</div>
                <div className="text-xs text-slate-600 mt-1">Village: {analysis.location.village} · Elevation {analysis.location.elevation_m}m</div>
                <div className="text-[11px] text-slate-500 mt-2">Model: {analysis.model.name} ({analysis.model.n_estimators} trees) · Train {analysis.model.n_train} · Val {analysis.model.n_val}</div>
                <div className="text-[11px] text-slate-500">Limitations: Heuristic lift, not measured outcome. Springshed is visual estimate.</div>
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={()=> window.location.href=`/planner?spring=${analysis.spring_id}&type=${analysis.recommendation.type}`} className="text-sm bg-emerald-700 text-white rounded px-4 py-2">Simulate → What-If</button>
              <button onClick={()=> fetch(`/api/reports/${analysis.spring_id}`).then(r=> r.headers.get('content-type')?.includes('pdf') ? r.blob().then(b=>{ const u=URL.createObjectURL(b); const a=document.createElement('a'); a.href=u; a.download=`JAL-RAKSHA-${analysis.spring_id}.pdf`; a.click(); }) : r.json().then(j=> alert(JSON.stringify(j).slice(0,400))))} className="text-sm border rounded px-4 py-2">Generate Report</button>
              <button onClick={async()=>{ const r=await fetch(`/api/analysis/${analysis.spring_id}/explain`,{method:'POST'}); const j=await r.json(); alert(j.explanation); }} className="text-sm border rounded px-4 py-2">Explain (AI)</button>
            </div>
          </div>
        )}
      </Card>

      <div className="grid md:grid-cols-4 gap-3">
        {[['Model', 'Random Forest'], ['R² (validation)', metrics.r2 ?? '—'], ['MAE', metrics.mae ?? '—'], ['RMSE', metrics.rmse ?? '—']].map(([l, v]) => (
          <div key={l} className="bg-white border border-slate-200 rounded-lg px-4 py-3">
            <div className="text-[11px] font-semibold uppercase text-slate-500">{l}</div>
            <div className="text-2xl font-bold text-brand-800">{String(v)}</div>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-500">Metrics computed live from validation_data.csv (n={metrics.n_validation}, train n={metrics.n_train}) — {metrics.computed_from}. Prediction target: recharge suitability (0–100).</p>

      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Feature importance (dynamic from model)" sub="Random Forest · aggregated one-hot importances">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" fontSize={11} /><YAxis type="category" dataKey="name" width={130} fontSize={11} />
              <Tooltip />
              <Bar dataKey="importance">
                {chartData.map((c, i) => <Cell key={i} fill={i === 0 ? '#1c534b' : '#4a9d8b'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="How the AI decides" sub="Same importances, plain view">
          <div className="space-y-2">
            {chartData.map((c) => (
              <div key={c.name} className="text-sm">
                <div className="flex justify-between text-xs"><span>{c.name}</span><span className="font-semibold">{(c.importance * 100).toFixed(1)}%</span></div>
                <div className="h-3 bg-slate-100 rounded mt-0.5">
                  <div className="h-3 rounded bg-brand-600" style={{ width: `${(c.importance / maxI) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="Try the model — live prediction" sub="POST /api/ml/predict · Prototype Decision-Support Estimate">
        <div className="grid md:grid-cols-4 gap-3">
          {(['elevation_m', 'slope_deg', 'annual_rainfall_mm', 'soil_moisture_index', 'distance_to_stream_m', 'lineament_density_index', 'groundwater_depth_m'] as const).map((k) => (
            <Field key={k} label={PRETTY[k] || k}>
              <input type="number" step="any" value={form[k]} onChange={(e) => set(k, +e.target.value)} className={inputCls} />
            </Field>
          ))}
          <Field label="Land use">
            <select value={form.land_use} onChange={(e) => set('land_use', e.target.value)} className={inputCls}>
              {['forest', 'agroforestry', 'agriculture', 'grassland', 'settlement', 'barren'].map((l) => <option key={l}>{l}</option>)}
            </select>
          </Field>
          <Field label="Geology">
            <select value={form.geology} onChange={(e) => set('geology', e.target.value)} className={inputCls}>
              {['fractured_rock', 'weathered_granite', 'sandstone', 'shale', 'clay'].map((g) => <option key={g}>{g}</option>)}
            </select>
          </Field>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button onClick={() => api.mlPredict(form).then(setPred).catch((e) => setErr(e.message))} className={btnPrimary}>Predict</button>
          {pred && <div className="text-sm">Score <b className="text-lg">{pred.score}</b> ({pred.class}) · confidence {pred.confidence} · top feature: {pred.top_feature?.feature}</div>}
        </div>
      </Card>
    </div>
  );
}
