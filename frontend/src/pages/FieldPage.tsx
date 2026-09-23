import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { btnPrimary, Card, Err, Field, inputCls, Loading } from '../components/ui';

export default function FieldPage(){
  const [springs,setSprings]=useState<any[]>([]);
  const [obs,setObs]=useState<any[]>([]);
  const [err,setErr]=useState('');
  const [form,setForm]=useState({spring_id:'SPR-001', observer_name:'', discharge_lpm:'', water_quality:'', notes:'', latitude:'', longitude:''});
  const [busy,setBusy]=useState(false);
  const load=()=>{
    api.springs().then(r=> setSprings(r.springs)).catch(()=>{});
    api.fieldObservations().then(r=> setObs(r.observations||[])).catch(()=>{});
  };
  useEffect(load,[]);
  const useGPS=()=>{
    if(!navigator.geolocation) return alert('Geolocation not supported');
    navigator.geolocation.getCurrentPosition(p=> setForm({...form, latitude:String(p.coords.latitude.toFixed(5)), longitude:String(p.coords.longitude.toFixed(5))}), ()=> alert('GPS denied'));
  };
  const submit=async()=>{
    if(!form.spring_id) return setErr('Spring required');
    setBusy(true); setErr('');
    try{
      const payload={...form, latitude: form.latitude?Number(form.latitude):0, longitude: form.longitude?Number(form.longitude):0, discharge_lpm: form.discharge_lpm?Number(form.discharge_lpm):null};
      const r=await api.fieldObservationCreate(payload);
      if(r.detail) throw new Error(r.detail);
      setForm({spring_id:'SPR-001', observer_name:'', discharge_lpm:'', water_quality:'', notes:'', latitude:'', longitude:''});
      load();
    }catch(e:any){ setErr(e.message); } finally{ setBusy(false); }
  };
  return (
    <div className="space-y-4">
      <Card title="Field Worker Mode" sub="Record discharge, water quality, GPS, notes — stored in backend/data/field_observations.json (offline queue TODO)">
        <div className="grid md:grid-cols-2 gap-3">
          <Field label="Spring *"><select value={form.spring_id} onChange={e=>setForm({...form,spring_id:e.target.value})} className={inputCls}>{springs.slice(0,60).map(s=> <option key={s.spring_id} value={s.spring_id}>{s.spring_id} — {s.state}</option>)}</select></Field>
          <Field label="Observer"><input value={form.observer_name} onChange={e=>setForm({...form,observer_name:e.target.value})} placeholder="Field Officer name" className={inputCls}/></Field>
          <Field label="Discharge (L/min)"><input type="number" value={form.discharge_lpm} onChange={e=>setForm({...form,discharge_lpm:e.target.value})} className={inputCls}/></Field>
          <Field label="Water quality"><input value={form.water_quality} onChange={e=>setForm({...form,water_quality:e.target.value})} placeholder="clear / turbid / saline" className={inputCls}/></Field>
          <Field label="Latitude"><input value={form.latitude} onChange={e=>setForm({...form,latitude:e.target.value})} className={inputCls}/></Field>
          <Field label="Longitude"><div className="flex gap-2"><input value={form.longitude} onChange={e=>setForm({...form,longitude:e.target.value})} className={inputCls}/><button onClick={useGPS} type="button" className="text-xs border rounded px-2">📍 GPS</button></div></Field>
          <div className="md:col-span-2"><Field label="Notes"><textarea value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})} rows={3} className={inputCls} placeholder="Field notes, vegetation, stream flow..."/></Field></div>
          <div className="md:col-span-2"><Field label="Photo (demo — URL or base64)"><input type="file" accept="image/*" onChange={e=>{
            const f=e.target.files?.[0]; if(!f) return;
            const r=new FileReader(); r.onload=()=> setForm({...form, notes: form.notes + `\n[Photo: ${f.name} ${Math.round(f.size/1024)}KB]`}); r.readAsDataURL(f);
          }} className={inputCls}/></Field></div>
        </div>
        <div className="mt-3 flex gap-2">
          <button onClick={submit} disabled={busy} className={btnPrimary}>{busy?'Submitting…':'Submit Observation'}</button>
          <span className="text-xs text-slate-500 self-center">Connectivity: {navigator.onLine ? '✅ Online' : '⚠️ Offline — will queue (demo)'}</span>
        </div>
        {err && <Err message={err} />}
      </Card>
      <Card title={`Field observations (${obs.length})`} sub="Newest first · pending field verification">
        {!obs.length ? <Loading label="No observations yet — be the first!" /> : (
          <div className="space-y-2">
            {obs.slice(0,20).map((o:any)=>(
              <div key={o.observation_id} className="border border-slate-200 rounded p-3 text-sm">
                <div className="font-bold">{o.observation_id} — {o.spring_id} · {o.observer_name}</div>
                <div className="text-xs text-slate-600">Discharge {o.discharge_lpm ?? '—'} L/min · WQ {o.water_quality || '—'} · {o.latitude},{o.longitude} · {o.created_at}</div>
                <div className="text-sm mt-1">{o.notes}</div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
