import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../config/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const refreshUser = useCallback(async () => {
        if (!localStorage.getItem('market_access')) {
            setUser(null);
            setLoading(false);
            return;
        }
        try {
            const { data } = await api.get('/auth/users/me');
            setUser(data);
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refreshUser();
    }, [refreshUser]);

    const login = async (username, password) => {
        const { data } = await api.post('/auth/token', { username, password });
        localStorage.setItem('market_access', data.access);
        localStorage.setItem('market_refresh', data.refresh);
        await refreshUser();
    };

    const register = async (values) => {
        await api.post('/auth/users/', values);
        await login(values.username, values.password);
    };

    const logout = () => {
        localStorage.removeItem('market_access');
        localStorage.removeItem('market_refresh');
        setUser(null);
    };

    const value = useMemo(
        () => ({ user, loading, login, register, logout, refreshUser, setUser }),
        [user, loading, refreshUser]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);