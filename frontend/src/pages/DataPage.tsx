import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Card, Err, inputCls, Loading } from '../components/ui';

const TABS = ['springs', 'wells', 'villages', 'rainfall', 'training'] as const;

export default function DataPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>('springs');
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState('');
  const [q, setQ] = useState('');
  const [sortK, setSortK] = useState('');
  const [sortD, setSortD] = useState<1 | -1>(1);

  useEffect(() => {
    setErr(''); setData(null);
    const loaders: Record<string, Promise<any>> = {
      springs: api.springs(), wells: api.wells(), villages: api.villages(),
      rainfall: api.rainfall(), training: api.trainingData(200),
    };
    loaders[tab].then(setData).catch((e) => setErr(e.message));
  }, [tab]);

  let rows: any[] = [];
  let cols: string[] = [];
  if (data) {
    if (tab === 'springs') { rows = data.springs; cols = ['spring_id', 'nearby_village', 'elevation_m', 'discharge_lpm', 'seasonality', 'recharge_suitability', 'land_use', 'geology']; }
    if (tab === 'wells') { rows = data.wells; cols = ['well_id', 'nearby_village', 'well_type', 'depth_m', 'water_level_m']; }
    if (tab === 'villages') { rows = data.villages; cols = ['village_id', 'name', 'block', 'population', 'households', 'elevation_m']; }
    if (tab === 'rainfall') { rows = [...(data.monthly || []), ...data.annual.map((a: any) => ({ month: a.year, month_num: '', rainfall_mm: a.annual_rainfall_mm, rainy_days: '' }))]; cols = ['month', 'month_num', 'rainfall_mm', 'rainy_days']; }
    if (tab === 'training') { rows = data.training.rows; cols = data.training.columns; }
  }
  if (q) {
    const needle = q.toLowerCase();
    rows = rows.filter((r) => Object.values(r).join(' ').toLowerCase().includes(needle));
  }
  if (sortK) {
    rows = [...rows].sort((a, b) => {
      const x = a[sortK], y = b[sortK];
      const nx = Number(x), ny = Number(y);
      if (!isNaN(nx) && !isNaN(ny) && x !== '' && y !== '') return (nx - ny) * sortD;
      return String(x).localeCompare(String(y)) * sortD;
    });
  }
  const clickSort = (c: string) => {
    if (sortK === c) setSortD(sortD === 1 ? -1 : 1);
    else { setSortK(c); setSortD(1); }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-center">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`text-sm font-semibold rounded px-3 py-1.5 border ${tab === t ? 'bg-brand-700 text-white border-brand-700' : 'border-slate-300 bg-white'}`}>
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search / filter records…" className={inputCls + ' !w-64 ml-auto'} />
      </div>
      <Card title={`${tab} — ${rows.length} records`} sub="Source: Synthetic Prototype Dataset · click a column to sort">
        {err ? <Err message={err} /> : !data ? <Loading /> : (
          <div className="overflow-auto max-h-[560px]">
            <table className="w-full text-xs whitespace-nowrap">
              <thead className="sticky top-0 bg-slate-50">
                <tr>{cols.map((c) => (
                  <th key={c} onClick={() => clickSort(c)} className="text-left font-bold text-slate-600 px-2 py-1.5 border-b cursor-pointer hover:text-brand-700">
                    {c}{sortK === c ? (sortD === 1 ? ' ▲' : ' ▼') : ''}
                  </th>
                ))}</tr>
              </thead>
              <tbody>
                {rows.slice(0, 300).map((r, i) => (
                  <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                    {cols.map((c) => <td key={c} className="px-2 py-1 text-slate-700">{String(r[c] ?? '')}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
