import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { btnPrimary, Card, Err, Field, inputCls, Loading } from '../components/ui';

export default function CropAdvisorPage(){
  const [springs,setSprings]=useState<any[]>([]);
  const [sel,setSel]=useState('SPR-001');
  const [result,setResult]=useState<any>(null);
  const [custom,setCustom]=useState({recharge:50, rainfall:800, soil_moisture:0.5, district:''});
  const [explain,setExplain]=useState('');
  const [err,setErr]=useState('');
  const [busy,setBusy]=useState(false);
  const load=()=>{
    api.springs().then(r=> { setSprings(r.springs); if(r.springs.length) setSel(r.springs[0].spring_id); }).catch(()=>{});
  };
  useEffect(load,[]);
  const runForSpring=async()=>{
    setBusy(true); setErr(''); setExplain(''); setResult(null);
    try{ const r=await api.cropAdvisor({spring_id: sel}); setResult(r); } catch(e:any){ setErr(e.message);} finally{ setBusy(false);}
  };
  const runCustom=async()=>{
    setBusy(true); setErr(''); setExplain('');
    try{ const r=await api.cropAdvisorPost(custom); setResult(r); } catch(e:any){ setErr(e.message);} finally{ setBusy(false);}
  };
  const runExplain=async()=>{
    if(!result) return;
    try{
      const body = result.spring_id ? {spring_id: result.spring_id} : custom;
      const r=await api.cropAdvisorExplain(body);
      setExplain(r.explanation || JSON.stringify(r).slice(0,400));
    }catch(e:any){ setErr(e.message); }
  };
  // REMOVED auto-run on sel change — user must click Advise for Spring
  return (
    <div className="space-y-4">
      <Card title="Smart Crop Advisor — Water-Aware Farming" sub="Uses recharge + IMD rainfall + soil to recommend crops that WILL survive. Prototype Decision-Support Estimate.">
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex-1 min-w-[220px]"><label className="text-xs font-semibold">Spring (auto uses its water data)</label><select value={sel} onChange={e=>setSel(e.target.value)} className={inputCls}>{springs.slice(0,60).map(s=> <option key={s.spring_id} value={s.spring_id}>{s.spring_id} — {s.state} — {s.recharge_suitability}% — {s.annual_rainfall_mm}mm</option>)}</select></div>
          <button onClick={runForSpring} disabled={busy} className={btnPrimary}>{busy?'Analyzing…':'Advise for Spring'}</button>
          <span className="text-xs text-slate-500">or custom below →</span>
        </div>
        <div className="mt-4 grid md:grid-cols-4 gap-2">
          <Field label="Recharge %"><input type="number" value={custom.recharge} onChange={e=>setCustom({...custom, recharge: Number(e.target.value)})} className={inputCls}/></Field>
          <Field label="Rainfall mm"><input type="number" value={custom.rainfall} onChange={e=>setCustom({...custom, rainfall: Number(e.target.value)})} className={inputCls}/></Field>
          <Field label="Soil moisture 0-1"><input type="number" step="0.1" value={custom.soil_moisture} onChange={e=>setCustom({...custom, soil_moisture: Number(e.target.value)})} className={inputCls}/></Field>
          <Field label="District (for soil)"><input value={custom.district} onChange={e=>setCustom({...custom, district: e.target.value})} placeholder="Anantapur" className={inputCls}/></Field>
        </div>
        <div className="mt-2 flex gap-2">
          <button onClick={runCustom} disabled={busy} className="text-sm border border-slate-300 rounded px-4 py-2 hover:bg-slate-50">Advise for Custom</button>
          <button onClick={runExplain} className="text-sm border rounded px-3 py-2">Explain (AI)</button>
        </div>
        {err && <Err message={err} />}
        {explain && <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded text-sm">{explain}</div>}
      </Card>

      {!result ? <div className="text-center py-8 text-sm text-slate-500 border border-dashed rounded-lg bg-slate-50">👆 Select a spring and click <b>Advise for Spring</b> to see recommendations — or use custom values below and click <b>Advise for Custom</b></div> : (
        <>
          <div className="grid md:grid-cols-3 gap-4">
            <Card title={`✅ Recommended (${result.counts?.recommended||0})`} sub="Will survive with your water">
              <div className="space-y-2">
                {result.recommended?.map((c:any)=>(
                  <div key={c.crop} className="border border-emerald-200 bg-emerald-50 rounded p-2">
                    <div className="font-bold text-emerald-800 text-sm">{c.crop} <span className="text-xs font-normal">({c.water_min_mm}-{c.water_max_mm}mm)</span></div>
                    <div className="text-xs text-slate-600">{c.season} · {c.days}d · {c.districts}</div>
                    <div className="text-xs mt-1">{c.reason}</div>
                  </div>
                ))}
                {!result.recommended?.length && <div className="text-xs text-slate-500">No perfect match — see Caution</div>}
              </div>
            </Card>
            <Card title={`⚠️ Caution (${result.counts?.caution||0})`} sub="Borderline — needs care">
              <div className="space-y-2">
                {result.caution?.map((c:any)=>(
                  <div key={c.crop} className="border border-amber-200 bg-amber-50 rounded p-2">
                    <div className="font-bold text-amber-800 text-sm">{c.crop}</div>
                    <div className="text-xs text-slate-600">{c.season}</div>
                    <div className="text-xs mt-1">{c.reason}</div>
                  </div>
                ))}
              </div>
            </Card>
            <Card title={`❌ Avoid (${result.counts?.avoid||0})`} sub="Will fail with your water">
              <div className="space-y-2">
                {result.avoid?.map((c:any)=>(
                  <div key={c.crop} className="border border-red-200 bg-red-50 rounded p-2">
                    <div className="font-bold text-red-800 text-sm">{c.crop}</div>
                    <div className="text-xs text-slate-600">{c.water_min_mm}-{c.water_max_mm}mm · needs {c.recharge_min}%</div>
                    <div className="text-xs mt-1">{c.reason}</div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
          <Card title="Input used" sub="Real IMD + soil integrated if district found">
            <div className="text-xs space-y-1">
              <div>Recharge: <b>{result.input?.recharge}%</b> · Rainfall: <b>{result.input?.rainfall_mm}mm</b> · Soil moisture: {result.input?.soil_moisture} · District: {result.input?.district || '-'} {result.input?.soil?.district ? `(soil Zn ${result.input.soil.zn}%)` : ''}</div>
              <div className="text-slate-500">{result.disclaimer}</div>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
