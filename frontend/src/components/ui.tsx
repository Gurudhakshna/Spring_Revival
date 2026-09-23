import React from 'react';

export function Badge({ children, tone = 'demo' }: { children: React.ReactNode; tone?: 'demo' | 'ok' | 'warn' | 'info' }) {
  const tones: Record<string, string> = {
    demo: 'bg-amber-100 text-amber-900 border-amber-300',
    ok: 'bg-emerald-100 text-emerald-900 border-emerald-300',
    warn: 'bg-red-100 text-red-900 border-red-300',
    info: 'bg-sky-100 text-sky-900 border-sky-300',
  };
  return (
    <span className={`inline-block text-[11px] font-semibold border rounded px-2 py-0.5 ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function DemoBadge() {
  return <Badge>DEMO DATA — Replace with validated government/field data</Badge>;
}

export function Card({ title, sub, right, children, className = '' }: {
  title?: string; sub?: string; right?: React.ReactNode; children: React.ReactNode; className?: string;
}) {
  return (
    <section className={`bg-white border border-slate-200 rounded-lg ${className}`}>
      {(title || right) && (
        <header className="flex items-start justify-between gap-3 px-4 pt-3 pb-2 border-b border-slate-100">
          <div>
            {title && <h3 className="text-sm font-bold text-slate-800">{title}</h3>}
            {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
          </div>
          {right}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-2xl font-bold text-brand-800 mt-1">{value}</div>
      {hint && <div className="text-xs text-slate-500 mt-0.5">{hint}</div>}
    </div>
  );
}

export function Err({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-lg p-4">
      <div className="font-semibold">Something went wrong</div>
      <div className="mt-1">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="mt-2 text-xs font-semibold underline">Retry</button>
      )}
    </div>
  );
}

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="py-6 space-y-3 animate-pulse">
      <div className="h-4 bg-slate-200 rounded w-1/3 mx-auto"></div>
      <div className="h-3 bg-slate-100 rounded w-1/2 mx-auto"></div>
      <div className="text-xs text-slate-400 text-center">{label}</div>
    </div>
  );
}
export function Skeleton({ rows=3 }: {rows?:number}){
  return <div className="space-y-2 animate-pulse">{Array.from({length:rows}).map((_,i)=>(<div key={i} className="h-4 bg-slate-200 rounded"></div>))}</div>;
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold text-slate-600">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

export const inputCls =
  'w-full text-sm border border-slate-300 rounded px-2 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-brand-600';
export const btnPrimary =
  'text-sm font-semibold bg-brand-700 text-white rounded px-4 py-2 hover:bg-brand-800 disabled:opacity-50';
export const btnGhost =
  'text-sm font-semibold border border-slate-300 rounded px-3 py-1.5 hover:bg-slate-50';
