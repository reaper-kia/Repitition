import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useUser } from '../../entities/user/useUser';
import type { Role } from '../../shared/api/types';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

interface ProtectedRouteProps {
  children: ReactNode;
  allow?: Role[];
}

export function ProtectedRoute({ children, allow }: ProtectedRouteProps) {
  const { user, loading, error, reload } = useUser();
  const location = useLocation();

  if (loading) return <div className="route-state"><Loading /></div>;
  if (error) return <div className="route-state"><ErrorMessage message={error} onRetry={() => void reload()} /></div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (allow && !allow.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}
