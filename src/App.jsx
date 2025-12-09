import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider } from './utils/ThemeProvider';
import Layout from './components/layout/Layout';
import Overview from './pages/Overview';
import Dashboards from './pages/Dashboards';
import CreateService from './pages/CreateService';
import Services from './pages/Services';
import ServiceDetail from './pages/ServiceDetail';
import EditService from './pages/EditService';
import UsersGroups from './pages/UsersGroups';
import Plugins from './pages/Plugins';
import Documentation from './pages/Documentation';
import Settings from './pages/Settings';
import Login from './pages/Login';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Overview />} />
            <Route path="dashboards" element={<Dashboards />} />
            <Route path="create" element={<CreateService />} />
            <Route path="services" element={<Services />} />
            <Route path="services/:serviceId" element={<ServiceDetail />} />
            <Route path="services/:serviceId/edit" element={<EditService />} />
            <Route path="users" element={<UsersGroups />} />
            <Route path="plugins" element={<Plugins />} />
            <Route path="docs" element={<Documentation />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
