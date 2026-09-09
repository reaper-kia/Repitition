import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from '../features/auth/ProtectedRoute';
import { AdminPage } from '../pages/admin/AdminPage';
import { CabinetPage } from '../pages/cabinet/CabinetPage';
import { HomePage } from '../pages/home/HomePage';
import { LoginPage } from '../pages/login/LoginPage';
import { ManagerPage } from '../pages/manager/ManagerPage';
import { NotFoundPage } from '../pages/not-found/NotFoundPage';
import { PublicLayout } from '../widgets/layout/PublicLayout';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/cabinet"
            element={<ProtectedRoute allow={['CLIENT']}><CabinetPage /></ProtectedRoute>}
          />
          <Route
            path="/manager"
            element={<ProtectedRoute allow={['CLUB_MANAGER']}><ManagerPage /></ProtectedRoute>}
          />
          <Route
            path="/manager/cases"
            element={<ProtectedRoute allow={['CLUB_MANAGER']}><ManagerPage /></ProtectedRoute>}
          />
          <Route
            path="/admin"
            element={<ProtectedRoute allow={['NETWORK_ADMIN']}><AdminPage /></ProtectedRoute>}
          />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}
