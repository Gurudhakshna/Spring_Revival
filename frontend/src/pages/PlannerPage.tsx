import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api, inr } from '../api/client';
import { btnPrimary, Card, Err, Field, inputCls, Loading } from '../components/ui';

export default function PlannerPage() {
  const [catalog, setCatalog] = useState<any[]>([]);
  const [springs, setSprings] = useState<any[]>([]);
  const [type, setType] = useState('check_dam');
  const [springId, setSpringId] = useState('SPR-001');
  const [qty, setQty] = useState(1);
  const [result, setResult] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string|null>(null);
  const showToast = (msg:string) => { setToast(msg); setTimeout(()=>setToast(null), 3000); };

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const springFromUrl = urlParams.get('spring');
    const typeFromUrl = urlParams.get('type');
    if(springFromUrl) setSpringId(springFromUrl);
    if(typeFromUrl) setType(typeFromUrl);
    Promise.all([api.interventions(), api.springs()])
      .then(([c, s]) => { setCatalog(c.interventions); setSprings(s.springs); 
        const initType = typeFromUrl || c.interventions[0]?.type || 'recharge_trench';
        setType(initType); setQty(Number(c.interventions.find((x:any)=>x.type===initType)?.default_qty||1));
        if(springFromUrl) api.analysis(springFromUrl).then(setAnalysis).catch(()=>{});
      })
      .catch((e) => setErr(e.message));
  }, []);

  const simulate = (t = type, q = qty, sid = springId) => {
    setBusy(true); setErr('');
    api.simulate({ intervention_type: t, spring_id: sid, quantity: q })
      .then((r)=>{ setResult(r); api.analysis(sid).then(setAnalysis).catch(()=>{}); showToast(`✓ Simulated: ${r.base_score} → ${r.predicted_score} (+${r.improvement} pts) for ${sid}`); }).catch((e) => setErr(e.message)).finally(() => setBusy(false));
  };
  useEffect(() => { if (catalog.length) simulate(); }, [type, qty, springId]); // eslint-disable-line

  const meta = catalog.find((c) => c.type === type);
  if (err && !catalog.length) return <Err message={err} onRetry={() => window.location.reload()} />;
  if (!catalog.length) return <Loading label="Loading intervention catalog…" />;

  const chart = result ? [
    { name: 'Recharge', Current: result.base_score, Proposed: result.predicted_score },
    { name: 'Priority', Current: analysis?.priority?.priority_score || 40, Proposed: result.priority ? (result.priority==='HIGH'?75: result.priority==='MEDIUM'?60:35) : 50 },
  ] : [];
  const difficultyMap:Record<string,string> = {recharge_trench:'Medium', check_dam:'High', percolation_pond:'Medium', contour_trench:'Low-Medium', vegetation_restoration:'Low', spring_shed_treatment:'Medium', drainage_treatment:'High', infiltration_gallery:'High'};
  const riskMap:Record<string,string> = {recharge_trench:'Low', check_dam:'Medium (stream)', percolation_pond:'Low', contour_trench:'Low', vegetation_restoration:'Very Low', spring_shed_treatment:'Low', drainage_treatment:'Medium', infiltration_gallery:'Medium'};

  return (
    <div className="grid lg:grid-cols-[340px_1fr] gap-4 relative">
      {toast && <div className="fixed top-20 right-4 bg-emerald-700 text-white text-sm font-semibold px-4 py-3 rounded-lg shadow-lg z-50 animate-bounce">{toast}</div>}
      <Card title="Intervention Planner" sub="Prototype scenario estimate — requires field validation">
        <div className="space-y-3">
          <Field label="Intervention type">
            <select value={type} onChange={(e) => { setType(e.target.value); setQty(Number(catalog.find((c) => c.type === e.target.value)?.default_qty || 1)); }} className={inputCls}>
              {catalog.map((c) => <option key={c.type} value={c.type}>{c.name} — {inr(Number(c.unit_cost_inr))} {c.unit}</option>)}
            </select>
          </Field>
          {meta && <><p className="text-xs text-slate-500">{meta.description}</p>
            <div className="text-xs bg-slate-50 rounded p-2 space-y-1">
              <div><b>Difficulty:</b> {difficultyMap[type] || 'Medium'} · <b>Risk:</b> {riskMap[type] || 'Low'}</div>
              <div><b>Why this fits:</b> {analysis?.recommendation?.type===type ? analysis.recommendation.why : meta.description.slice(0,90)}</div>
            </div></>}
          <Field label="Near spring">
            <select value={springId} onChange={(e) => { setSpringId(e.target.value); api.analysis(e.target.value).then(setAnalysis).catch(()=>{}); }} className={inputCls}>
              {springs.map((s) => <option key={s.spring_id} value={s.spring_id}>{s.spring_id} — {s.state} — score {Number(s.recharge_suitability).toFixed(0)} {s.tribal_belt?.slice(0,15)}</option>)}
            </select>
          </Field>
          <Field label={`Quantity (${meta?.unit}) — ${qty}`}>
            <input type="range" min={meta?.min_qty || 1} max={meta?.max_qty || 5} step="1" value={qty}
              onChange={(e) => setQty(Number(e.target.value))} className="w-full" />
          </Field>
          <button onClick={() => simulate()} disabled={busy} className={btnPrimary + ' w-full'}>
            {busy ? 'Simulating…' : 'SIMULATE'}
          </button>
          <p className="text-[11px] text-slate-500">Parameters recalculate live — move the slider and watch the estimate change.</p>
        </div>
      </Card>

      <div className="space-y-4">
        {err && <Err message={err} />}
        {!result ? <Loading label="Run a simulation…" /> : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                ['Current score', String(result.base_score)], ['After intervention', String(result.predicted_score)],
                ['Improvement', `+${result.improvement} pts`], ['Est. cost', inr(result.estimated_cost_inr)],
              ].map(([l, v]) => (
                <div key={l} className="bg-white border border-slate-200 rounded-lg px-4 py-3">
                  <div className="text-[11px] font-semibold uppercase text-slate-500">{l}</div>
                  <div className="text-xl font-bold text-brand-800">{v}</div>
                </div>
              ))}
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <Card title="Current vs Proposed">
                <table className="w-full text-sm">
                  <thead><tr className="text-left text-xs text-slate-500 border-b"><th></th><th>Current</th><th>Proposed</th></tr></thead>
                  <tbody>
                    {result.comparison.rows.map((r: any[]) => (
                      <tr key={r[0]} className="border-b border-slate-100">
                        <td className="py-1.5 font-semibold">{r[0]}</td><td>{r[1]}</td><td className="font-semibold">{r[2]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="text-xs mt-2 space-x-2">
                  <span>Priority: <b>{result.priority}</b></span><span>Risk: <b>{result.risk}</b></span><span>Confidence: <b>{result.confidence}</b></span>
                </div>
              </Card>
              <Card title="Visual improvement">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={chart}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis domain={[0, 100]} /><Tooltip />
                    <Bar dataKey="Current" fill="#94a3b8" /><Bar dataKey="Proposed" fill="#20665b">
                      {chart.map((_, i) => <Cell key={i} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="text-[11px] text-slate-500 mt-1">{result.disclaimer}</div>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
