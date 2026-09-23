import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, reportColor } from '../api/client';
import MapView, { ALL_LAYERS } from '../components/MapView';
import { Badge, btnGhost, btnPrimary, Card, Err, Field, inputCls, Loading } from '../components/ui';

const PROBLEMS = ['well_dry', 'spring_stopped', 'level_falling', 'shortage', 'quality', 'structure_damaged', 'flooding', 'other'];
const SEVS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export default function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [clusters, setClusters] = useState<any>(null);
  const [sel, setSel] = useState<any>(null);
  const [err, setErr] = useState('');
  const [ok, setOk] = useState('');
  const [form, setForm] = useState({ problem_type: 'well_dry', description: '', village: '', latitude: '', longitude: '', severity: 'HIGH' });
  // WhatsApp-style demo
  const [chat, setChat] = useState<{ from: string; text: string }[]>([]);
  const [session, setSession] = useState<any>({});
  const [msg, setMsg] = useState('');

  const load = () => {
    api.reports().then((r) => setReports(r.reports)).catch((e) => setErr(e.message));
    api.reportClusters().then(setClusters).catch(() => {});
  };
  useEffect(() => {
    load();
    const t = setInterval(load, 30000); // polling: simplest real-time update
    return () => clearInterval(t);
  }, []);

  const openReport = (id: string) => api.reportGet(id).then(setSel).catch((e) => setErr(e.message));
  const set = (k: string, v: any) => setForm({ ...form, [k]: v });

  const submit = () => {
    setErr(''); setOk('');
    api.reportCreate({
      ...form,
      latitude: Number(form.latitude) || 0, longitude: Number(form.longitude) || 0,
    }).then((r) => {
      setOk(`Your report ${r.report_id} has been submitted successfully. Community reported — pending field verification.`);
      setForm({ problem_type: 'well_dry', description: '', village: '', latitude: '', longitude: '', severity: 'HIGH' });
      load(); setSel(r);
    }).catch((e) => setErr(e.message));
  };

  const sendChat = (text: string) => {
    const m = text.trim();
    if (!m && session.step) return;
    setChat((c) => [...c, { from: 'villager', text: m || '(start)' }]);
    setMsg('');
    api.reportChat(session, m).then((r) => {
      setSession(r.session || {});
      setChat((c) => [...c, { from: 'system', text: r.reply }]);
      if (r.done) { load(); if (r.report_id) openReport(r.report_id); }
    }).catch(() => setChat((c) => [...c, { from: 'system', text: 'Network error — please retry.' }]));
  };

  return (
    <div className="space-y-4">
      <div className="grid lg:grid-cols-[340px_1fr_360px] gap-4">
        <Card title="Report Water Problem" sub="Community reported — pending field verification">
          <div className="space-y-2">
            <Field label="Problem type">
              <select value={form.problem_type} onChange={(e) => set('problem_type', e.target.value)} className={inputCls}>
                {PROBLEMS.map((p) => <option key={p} value={p}>{p.replace(/_/g, ' ')}</option>)}
              </select>
            </Field>
            <Field label="Description"><input value={form.description} onChange={(e) => set('description', e.target.value)} placeholder="Our well went dry" className={inputCls} /></Field>
            <Field label="Village"><input value={form.village} onChange={(e) => set('village', e.target.value)} placeholder="Example Village" className={inputCls} /></Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Latitude"><input value={form.latitude} onChange={(e) => set('latitude', e.target.value)} placeholder="23.46" className={inputCls} /></Field>
              <Field label="Longitude"><input value={form.longitude} onChange={(e) => set('longitude', e.target.value)} placeholder="84.96" className={inputCls} /></Field>
            </div>
            <Field label="Severity">
              <select value={form.severity} onChange={(e) => set('severity', e.target.value)} className={inputCls}>
                {SEVS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <button onClick={submit} className={btnPrimary + ' w-full'}>Submit Report</button>
            {ok && <div className="text-xs text-emerald-700 font-semibold">{ok}</div>}
            {err && <div className="text-xs text-red-700">{err}</div>}
          </div>
        </Card>

        <div className="space-y-3">
          <div className="border border-slate-300 rounded-lg overflow-hidden" style={{ height: 480 }}>
            <MapView springs={[]} villages={[]} wells={[]} grid={[]} interventions={[]}
              layers={{ ...ALL_LAYERS }}
              reports={reports} center={[22.5, 79.5]} zoom={5} onReportClick={openReport} />
          </div>
          <Card title={`Reports (${reports.length})`} sub="Auto-refreshes every 30s · click for detail">
            {reports.length === 0 ? <div className="text-sm text-slate-500">No reports yet — submit the first one.</div> : (
              <div className="max-h-[260px] overflow-y-auto divide-y divide-slate-100">
                {reports.map((r) => (
                  <button key={r.report_id} onClick={() => openReport(r.report_id)}
                    className={`w-full text-left py-2 px-1 hover:bg-slate-50 ${sel?.report_id === r.report_id ? 'bg-brand-50' : ''}`}>
                    <div className="text-sm font-bold">
                      {r.severity === 'CRITICAL' ? '🔴' : '🔵'} {r.report_id}{' '}
                      <span className="text-xs" style={{ color: reportColor(r.status) }}>{String(r.status).replace(/_/g, ' ')}</span>
                    </div>
                    <div className="text-xs text-slate-500">
                      {String(r.problem_type).replace(/_/g, ' ')} · {r.village} · {r.severity} ·
                      station {r.nearest_station_id || '—'} ({r.risk_level || '—'})
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div className="space-y-3">
          {!sel ? <Loading label="Select a report…" /> : (
            <Card title={`${sel.report_id}`} sub="Community reported — pending field verification">
              <dl className="text-sm space-y-1">
                <div className="flex justify-between"><dt className="text-slate-500">Problem</dt><dd className="font-semibold">{String(sel.problem_type).replace(/_/g, ' ')}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Village</dt><dd className="font-semibold">{sel.village}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Severity</dt><dd className="font-bold">{sel.severity}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Time</dt><dd className="font-semibold text-xs">{String(sel.created_at).slice(0, 16).replace('T', ' ')}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Status</dt><dd className="font-bold" style={{ color: reportColor(sel.status) }}>{String(sel.status).replace(/_/g, ' ')}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Nearest station</dt><dd className="font-semibold">{sel.nearest_station_id || '—'}{sel.nearest_station ? ` (${sel.nearest_station.distance_km} km)` : ''}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">GW risk</dt><dd className="font-bold">{sel.risk_level || '—'}</dd></div>
              </dl>
              {sel.verification && (
                <div className="text-xs mt-2 p-2 bg-slate-50 rounded border border-slate-200">
                  <div className="font-semibold">Station cross-check ({sel.verification.station_id})</div>
                  <div>Trend: {sel.verification.station_trend} · Rainfall anomaly: {sel.verification.rainfall_anomaly_pct ?? '—'}% · Status: {sel.verification.station_risk}</div>
                  <div className="mt-1">{sel.verification.verdict}</div>
                </div>
              )}
              <div className="flex gap-2 mt-3">
                <select id="jr-status" className={inputCls + ' !w-auto'} defaultValue={sel.status}>
                  {['NEW', 'UNDER_REVIEW', 'ESCALATED', 'RESOLVED'].map((s) => <option key={s}>{s}</option>)}
                </select>
                <button onClick={() => {
                  const v = (document.getElementById('jr-status') as HTMLSelectElement).value;
                  api.reportStatus(sel.report_id, v).then((r) => { setSel(r); load(); }).catch((e) => setErr(e.message));
                }} className={btnGhost}>Update</button>
              </div>
              <div className="flex gap-2 mt-2">
                <button onClick={() => api.reportReverify(sel.report_id).then((r) => { setSel(r); load(); }).catch((e) => setErr(e.message))} className={btnGhost}>Re-check station</button>
                <Link to="/planner" className={btnPrimary + ' flex-1 text-center'}>Simulate Intervention</Link>
              </div>
            </Card>
          )}
          <Card title="Report clusters" sub="Prototype prioritization rule">
            {!clusters ? <Loading /> : clusters.clusters.filter((c: any) => c.report_count >= 2).length === 0 ? (
              <div className="text-xs text-slate-500">No clusters yet. {clusters.rule}</div>
            ) : (
              <ul className="text-sm space-y-1">
                {clusters.clusters.filter((c: any) => c.report_count >= 2).map((c: any) => (
                  <li key={c.station_id}>⚠ {c.station_id}: <b>{c.report_count} reports</b> — {c.attention.replace(/_/g, ' ')}</li>
                ))}
              </ul>
            )}
          </Card>
          <Card title="WhatsApp/SMS demo" sub="Prototype simulation — no real messaging connected">
            <div className="space-y-1.5 max-h-56 overflow-y-auto border border-slate-100 rounded p-2 bg-slate-50">
              {chat.length === 0 && <div className="text-xs text-slate-500">Press Start, then answer as the villager.</div>}
              {chat.map((m, i) => (
                <div key={i} className={`text-xs rounded px-2 py-1 max-w-[90%] ${m.from === 'villager' ? 'bg-brand-700 text-white ml-auto' : 'bg-white border border-slate-200'}`}>
                  <b>{m.from === 'villager' ? 'VILLAGER' : 'SYSTEM'}:</b> {m.text}
                </div>
              ))}
            </div>
            <div className="flex gap-2 mt-2">
              <input value={msg} onChange={(e) => setMsg(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && sendChat(msg)}
                placeholder="Type reply…" className={inputCls} />
              <button onClick={() => { setChat([]); setSession({}); sendChat(''); }} className={btnGhost}>Start</button>
              <button onClick={() => sendChat(msg)} className={btnPrimary}>Send</button>
            </div>
          </Card>
        </div>
      </div>
      <div><Badge tone="info">Reports update live on the map (30s polling) · Groundwater cross-check: AI/Prototype Decision Support</Badge></div>
    </div>
  );
}
