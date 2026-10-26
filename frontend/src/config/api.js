import axios from 'axios';

export const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use(config => {
    const token = localStorage.getItem('market_access');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    r => r,
    async error => {
        const original = error.config;
        if (error.response?.status === 401 && !original?._retry && 
            localStorage.getItem('market_refresh') && !original.url?.includes('/auth/token')) {
            original._retry = true;
            try {
                const { data } = await axios.post(
                    `${api.defaults.baseURL}/auth/token/refresh`,
                    { refresh_token: localStorage.getItem('market_refresh') }
                );
                const access = data.access || data.access_token;
                const refresh = data.refresh || data.refresh_token;
                if (access) localStorage.setItem('market_access', access);
                if (refresh) localStorage.setItem('market_refresh', refresh);
                original.headers.Authorization = `Bearer ${access}`;
                return api(original);
            } catch {
                localStorage.removeItem('market_access');
                localStorage.removeItem('market_refresh');
            }
        }
        return Promise.reject(error);
    }
);

export function errorMessage(error) {
    return error?.response?.data?.detail || error?.response?.data?.message || 
           error.message || 'Что-то пошло не так';
}