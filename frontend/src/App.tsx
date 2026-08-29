import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Incidents } from './pages/Incidents';
import { IncidentDetail } from './pages/IncidentDetail';
import { ReviewQueue } from './pages/ReviewQueue';
import { Policies } from './pages/Policies';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/incidents/:id" element={<IncidentDetail />} />
          <Route path="/review" element={<ReviewQueue />} />
          <Route path="/policies" element={<Policies />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
