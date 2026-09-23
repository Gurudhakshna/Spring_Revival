import { Card } from '../components/ui';

export default function AboutPage() {
  return (
    <div className="space-y-4 max-w-4xl">
      <Card title="JAL-RAKSHA AI" sub="SIH26240 — AI-Based Spring Revival and Recharge Planning for Tribal Areas">
        <div className="text-sm space-y-2 text-slate-700">
          <p>Decision-support platform that answers four questions: <b>where are the springs?</b> what areas likely feed them? <b>where is recharge more suitable?</b> and <b>what intervention fits there, with what estimated impact?</b></p>
          <p>It combines elevation, slope, rainfall, land use, geology, distance to streams, lineament density and groundwater depth into a transparent prototype recharge score, plus a Random Forest model trained on the bundled dataset.</p>
          <p className="font-semibold text-amber-800">All predictions are labelled “Prototype Decision-Support Estimate”. The system never claims a model guarantees groundwater recharge. Current data is synthetic and illustrative — replace with validated government/field data before operational use.</p>
        </div>
      </Card>
      <Card title="How the recharge score is calculated">
        <table className="text-sm w-full">
          <thead><tr className="text-left text-xs text-slate-500 border-b"><th>Factor</th><th>Weight</th><th>Normalisation (prototype)</th></tr></thead>
          <tbody className="text-slate-700">
            {[['Rainfall', '20%', '(rain − 700) / 900, clipped 0–1'], ['Slope', '15%', '1 − (slope − 2) / 33'], ['Soil moisture', '15%', 'index 0–1 directly'], ['Land use', '10%', 'forest .9 … barren .2'], ['Geology', '15%', 'fractured rock .9 … clay .25'], ['Distance to stream', '10%', 'exp(−dist / 600)'], ['Lineament density', '10%', 'index 0–1 directly'], ['Groundwater depth', '5%', '1 − (depth − 3) / 47']].map(([a, b, c]) => (
              <tr key={a} className="border-b border-slate-100"><td className="py-1 font-semibold">{a}</td><td>{b}</td><td className="text-xs">{c}</td></tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs text-slate-500 mt-2">Weights are configurable per request (POST /api/recharge/calculate accepts a weights override) and renormalised to 100. Classes: HIGH ≥ 70, MEDIUM 45–70, LOW &lt; 45.</p>
      </Card>
      <Card title="How the AI works">
        <div className="text-sm text-slate-700 space-y-1">
          <p>RandomForestRegressor (200 trees) on 9 features, one-hot encoded categoricals. Metrics (R² / MAE / RMSE) are computed live from validation_data.csv on the AI Analysis page — never hardcoded.</p>
          <p>Priority = 0.40·recharge + 0.20·vulnerability + 0.15·population + 0.15·feasibility + 0.10·water stress. Risk flags are a fixed transparent rule set (8 checks).</p>
        </div>
      </Card>
      <Card title="Replacing demo data with real data">
        <ol className="text-sm text-slate-700 list-decimal ml-5 space-y-1">
          <li>Collect validated springs, wells, villages, rainfall and recharge observations (CGWB / state groundwater / IMD / field surveys).</li>
          <li>Match the column contracts in data/ (see README § Dataset + data contracts).</li>
          <li>Drop files into backend/data/ (or point DATA_DIR at them) and retrain: the model rebuilds automatically on next startup.</li>
          <li>For live feeds, implement a subclass of FutureGovernmentDataProvider (backend/services/data_provider.py) — no frontend changes needed.</li>
        </ol>
      </Card>
      <Card title="Limitations & field validation">
        <ul className="text-sm text-slate-700 list-disc ml-5 space-y-1">
          <li>Synthetic demo data — magnitudes are illustrative, not measurements.</li>
          <li>Springsheds are visual estimates, not officially delineated.</li>
          <li>Intervention impacts are scenario estimates, not measured outcomes.</li>
          <li>Requires hydrogeologist field checks: spring discharge monitoring, geophysical confirmation, community consent, and post-monsoon review before any construction.</li>
        </ul>
      </Card>
    </div>
  );
}
