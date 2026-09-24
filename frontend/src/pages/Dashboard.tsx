import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import { Card, Err, Kpi, Loading } from '../components/ui';
import { useStudyArea } from '../App';
import { staggerContainer, bouncyCard, scrollReveal } from '../components/motion';

export default function Dashboard() {
  const { area } = useStudyArea();
  const [d, setD] = useState<any>(null);
  const [rain, setRain] = useState<any>(null);
  const [prio, setPrio] = useState<any[]>([]);
  const [ew, setEw] = useState<any>(null);
  const [realSummary, setRealSummary] = useState<any>(null);
  const [beltRain, setBeltRain] = useState<any>(null);
  const [err, setErr] = useState('');

  const load = () => {
    setErr('');
    const prioQuery = area && area !== 'all' ? { belt_id: area } : undefined;
    Promise.all([api.dashboard(), api.rainfall(), api.priorities(prioQuery)])
      .then(([dash, r, p]) => { setD(dash); setRain(r); setPrio(p.priorities.slice(0, 6)); })
      .catch((e) => setErr(e.message));
    api.ewSummary(1).then(setEw).catch(() => {});
    api.realSummary().then(setRealSummary).catch(()=>{});
    api.tribalBeltRainfall().then(setBeltRain).catch(()=>{});
  };
  useEffect(load, [area]);


  if (err) return <Err message={err} onRetry={load} />;
  if (!d) return <Loading label="Loading dashboard…" />;

  const classData = [
    { name: 'High (≥70)', count: d.recharge_classes.HIGH, fill: '#15803d' },
    { name: 'Medium (45–70)', count: d.recharge_classes.MEDIUM, fill: '#d97706' },
    { name: 'Low (<45)', count: d.recharge_classes.LOW, fill: '#b91c1c' },
  ];
  const annual = (rain?.annual || []).map((r: any) => ({ year: r.year, mm: Number(r.annual_rainfall_mm) }));

  return (
    <motion.div className="space-y-4" initial="hidden" animate="visible" variants={staggerContainer}>
      <motion.div className="grid grid-cols-2 md:grid-cols-5 gap-3" variants={staggerContainer}>
        {[ 
          {label:"Total Springs", value:String(d.total_springs), hint:`${d.perennial_springs} perennial · ${d.seasonal_springs} seasonal`},
          {label:"Avg Recharge Suitability", value:`${d.avg_recharge_suitability}%`, hint:"Prototype estimate"},
          {label:"High Priority Zones", value:String(d.high_priority_zones), hint:"Priority ≥ 65"},
          {label:"Villages Covered", value:String(d.villages_covered), hint:`${d.total_wells} wells mapped`},
          {label:"Potential Intervention Sites", value:String(d.potential_intervention_sites), hint:`${d.intervention_types} intervention types`},
        ].map((k)=>(
          <motion.div key={k.label} variants={bouncyCard} whileHover={{ y: -4, transition:{type:"spring", stiffness:400} }} whileTap={{ scale: 0.97 }}>
            <Kpi label={k.label} value={k.value} hint={k.hint} />
          </motion.div>
        ))}
      </motion.div>

      <motion.div className="grid md:grid-cols-2 gap-4" initial="hidden" whileInView="visible" viewport={{ once:true, amount:0.2 }} variants={staggerContainer}>
        <motion.div variants={scrollReveal} whileHover={{ y: -2 }} transition={{ type:"spring", stiffness:300 }}>
          <Card title="Springs by recharge class" sub="Dynamic from loaded dataset (126 pan-India)">
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
        </motion.div>
        <motion.div variants={scrollReveal} whileHover={{ y: -2 }} transition={{ type:"spring", stiffness:300 }}>
          <Card title="Annual rainfall (prototype)" sub="Source: Synthetic Prototype Dataset (see Data → Historical for Real IMD 1901-2017)">
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
        </motion.div>
      </motion.div>

      {beltRain && (
        <motion.div initial="hidden" whileInView="visible" viewport={{ once:true }} variants={scrollReveal}>
          <Card title="Real IMD Rainfall — Tribal Belt Comparison" sub="Source: IMD District Normal (641 districts) aggregated to 7 belts — Real data from Spring_Revival Db">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 text-xs">
              {Object.entries(beltRain.belts||{}).map(([id, v]: any)=>(
                <motion.div key={id} whileHover={{ scale: 1.03, y: -2 }} whileTap={{ scale: 0.98 }} transition={{ type:"spring", stiffness:400 }}>
                  <div className="bg-slate-50 border rounded p-2 hover:shadow-md transition-shadow">
                    <div className="font-bold text-brand-800">{id.toUpperCase()}</div>
                    <div>{v.districts} districts</div>
                    <div>Annual: <b>{v.avg_annual_mm} mm</b></div>
                    <div>Monsoon: {v.avg_monsoon_mm} mm</div>
                  </div>
                </motion.div>
              ))}
            </div>
            <div className="text-[11px] text-slate-500 mt-2">Example: Jharkhand 1303mm vs Rajasthan 732mm — explains why recharge LOW in desert.</div>
          </Card>
        </motion.div>
      )}
      {realSummary && (
        <motion.div initial="hidden" whileInView="visible" viewport={{ once:true }} variants={scrollReveal}>
          <Card title="Real Data Integrated" sub="Spring_Revival Db — now live via /api/real/*">
            <div className="flex flex-wrap gap-3 text-xs">
              <span className="bg-emerald-50 border border-emerald-200 rounded px-2 py-1">📊 District Normal: <b>{realSummary.district_normal?.rows} districts</b></span>
              <span className="bg-sky-50 border border-sky-200 rounded px-2 py-1">📈 Historical: <b>{realSummary.historical?.rows} records {realSummary.historical?.years}</b></span>
              <span className="bg-amber-50 border border-amber-200 rounded px-2 py-1">🌱 Soil: <b>{realSummary.soil?.rows} districts</b></span>
              <span className="bg-slate-50 border rounded px-2 py-1">Daily: 8790 records</span>
              <Link to="/data" className="ml-auto text-xs font-semibold text-brand-700 underline">Explore in Data → IMD Normal / Soil tabs</Link>
            </div>
          </Card>
        </motion.div>
      )}

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

      <motion.div initial="hidden" whileInView="visible" viewport={{ once:true }} variants={scrollReveal}>
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
                  <motion.tr key={p.spring_id} initial={{ opacity:0, x:-8 }} whileInView={{ opacity:1, x:0 }} viewport={{once:true}} transition={{ delay: 0.02 }} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-1.5 pr-3 font-semibold">{p.spring_id}</td>
                    <td className="pr-3">{p.priority_score}</td>
                    <td className="pr-3"><span className="text-xs font-bold">{p.priority_class}</span></td>
                    <td className="pr-3 text-xs text-slate-600">
                      {p.components.recharge_suitability}/{p.components.spring_vulnerability}/{p.components.population_dependency}/{p.components.intervention_feasibility}/{p.components.water_stress}
                    </td>
                    <td className="text-xs text-slate-600">{p.why.slice(0, 2).join(' · ')}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
