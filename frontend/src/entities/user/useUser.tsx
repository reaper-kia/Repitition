import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { api } from '../../shared/api';
import type { MeResponse } from '../../shared/api/types';

interface UserState {
  user: MeResponse | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

const UserContext = createContext<UserState | null>(null);

export function useUser(): UserState {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error('useUser must be used inside UserProvider');
  return ctx;
}

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const me = await api.getMe();
      setUser(me);
      setError(null);
    } catch (e) {
      setUser(null);
      const status = (e as { status?: number }).status;
      setError(status === 401 || status === 403 ? null : 'Не удалось проверить сессию');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return (
    <UserContext.Provider value={{ user, loading, error, reload }}>
      {children}
    </UserContext.Provider>
  );
}
