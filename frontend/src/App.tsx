import { createContext, useContext, useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { motion, useScroll, useSpring } from 'framer-motion';
import { api } from './api/client';

export interface StudyAreaContextValue {
  area: string;
  setArea: (a: string) => void;
  areas: any[];
}

export const StudyAreaContext = createContext<StudyAreaContextValue>({
  area: 'all',
  setArea: () => {},
  areas: [],
});

export const useStudyArea = () => useContext(StudyAreaContext);

const NAV = [
  ['/', 'Overview'],
  ['/dashboard', 'Dashboard'],
  ['/map', 'Recharge Map'],
  ['/springs', 'Springs'],
  ['/early-warning', 'Early Warning'],
  ['/reports', 'Reports'],
  ['/planner', 'Planner'],
  ['/ai', 'AI Analysis'],
  ['/crop', 'Crop Advisor'],
  ['/field', 'Field'],
  ['/data', 'Data'],
  ['/about', 'About'],
];

export default function App() {
  const [areas, setAreas] = useState<any[]>([]);
  const [area, setArea] = useState('all');
  const loc = useLocation();
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 200, damping: 30, restDelta: 0.001 });

  useEffect(() => {
    api.studyAreas()
      .then((r) => setAreas(r.areas || []))
      .catch(() => {});
  }, []);

  return (
    <StudyAreaContext.Provider value={{ area, setArea, areas }}>
      <motion.div
        className="fixed top-0 left-0 right-0 h-[3px] bg-emerald-500 origin-left z-[60]"
        style={{ scaleX }}
      />
      <div className="min-h-screen flex flex-col bg-slate-50">
        <motion.header
          initial={{ y: -8, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 400, damping: 28, mass: 0.6 }}
          className="bg-brand-900 text-white shadow-md sticky top-0 z-40 backdrop-blur"
        >
          <div className="px-4 py-3 flex flex-wrap items-center gap-3">
            <NavLink to="/" className="flex items-center gap-3 mr-auto hover:opacity-95 transition-opacity">
              <div className="w-9 h-9 rounded-lg bg-white text-brand-800 flex items-center justify-center text-xl font-black shadow-inner">
                J
              </div>
              <div>
                <div className="font-extrabold tracking-wide text-lg leading-tight flex items-center gap-2">
                  <span>JAL-RAKSHA AI</span>
                  <span className="text-[10px] bg-sky-500/30 text-sky-200 border border-sky-400/40 font-bold px-2 py-0.5 rounded">
                    SIH26240
                  </span>
                </div>
                <div className="text-[11px] text-brand-100">
                  Decision Support for Spring Revival &amp; Groundwater Recharge in Tribal Belts
                </div>
              </div>
            </NavLink>

            <label className="text-xs flex items-center gap-2 bg-brand-800/80 px-2.5 py-1.5 rounded-md border border-brand-700">
              <span className="text-brand-100 font-semibold">Study Belt:</span>
              <select
                value={area}
                onChange={(e) => setArea(e.target.value)}
                className="text-slate-800 text-xs rounded px-2 py-1 bg-white font-medium focus:ring-2 focus:ring-sky-400 focus:outline-none"
              >
                <option value="all">Pan-India (All 7 Belts · 126 Springs)</option>
                {areas.map((a) => (
                  <option key={a.id} value={a.id} disabled={a.active === false}>
                    {a.name} ({a.state})
                  </option>
                ))}
              </select>
            </label>
          </div>

          <nav className="bg-brand-800 px-4 flex gap-1 overflow-x-auto border-t border-brand-700/60 scrollbar-none">
            {NAV.map(([to, label]) => (
              <motion.div key={to} whileHover={{ y: -1 }} whileTap={{ y: 0 }}>
                <NavLink
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `text-[13px] font-semibold px-3 py-2 whitespace-nowrap transition-colors block ${
                      isActive
                        ? 'bg-white text-brand-900 rounded-t shadow-sm'
                        : 'text-brand-100 hover:text-white hover:bg-brand-700/50 rounded-t'
                    }`
                  }
                >
                  {label}
                </NavLink>
              </motion.div>
            ))}
          </nav>
        </motion.header>

        <div className="bg-emerald-50 border-b border-emerald-200 px-4 py-1.5 text-center text-xs flex items-center justify-center gap-1.5">
          <span className="font-bold text-emerald-900">✓ REAL DATA FOUNDATION:</span>
          <span className="text-emerald-800">
            Live on CGWB groundwater (416K records, 6,440 stations, 1994–2017) + IMD district normals (641 districts) + Soil (673 districts) — Field validation still required before deployment.
          </span>
        </div>

        <motion.main
          key={loc.pathname}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          className="p-4 flex-1 w-full max-w-[1400px] mx-auto"
        >
          <Outlet context={{ area, setArea, areas }} />
        </motion.main>

        <footer className="px-4 py-3 text-[11px] text-slate-500 border-t border-slate-200 bg-white">
          <div className="max-w-[1400px] mx-auto flex flex-wrap justify-between items-center gap-2">
            <div>
              JAL-RAKSHA AI · Smart India Hackathon 2024 (SIH26240) · Prototype Decision-Support Platform
            </div>
            <div className="flex gap-4">
              <span>Real Datasets: CGWB (416K rows) &amp; IMD (641 dist)</span>
              <span>Map data © OpenStreetMap contributors</span>
            </div>
          </div>
        </footer>
      </div>
    </StudyAreaContext.Provider>
  );
}
