import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import App from './App';
import Dashboard from './pages/Dashboard';
import RechargeMapPage from './pages/RechargeMapPage';
import SpringsPage from './pages/SpringsPage';
import PlannerPage from './pages/PlannerPage';
import EarlyWarningPage from './pages/EarlyWarningPage';
import ReportsPage from './pages/ReportsPage';
import AIAnalysisPage from './pages/AIAnalysisPage';
import DataPage from './pages/DataPage';
import FieldPage from './pages/FieldPage';
import AboutPage from './pages/AboutPage';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<App />}>
          <Route index element={<Dashboard />} />
          <Route path="map" element={<RechargeMapPage />} />
          <Route path="springs" element={<SpringsPage />} />
          <Route path="early-warning" element={<EarlyWarningPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="planner" element={<PlannerPage />} />
          <Route path="ai" element={<AIAnalysisPage />} />
          <Route path="field" element={<FieldPage />} />
          <Route path="data" element={<DataPage />} />
          <Route path="about" element={<AboutPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
