import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Badge, btnPrimary, btnGhost } from '../components/ui';

export default function LandingPage() {
  const navigate = useNavigate();

  const stats = [
    { label: 'Tribal Belts Covered', value: '7 Zones', hint: 'Pan-India Representation' },
    { label: 'Springs Profiled', value: '126 Springs', hint: 'Catchment & Discharge Mapped' },
    { label: 'Villages & Wells', value: '84 Vill. / 105 Wells', hint: 'Demographic Water Linkage' },
    { label: 'CGWB Groundwater Records', value: '416,000+', hint: '1994–2025 Station Data' },
    { label: 'IMD Climate Normals', value: '641 Districts', hint: 'Real Rainfall & Soil Profiles' },
  ];

  const features = [
    {
      title: 'Hydrogeological AI Scoring',
      desc: 'Dual-engine validation: deterministic 8-factor weighted hydrology cross-verified by a 200-tree RandomForest ML pipeline with explainable feature attribution.',
      badge: 'Dual Engine',
      link: '/ai',
    },
    {
      title: 'Springshed GIS & Recharge Map',
      desc: 'Interactive Leaflet GIS visualizing spring coordinates, estimated recharge zones, groundwater depth layers, and regional tribal belt overlays.',
      badge: 'GIS Layer',
      link: '/map',
    },
    {
      title: 'Intervention Impact Simulator',
      desc: 'Model 8 field interventions (contour trenches, percolation ponds, check dams) with dynamic cost estimation (INR) and predicted score lift.',
      badge: 'Scenario Modeling',
      link: '/planner',
    },
    {
      title: 'CGWB Early Warning Alerts',
      desc: 'Monitors 416K+ real CGWB telemetry points to predict aquifer depletion and spring drying with multi-month lead times.',
      badge: 'Real CGWB Data',
      link: '/early-warning',
    },
    {
      title: 'Water-Aware Crop Advisor',
      desc: 'Recommends drought-resilient crops and water conservation practices aligned with seasonal recharge and soil micronutrient status.',
      badge: 'Farmer First',
      link: '/crop',
    },
    {
      title: 'Field Reporting & Mobile Sync',
      desc: 'Lightweight interface for ground hydrologists and community volunteers to log real discharge, water quality, and GPS coordinates.',
      badge: 'Field Sync',
      link: '/field',
    },
  ];

  return (
    <div className="space-y-8 py-2">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-900 via-brand-800 to-slate-900 text-white p-8 md:p-12 shadow-xl border border-brand-700/50">
        <div className="relative z-10 max-w-3xl space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="bg-sky-500/20 text-sky-200 border border-sky-400/30 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
              Smart India Hackathon 2024 · SIH26240
            </span>
            <span className="bg-emerald-500/20 text-emerald-200 border border-emerald-400/30 text-xs font-bold px-3 py-1 rounded-full">
              Decision Support Platform
            </span>
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
            Reviving Mountain &amp; Plateau Springs with <span className="text-sky-300">Predictive AI</span>
          </h1>

          <p className="text-base md:text-lg text-slate-200 leading-relaxed">
            Over 50 million indigenous citizens depend on natural springs for drinking water and subsistence agriculture. 
            <strong> JAL-RAKSHA AI</strong> couples physical hydrogeology with machine learning, 416K real CGWB groundwater records, 
            and IMD climate normals to identify drying springs and simulate targeted revival interventions.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all text-sm flex items-center gap-2"
            >
              <span>Explore Dashboard</span>
              <span>→</span>
            </button>
            <button
              onClick={() => navigate('/map')}
              className="bg-white/10 hover:bg-white/20 text-white border border-white/20 font-bold px-5 py-3 rounded-lg transition-all text-sm"
            >
              Interactive GIS Map
            </button>
            <button
              onClick={() => navigate('/early-warning')}
              className="bg-white/10 hover:bg-white/20 text-white border border-white/20 font-bold px-5 py-3 rounded-lg transition-all text-sm"
            >
              Early Warning System
            </button>
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute -right-20 -bottom-20 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {stats.map((s) => (
          <div key={s.label} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm text-center md:text-left">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{s.label}</div>
            <div className="text-xl md:text-2xl font-extrabold text-brand-800 mt-1">{s.value}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">{s.hint}</div>
          </div>
        ))}
      </div>

      {/* Core Capabilities */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-800">Integrated Decision Support Modules</h2>
            <p className="text-xs text-slate-500 mt-0.5">End-to-end hydrogeological assessment from catchment analytics to field action</p>
          </div>
          <Link to="/about" className="text-xs font-semibold text-brand-700 hover:text-brand-900 underline">
            Architecture &amp; Methodology →
          </Link>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f) => (
            <div
              key={f.title}
              onClick={() => navigate(f.link)}
              className="group bg-white border border-slate-200 hover:border-brand-500 rounded-xl p-5 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-brand-700 bg-brand-50 border border-brand-200 px-2 py-0.5 rounded">
                    {f.badge}
                  </span>
                  <span className="text-slate-400 group-hover:text-brand-600 transition-colors">↗</span>
                </div>
                <h3 className="font-bold text-slate-800 group-hover:text-brand-800 text-base mb-1.5 transition-colors">
                  {f.title}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">{f.desc}</p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center text-xs font-semibold text-brand-700 group-hover:translate-x-1 transition-transform">
                <span>Open module</span>
                <span className="ml-1">→</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Scientific Validation Note */}
      <div className="bg-sky-50 border border-sky-200 rounded-xl p-5 space-y-2">
        <div className="flex items-center gap-2">
          <Badge tone="info">Scientific Transparency &amp; Deployment Roadmap</Badge>
          <span className="text-xs font-bold text-sky-950">Prototype Decision-Support Notice</span>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          The current prototype utilizes <strong>416,952 real CGWB telemetry observations</strong> for early warning trend detection and 
          <strong> real IMD district climate records</strong> (641 districts). For pan-India demonstration across 7 tribal zones, 
          spring and well coordinates are calibrated against representative regional geology and elevation gradients. 
          All AI predictions serve as advisory decision-support estimates to prioritize field surveys and hydrogeological ground-truthing.
        </p>
      </div>
    </div>
  );
}
