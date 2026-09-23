import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Card, Err, inputCls, Loading } from '../components/ui';

const TABS = ['springs', 'wells', 'villages', 'rainfall', 'training', 'imd_normal', 'historical', 'soil', 'daily'] as const;
const TAB_LABELS: Record<string,string> = {springs:'Springs', wells:'Wells', villages:'Villages', rainfall:'Rainfall (Synthetic)', training:'Training', imd_normal:'IMD Normal (641)', historical:'Historical 1901-2017 (4188)', soil:'Soil (673)', daily:'Daily (8790)'};

export default function DataPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>('springs');
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState('');
  const [q, setQ] = useState('');
  const [sortK, setSortK] = useState('');
  const [sortD, setSortD] = useState<1 | -1>(1);

  const [realQ, setRealQ] = useState('');
  useEffect(() => {
    setErr(''); setData(null);
    const loaders: Record<string, Promise<any>> = {
      springs: api.springs(), wells: api.wells(), villages: api.villages(),
      rainfall: api.rainfall(), training: api.trainingData(200),
      imd_normal: api.rainfallNormal({limit: 50, q: realQ || undefined}),
      historical: api.rainfallHistorical({limit: 50, subdivision: realQ || undefined}),
      soil: api.soil({q: realQ || undefined, limit: 50}),
      daily: api.rainfallDaily({state: realQ || undefined, limit: 20}),
    };
    loaders[tab].then(setData).catch((e) => setErr(e.message));
  }, [tab, realQ]);

  let rows: any[] = [];
  let cols: string[] = [];
  let sourceNote = "Source: Synthetic Prototype Dataset";
  if (data) {
    if (tab === 'springs') { rows = data.springs; cols = ['spring_id', 'nearby_village', 'state', 'elevation_m', 'discharge_lpm', 'seasonality', 'recharge_suitability', 'land_use', 'geology']; }
    if (tab === 'wells') { rows = data.wells; cols = ['well_id', 'nearby_village', 'state', 'well_type', 'depth_m', 'water_level_m']; }
    if (tab === 'villages') { rows = data.villages; cols = ['village_id', 'name', 'state', 'block', 'population', 'households', 'elevation_m']; }
    if (tab === 'rainfall') { rows = [...(data.monthly || []), ...data.annual.map((a: any) => ({ month: a.year, month_num: '', rainfall_mm: a.annual_rainfall_mm, rainy_days: '' }))]; cols = ['month', 'month_num', 'rainfall_mm', 'rainy_days']; }
    if (tab === 'training') { rows = data.training.rows; cols = data.training.columns; }
    if (tab === 'imd_normal') { rows = data.rows || data; cols = ['STATE_UT_NAME','DISTRICT','JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC','ANNUAL']; sourceNote = "Source: IMD District-wise Normal — 641 districts, Real data from Spring_Revival Db";}
    if (tab === 'historical') { rows = data.rows || data; cols = ['SUBDIVISION','YEAR','JAN','FEB','JUN','JUL','AUG','SEP','ANNUAL']; sourceNote = "Source: IMD 1901-2017 Subdivision — 4188 records, Real";}
    if (tab === 'soil') { rows = data.rows || data; cols = ['district','zn','fe','cu','mn','b','s']; sourceNote = "Source: Soil micronutrients — 673 districts, % values, Real";}
    if (tab === 'daily') { rows = data.rows || data; cols = ['state','district','month','1st','2nd','3rd','15th','30th']; sourceNote = "Source: IMD Daily District-wise — 8790 records, Real";}
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

  const [uploadType,setUploadType]=useState('springs');
  const [uploadFile,setUploadFile]=useState<File|null>(null);
  const [uploadRes,setUploadRes]=useState<any>(null);
  const doUpload=async()=>{
    if(!uploadFile) return;
    const fd=new FormData(); fd.append('file', uploadFile);
    const r=await fetch(`/api/data/upload?type=${uploadType}`,{method:'POST', body:fd});
    const j=await r.json(); setUploadRes(j);
  };

  return (
    <div className="space-y-3">
      <Card title="Data Management — Upload & Validate" sub="Admin: Upload CSV (springs/villages/wells) → Validate header contract → Preview → Import history">
        <div className="flex flex-wrap gap-2 items-end">
          <div><label className="text-xs font-semibold">Type</label><select value={uploadType} onChange={e=>setUploadType(e.target.value)} className={inputCls}><option>springs</option><option>villages</option><option>wells</option></select></div>
          <div><label className="text-xs font-semibold">CSV File</label><input type="file" accept=".csv" onChange={e=>setUploadFile(e.target.files?.[0]||null)} className={inputCls}/></div>
          <button onClick={doUpload} className="text-sm bg-brand-700 text-white rounded px-4 py-2">Validate & Preview</button>
          <button onClick={async()=>{ const r=await api.dataHistory(); setUploadRes({history:r.history}); }} className="text-sm border rounded px-3 py-2">History</button>
        </div>
        {uploadRes && <pre className="mt-3 text-xs bg-slate-50 border rounded p-3 overflow-auto max-h-48">{JSON.stringify(uploadRes,null,2)}</pre>}
        <div className="text-[11px] text-slate-500 mt-2">Required springs: spring_id,latitude,longitude,recharge_suitability · villages: village_id,name,latitude,longitude · wells: well_id,latitude,longitude,depth_m · Errors shown before import.</div>
      </Card>

      <div className="flex flex-wrap gap-1 items-center">
        {TABS.map((t) => (
          <button key={t} onClick={() => { setTab(t); setRealQ(''); }} title={TAB_LABELS[t]}
            className={`text-xs font-semibold rounded px-2.5 py-1.5 border ${tab === t ? 'bg-brand-700 text-white border-brand-700' : 'border-slate-300 bg-white'}`}>
            {TAB_LABELS[t]}
          </button>
        ))}
        <div className="ml-auto flex gap-2">
          <input value={realQ} onChange={(e) => setRealQ(e.target.value)} placeholder={['imd_normal','historical','soil','daily'].includes(tab) ? 'Filter real data (state/district)...' : 'Search...'} className={inputCls + ' !w-56'} />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search / filter rows…" className={inputCls + ' !w-40'} />
        </div>
      </div>
      <Card title={`${TAB_LABELS[tab]} — ${rows.length} records`} sub={`${sourceNote} · click a column to sort`}>
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
