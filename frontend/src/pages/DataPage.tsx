import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Card, Err, inputCls, Loading } from '../components/ui';

const TABS = ['springs', 'wells', 'villages', 'rainfall', 'training'] as const;
const REAL_TABS = ['imd_normal', 'historical', 'soil', 'daily'] as const;
const TAB_LABELS: Record<string,string> = {springs:'Springs', wells:'Wells', villages:'Villages', rainfall:'Rainfall (Synthetic)', training:'Training', imd_normal:'IMD Normal (641)', historical:'Historical 1901-2017 (4188)', soil:'Soil (673)', daily:'Daily (8790)'};

export default function DataPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>('springs');
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState('');
  const [q, setQ] = useState('');
  const [sortK, setSortK] = useState('');
  const [sortD, setSortD] = useState<1 | -1>(1);

  const [realTab, setRealTab] = useState<(typeof REAL_TABS)[number]>('imd_normal');
  const [realData, setRealData] = useState<any>(null);
  const [realQ, setRealQ] = useState('');
  const [realErr, setRealErr] = useState('');
  useEffect(() => {
    setErr(''); setData(null);
    const loaders: Record<string, Promise<any>> = {
      springs: api.springs(), wells: api.wells(), villages: api.villages(),
      rainfall: api.rainfall(), training: api.trainingData(200),
    };
    if ((TABS as readonly string[]).includes(tab)) {
      loaders[tab].then(setData).catch((e) => setErr(e.message));
    }
  }, [tab]);
  useEffect(() => {
    setRealErr(''); setRealData(null);
    const realLoaders: Record<string, Promise<any>> = {
      imd_normal: api.rainfallNormal({limit: 50, q: realQ || undefined}),
      historical: api.rainfallHistorical({limit: 50, subdivision: realQ || undefined}),
      soil: api.soil({q: realQ || undefined, limit: 50}),
      daily: api.rainfallDaily({state: realQ || undefined, limit: 20}),
    };
    realLoaders[realTab].then(setRealData).catch((e) => setRealErr(e.message));
  }, [realTab, realQ]);

  let rows: any[] = [];
  let cols: string[] = [];
  let sourceNote = "Source: Synthetic Prototype Dataset";
  if (data) {
    if (tab === 'springs') { rows = data.springs; cols = ['spring_id', 'nearby_village', 'state', 'elevation_m', 'discharge_lpm', 'seasonality', 'recharge_suitability', 'land_use', 'geology']; }
    if (tab === 'wells') { rows = data.wells; cols = ['well_id', 'nearby_village', 'state', 'well_type', 'depth_m', 'water_level_m']; }
    if (tab === 'villages') { rows = data.villages; cols = ['village_id', 'name', 'state', 'block', 'population', 'households', 'elevation_m']; }
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
          <button key={t} onClick={() => setTab(t)} title={TAB_LABELS[t]}
            className={`text-xs font-semibold rounded px-2.5 py-1.5 border ${tab === t ? 'bg-brand-700 text-white border-brand-700' : 'border-slate-300 bg-white'}`}>
            {TAB_LABELS[t]}
          </button>
        ))}
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search / filter rows…" className={inputCls + ' !w-48 ml-auto'} />
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

      <Card title="Real IMD + Soil — Spring_Revival Db" sub="Real data from your Spring_Revival Db — 641 districts, 4188 historical, 673 soil, 8790 daily">
        <div className="flex flex-wrap gap-1 items-center mb-3">
          {REAL_TABS.map((t) => (
            <button key={t} onClick={() => setRealTab(t)} title={TAB_LABELS[t]}
              className={`text-xs font-semibold rounded px-2.5 py-1.5 border ${realTab === t ? 'bg-emerald-700 text-white border-emerald-700' : 'border-slate-300 bg-white'}`}>
              {TAB_LABELS[t]}
            </button>
          ))}
          <input value={realQ} onChange={(e) => setRealQ(e.target.value)} placeholder="Filter real data (state/district)..." className={inputCls + ' !w-64 ml-auto'} />
        </div>
        {realErr ? <Err message={realErr} /> : !realData ? <Loading label="Loading real data…" /> : (
          <div className="overflow-auto max-h-[360px]">
            <table className="w-full text-xs whitespace-nowrap">
              <thead className="sticky top-0 bg-emerald-50">
                <tr>{(realTab==='imd_normal'?['STATE_UT_NAME','DISTRICT','ANNUAL']: realTab==='historical'?['SUBDIVISION','YEAR','ANNUAL']: realTab==='soil'?['district','zn','fe','cu','mn']: ['state','district','month','1st','2nd']).map((c)=>(
                  <th key={c} className="text-left font-bold text-emerald-700 px-2 py-1.5 border-b">{c}</th>
                ))}</tr>
              </thead>
              <tbody>
                {(realData.rows||[]).slice(0,100).map((r:any,i:number)=>(
                  <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                    {(realTab==='imd_normal'?['STATE_UT_NAME','DISTRICT','ANNUAL']: realTab==='historical'?['SUBDIVISION','YEAR','ANNUAL']: realTab==='soil'?['district','zn','fe','cu','mn']: ['state','district','month','1st','2nd']).map((c)=>(
                      <td key={c} className="px-2 py-1 text-slate-700">{String(r[c] ?? '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="text-[11px] text-slate-500 mt-2">{realData.count} records · Source: {realData.source || 'IMD/Soil Real'}</div>
          </div>
        )}
      </Card>
    </div>
  );
}
