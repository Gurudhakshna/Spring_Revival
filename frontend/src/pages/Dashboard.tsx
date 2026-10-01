import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import { Card, Err, Kpi, Loading } from '../components/ui';

export default function Dashboard() {
  const [d, setD] = useState<any>(null);
  const [rain, setRain] = useState<any>(null);
  const [prio, setPrio] = useState<any[]>([]);
  const [ew, setEw] = useState<any>(null);
  const [err, setErr] = useState('');

  const load = () => {
    setErr('');
    Promise.all([api.dashboard(), api.rainfall(), api.priorities()])
      .then(([dash, r, p]) => { setD(dash); setRain(r); setPrio(p.priorities.slice(0, 6)); })
      .catch((e) => setErr(e.message));
    api.ewSummary(1).then(setEw).catch(() => {});
  };
  useEffect(load, []);

  if (err) return <Err message={err} onRetry={load} />;
  if (!d) return <Loading label="Loading dashboard…" />;

  const classData = [
    { name: 'High (≥70)', count: d.recharge_classes.HIGH, fill: '#15803d' },
    { name: 'Medium (45–70)', count: d.recharge_classes.MEDIUM, fill: '#d97706' },
    { name: 'Low (<45)', count: d.recharge_classes.LOW, fill: '#b91c1c' },
  ];
  const annual = (rain?.annual || []).map((r: any) => ({ year: r.year, mm: Number(r.annual_rainfall_mm) }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Kpi label="Total Springs" value={String(d.total_springs)} hint={`${d.perennial_springs} perennial · ${d.seasonal_springs} seasonal`} />
        <Kpi label="Avg Recharge Suitability" value={`${d.avg_recharge_suitability}%`} hint="Prototype estimate" />
        <Kpi label="High Priority Zones" value={String(d.high_priority_zones)} hint="Priority ≥ 65" />
        <Kpi label="Villages Covered" value={String(d.villages_covered)} hint={`${d.total_wells} wells mapped`} />
        <Kpi label="Potential Intervention Sites" value={String(d.potential_intervention_sites)} hint={`${d.intervention_types} intervention types`} />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Springs by recharge class" sub="Dynamic from loaded dataset">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={classData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" fontSize={12} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count">{classData.map((c) => <Cell key={c.name} fill={c.fill} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Annual rainfall (prototype)" sub="Source: Synthetic Prototype Dataset">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={annual}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" fontSize={11} />
              <YAxis fontSize={11} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="mm" name="Rainfall (mm)" stroke="#20665b" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {ew && (
        <Card title="Groundwater Early Warning" sub="Real monitoring data · AI/Prototype Decision Support"
          right={<Link to="/early-warning" className="text-xs font-semibold text-brand-700 underline">Open Early Warning</Link>}>
          <div className="flex flex-wrap gap-4 text-sm">
            <span><b className="text-lg">{ew.count}</b> active warnings</span>
            <span className="text-red-700 font-semibold">🔴 {ew.levels?.CRITICAL ?? 0} critical</span>
            <span className="text-orange-600 font-semibold">🟠 {ew.levels?.WARNING ?? 0} warning</span>
            <span className="text-amber-600 font-semibold">🟡 {ew.levels?.WATCH ?? 0} watch</span>
            <span className="text-xs text-slate-500 ml-auto">updated {ew.last_updated}</span>
          </div>
        </Card>
      )}

      <Card title="Top priority springs" sub="Transparent priority score — see Planner / Springs for the formula"
        right={<Link to="/springs" className="text-xs font-semibold text-brand-700 underline">Open Springs</Link>}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-slate-500 border-b">
              <th className="py-1 pr-3">Spring</th><th className="pr-3">Score</th><th className="pr-3">Class</th>
              <th className="pr-3">Components (R/V/P/F/W)</th><th>Why?</th>
            </tr></thead>
            <tbody>
              {prio.map((p) => (
                <tr key={p.spring_id} className="border-b border-slate-100">
                  <td className="py-1.5 pr-3 font-semibold">{p.spring_id}</td>
                  <td className="pr-3">{p.priority_score}</td>
                  <td className="pr-3"><span className="text-xs font-bold">{p.priority_class}</span></td>
                  <td className="pr-3 text-xs text-slate-600">
                    {p.components.recharge_suitability}/{p.components.spring_vulnerability}/{p.components.population_dependency}/{p.components.intervention_feasibility}/{p.components.water_stress}
                  </td>
                  <td className="text-xs text-slate-600">{p.why.slice(0, 2).join(' · ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
