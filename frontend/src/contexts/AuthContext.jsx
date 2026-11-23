
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../config/api';

const AuthContext = createContext(null);

function readIsAdmin() {
    const token = localStorage.getItem('market_access');
    if (!token) return false;

    try {
        const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
        const bytes = Uint8Array.from(atob(payload), char => char.charCodeAt(0));
        const json = new TextDecoder().decode(bytes);
        return Boolean(JSON.parse(json).is_admin);
    } catch {
        return false;
    }
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isAdmin, setIsAdmin] = useState(readIsAdmin);

    const refreshUser = useCallback(async () => {
        if (!localStorage.getItem('market_access')) {
            setUser(null);
            setIsAdmin(false);
            setLoading(false);
            return;
        }
        try {
            const { data } = await api.get('/auth/users/me');
            setUser(data);
            setIsAdmin(readIsAdmin());
        } catch {
            setUser(null);
            setIsAdmin(false);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refreshUser();
    }, [refreshUser]);

    useEffect(() => {
        const onExpired = () => {
            setUser(null);
            setIsAdmin(false);
        };
        window.addEventListener('market:session-expired', onExpired);
        return () => window.removeEventListener('market:session-expired', onExpired);
    }, []);

    const login = useCallback(async (username, password) => {
        const { data } = await api.post('/auth/token', { username, password });
        localStorage.setItem('market_access', data.access);
        localStorage.setItem('market_refresh', data.refresh);
        setIsAdmin(readIsAdmin());
        await refreshUser();
    }, [refreshUser]);

    const register = useCallback(async values => {
        await api.post('/auth/users/', values);
        await login(values.username, values.password);
    }, [login]);

    const logout = useCallback(() => {
        localStorage.removeItem('market_access');
        localStorage.removeItem('market_refresh');
        setUser(null);
        setIsAdmin(false);
    }, []);

    const value = useMemo(
        () => ({ user, loading, isAdmin, login, register, logout, refreshUser, setUser }),
        [user, loading, isAdmin, login, register, logout, refreshUser]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
