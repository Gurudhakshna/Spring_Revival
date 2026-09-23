/* Typed API client. All calls go through the FastAPI backend (never demo files). */
export interface Dashboard { [k: string]: any }
export interface Spring { spring_id: string; latitude: number; longitude: number; [k: string]: any }
export interface Village { village_id: string; name: string; latitude: number; longitude: number; [k: string]: any }
export interface Well { well_id: string; latitude: number; longitude: number; [k: string]: any }
export interface GridPoint { id: string; latitude: number; longitude: number; score: number; class: string }

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...init });
  } catch {
    throw new Error('Backend unavailable at localhost:8000. Start it with start-backend (see README).');
  }
  if (!res.ok) throw new Error(`Request failed (${res.status}) for ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => req<any>('/api/health'),
  dashboard: () => req<Dashboard>('/api/dashboard'),
  villages: (q?: { search?: string; state?: string; belt_id?: string }) => {
    const p = new URLSearchParams();
    if (q?.search) p.set('search', q.search);
    if (q?.state) p.set('state', q.state);
    if (q?.belt_id) p.set('belt_id', q.belt_id);
    const s = p.toString();
    return req<{ count: number; villages: Village[] }>(`/api/villages${s ? `?${s}` : ''}`);
  },
  springs: (q?: { search?: string; suitability_class?: string; seasonality?: string; state?: string; belt_id?: string; tribal_belt?: string }) => {
    const p = new URLSearchParams();
    if (q?.search) p.set('search', q.search);
    if (q?.suitability_class) p.set('suitability_class', q.suitability_class);
    if (q?.seasonality) p.set('seasonality', q.seasonality);
    if (q?.state) p.set('state', q.state);
    if (q?.belt_id) p.set('belt_id', q.belt_id);
    if (q?.tribal_belt) p.set('tribal_belt', q.tribal_belt);
    const s = p.toString();
    return req<{ count: number; springs: Spring[] }>(`/api/springs${s ? `?${s}` : ''}`);
  },
  springDetail: (id: string) => req<Spring>(`/api/springs/${encodeURIComponent(id)}`),
  wells: (q?: { state?: string; belt_id?: string }) => {
    const p = new URLSearchParams();
    if (q?.state) p.set('state', q.state);
    if (q?.belt_id) p.set('belt_id', q.belt_id);
    const s = p.toString();
    return req<{ count: number; wells: Well[] }>(`/api/wells${s ? `?${s}` : ''}`);
  },
  rainfall: () => req<{ monthly: any[]; annual: any[] }>('/api/rainfall'),
  rechargeMap: (q?: { belt_id?: string; state?: string }) => {
    const p = new URLSearchParams();
    if (q?.belt_id) p.set('belt_id', q.belt_id);
    if (q?.state) p.set('state', q.state);
    const s = p.toString();
    return req<{ points: any[]; grid: GridPoint[]; weights: any }>(`/api/recharge/map${s ? `?${s}` : ''}`);
  },
  rechargeFor: (id: string) => req<any>(`/api/recharge/${encodeURIComponent(id)}`),
  rechargeCalculate: (body: any) =>
    req<any>('/api/recharge/calculate', { method: 'POST', body: JSON.stringify(body) }),
  mlPredict: (body: any) => req<any>('/api/ml/predict', { method: 'POST', body: JSON.stringify(body) }),
  mlMetrics: () => req<any>('/api/ml/metrics'),
  mlImportance: () => req<any>('/api/ml/feature-importance'),
  interventions: () => req<{ count: number; interventions: any[] }>('/api/interventions'),
  simulate: (body: any) =>
    req<any>('/api/interventions/simulate', { method: 'POST', body: JSON.stringify(body) }),
  priorities: (q?: { state?: string; belt_id?: string }) => {
    const p = new URLSearchParams();
    if (q?.state) p.set('state', q.state);
    if (q?.belt_id) p.set('belt_id', q.belt_id);
    const s = p.toString();
    return req<{ count: number; priorities: any[] }>(`/api/priorities${s ? `?${s}` : ''}`);
  },
  riskFlags: (spring_id?: string) =>
    req<any>(`/api/risk-flags${spring_id ? `?spring_id=${encodeURIComponent(spring_id)}` : ''}`),
  trainingData: (limit = 100) => req<any>(`/api/training-data?limit=${limit}`),
  studyAreas: () => req<{ areas: any[] }>('/api/study-areas'),
  // Unified AI Analysis - ONE call for recharge+risk+priority+why
  analysis: (spring_id: string) => req<any>(`/api/analysis/${encodeURIComponent(spring_id)}`),
  // Field observations
  fieldObservations: () => req<any>('/api/field-observations'),
  fieldObservationCreate: (body: any) => req<any>('/api/field-observations', { method: 'POST', body: JSON.stringify(body) }),
  // Reports
  reportGenerate: (spring_id: string) => req<any>(`/api/reports/${encodeURIComponent(spring_id)}`),
  // Data upload (admin)
  dataUpload: (body: FormData) => fetch('/api/data/upload', { method: 'POST', body }).then(r => r.json()),
  dataHistory: () => req<any>('/api/data/history'),
  // Real IMD + Soil (Spring_Revival Db)
  realSummary: () => req<any>('/api/real/summary'),
  rainfallNormal: (q?: {state?:string; district?:string; q?:string; limit?:number}) => {
    const p=new URLSearchParams(); if(q?.state) p.set('state',q.state); if(q?.district) p.set('district',q.district); if(q?.q) p.set('q',q.q); if(q?.limit) p.set('limit',String(q.limit));
    const s=p.toString(); return req<any>(`/api/rainfall/normal${s?`?${s}`:''}`);
  },
  rainfallHistorical: (q?: {subdivision?:string; from_year?:number; to_year?:number; limit?:number}) => {
    const p=new URLSearchParams(); if(q?.subdivision) p.set('subdivision',q.subdivision); if(q?.from_year) p.set('from_year',String(q.from_year)); if(q?.to_year) p.set('to_year',String(q.to_year)); if(q?.limit) p.set('limit',String(q.limit));
    const s=p.toString(); return req<any>(`/api/rainfall/historical${s?`?${s}`:''}`);
  },
  rainfallDaily: (q?: {state?:string; district?:string; month?:number; limit?:number}) => {
    const p=new URLSearchParams(); if(q?.state) p.set('state',q.state); if(q?.district) p.set('district',q.district); if(q?.month) p.set('month',String(q.month)); if(q?.limit) p.set('limit',String(q.limit));
    const s=p.toString(); return req<any>(`/api/rainfall/daily${s?`?${s}`:''}`);
  },
  soil: (q?: {district?:string; q?:string; limit?:number}) => {
    const p=new URLSearchParams(); if(q?.district) p.set('district',q.district); if(q?.q) p.set('q',q.q); if(q?.limit) p.set('limit',String(q.limit));
    const s=p.toString(); return req<any>(`/api/soil${s?`?${s}`:''}`);
  },
  tribalBeltRainfall: () => req<any>('/api/tribal-belt/rainfall'),
  // ---- Feature 1: groundwater early warning (real dataset, AI/Prototype Decision Support)
  ewStatus: () => req<any>('/api/early-warning/status'),
  ewSummary: (limit = 100) => req<any>(`/api/early-warning/summary?limit=${limit}`),
  ewStations: (q?: { risk?: string; search?: string; limit?: number; offset?: number }) => {
    const p = new URLSearchParams();
    if (q?.risk) p.set('risk', q.risk);
    if (q?.search) p.set('search', q.search);
    if (q?.limit) p.set('limit', String(q.limit));
    if (q?.offset) p.set('offset', String(q.offset));
    const s = p.toString();
    return req<any>(`/api/early-warning/stations${s ? `?${s}` : ''}`);
  },
  ewStation: (id: string) => req<any>(`/api/early-warning/stations/${encodeURIComponent(id)}`),
  ewLeadTime: () => req<any>('/api/early-warning/lead-time'),
  ewForecast: (id: string, horizon_days = 30) =>
    req<any>(`/api/early-warning/forecast/${encodeURIComponent(id)}`, { method: 'POST', body: JSON.stringify({ horizon_days }) }),
  // ---- Feature 2: community reporting (pending field verification)
  reports: (q?: { status?: string; severity?: string }) => {
    const p = new URLSearchParams();
    if (q?.status) p.set('status', q.status);
    if (q?.severity) p.set('severity', q.severity);
    const s = p.toString();
    return req<any>(`/api/community-reports${s ? `?${s}` : ''}`);
  },
  reportGet: (id: string) => req<any>(`/api/community-reports/${encodeURIComponent(id)}`),
  reportCreate: (body: any) =>
    req<any>('/api/community-reports', { method: 'POST', body: JSON.stringify(body) }),
  reportStatus: (id: string, status: string) =>
    req<any>(`/api/community-reports/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  reportReverify: (id: string) =>
    req<any>(`/api/community-reports/${encodeURIComponent(id)}/reverify`, { method: 'POST', body: JSON.stringify({}) }),
  reportClusters: () => req<any>('/api/community-reports/clusters'),
  reportChat: (session: any, message: string) =>
    req<any>('/api/community-reports/chat', { method: 'POST', body: JSON.stringify({ session, message }) }),
};

export const inr = (n: number) => '₹' + Number(n || 0).toLocaleString('en-IN');
export const clsColor = (c: string) =>
  c === 'HIGH' ? '#15803d' : c === 'MEDIUM' ? '#d97706' : '#b91c1c';
export const riskColor = (r: string) =>
  r === 'CRITICAL' ? '#b91c1c' : r === 'WARNING' ? '#ea580c' : r === 'WATCH' ? '#d97706' : '#15803d';
export const reportColor = (s: string) =>
  s === 'ESCALATED' ? '#ea580c' : s === 'UNDER_REVIEW' ? '#d97706' : s === 'RESOLVED' ? '#15803d' : '#1d4ed8';
export const scoreColor = (s: number) =>
  s >= 70 ? '#15803d' : s >= 55 ? '#65a30d' : s >= 45 ? '#d97706' : s >= 30 ? '#ea580c' : '#b91c1c';
