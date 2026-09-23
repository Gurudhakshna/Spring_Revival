import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { api } from './api/client';
import { Badge, DemoBadge } from './components/ui';

const NAV = [
  ['/', 'Dashboard'], ['/map', 'Recharge Map'], ['/springs', 'Springs'],
  ['/early-warning', 'Early Warning'], ['/reports', 'Reports'],
  ['/planner', 'Planner'], ['/ai', 'AI Analysis'], ['/field', 'Field'], ['/data', 'Data'], ['/about', 'About'],
];

export default function App() {
  const [areas, setAreas] = useState<any[]>([]);
  const [area, setArea] = useState('prototype');
  const [demo, setDemo] = useState(() => localStorage.getItem('jr-demo') !== 'off');
  const loc = useLocation();

  useEffect(() => { api.studyAreas().then((r) => setAreas(r.areas)).catch(() => {}); }, []);
  useEffect(() => { localStorage.setItem('jr-demo', demo ? 'on' : 'off'); }, [demo]);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-brand-900 text-white">
        <div className="px-4 py-3 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-3 mr-auto">
            <div className="w-9 h-9 rounded bg-white text-brand-800 flex items-center justify-center text-xl font-bold">J</div>
            <div>
              <div className="font-extrabold tracking-wide text-lg leading-tight">JAL-RAKSHA AI</div>
              <div className="text-[11px] text-brand-100">Spring Revival &amp; Recharge Planning · AI-powered decision support for sustainable spring revival</div>
            </div>
          </div>
          <label className="text-xs flex items-center gap-2">
            <span className="text-brand-100 font-semibold">Study Area</span>
            <select value={area} onChange={(e) => setArea(e.target.value)}
              className="text-slate-800 text-xs rounded px-2 py-1">
              {(areas.length ? areas : [{ id: 'prototype', name: 'Prototype Study Area' }]).map((a) => (
                <option key={a.id} value={a.id} disabled={a.active === false}>{a.name}</option>
              ))}
            </select>
          </label>
          <button onClick={() => setDemo(!demo)}
            className={`text-xs font-bold rounded px-3 py-1.5 border ${demo ? 'bg-amber-400 text-amber-950 border-amber-300' : 'border-brand-300 text-white'}`}
            title="Toggle demo-data banner">
            {demo ? 'DEMO MODE · ON' : 'DEMO MODE · OFF'}
          </button>
        </div>
        <nav className="bg-brand-800 px-4 flex gap-1 overflow-x-auto">
          {NAV.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `text-[13px] font-semibold px-3 py-2 whitespace-nowrap ${isActive ? 'bg-white text-brand-900 rounded-t' : 'text-brand-100 hover:text-white'}`}>
              {label}
            </NavLink>
          ))}
          <span className="ml-auto hidden md:flex items-center pb-1">
            <Badge tone="info">Prototype Decision-Support Estimate</Badge>
          </span>
        </nav>
      </header>
      {demo && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-1.5 text-center">
          <span className="text-xs font-semibold text-amber-900">DEMO MODE — Synthetic Data · </span>
          <span className="text-xs text-amber-800">All values are illustrative. Replace with validated government/field data before operational use.</span>
        </div>
      )}
      <div className="px-4 pt-2 flex gap-2 items-center">
        <DemoBadge />
        <span className="text-[11px] text-slate-500">Route: {loc.pathname}</span>
      </div>
      <main className="p-4 flex-1 w-full max-w-[1400px] mx-auto">
        <Outlet />
      </main>
      <footer className="px-4 py-3 text-[11px] text-slate-500 border-t border-slate-200 bg-white">
        JAL-RAKSHA AI · SIH26240 prototype · Predictions are prototype decision-support estimates — field validation required · OSM © OpenStreetMap contributors
      </footer>
    </div>
  );
}
