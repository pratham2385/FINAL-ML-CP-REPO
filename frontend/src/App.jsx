import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './components/common/Toast';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { EmailAnalysis } from './pages/EmailAnalysis';
import { URLAnalysis } from './pages/URLAnalysis';
import { FileAnalysis } from './pages/FileAnalysis';
import { AnalysisHistory } from './pages/AnalysisHistory';
import { Settings } from './pages/Settings';

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="email" element={<EmailAnalysis />} />
            <Route path="url" element={<URLAnalysis />} />
            <Route path="upload-eml" element={<FileAnalysis />} />
            <Route path="history" element={<AnalysisHistory />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}
